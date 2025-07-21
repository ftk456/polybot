import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os

# Chemins vers les fichiers JSON
INVENTAIRES_FILE = "data/inventaires.json"
BANKS_FILE = "data/members_banks.json"
COOLDOWNS_FILE = "data/peche_cooldowns.json"

def load_data(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)
    with open(file, "r") as f:
        return json.load(f)

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def get_timestamp():
    return int(discord.utils.utcnow().timestamp())

class Peche(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Déf des poissons avec leurs chances et valeurs
        self.fish_data = [
            {"name": "Commun", "value": 5, "chance": 51},
            {"name": "Uncommon", "value": 10, "chance": 25},
            {"name": "Rare", "value": 25, "chance": 15},
            {"name": "Epic", "value": 50, "chance": 7},
            {"name": "Legendaire", "value": 100, "chance": 2}
        ]

    def get_random_fish(self):
        roll = random.uniform(0, 100)
        cumulative = 0
        for fish in self.fish_data:
            cumulative += fish["chance"]
            if roll <= cumulative:
                return fish
        return self.fish_data[0]

    async def cog_load(self):
        # ✅ Commande /peche
        @app_commands.command(name="peche", description="Pêche un poisson aléatoire (avec cooldown).")
        async def peche(interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            inventaires = load_data(INVENTAIRES_FILE)
            cooldowns = load_data(COOLDOWNS_FILE)
            now = get_timestamp()

            user_data = cooldowns.get(user_id, {
                "count": 0,
                "last_peche": 0,
                "block_until": 0
            })

            # Vérifier le cooldown de 2h30
            if user_data.get("block_until", 0) > now:
                remaining = user_data["block_until"] - now
                minutes, seconds = divmod(remaining, 60)
                hours, minutes = divmod(minutes, 60)
                return await interaction.response.send_message(
                    f"⏳ Vous êtes épuisé ! Attendez encore **{hours}h {minutes}min {seconds}s** avant de pêcher à nouveau.",
                    ephemeral=True
                )

            # Vérifier cooldown de 2 minutes pour eviter le farrm intensif
            last_time = user_data.get("last_peche", 0)
            if now - last_time < 120:
                wait = 120 - (now - last_time)
                mins, secs = divmod(wait, 60)
                return await interaction.response.send_message(
                    f" Vous devez attendre **{mins}min {secs}s** avant de pouvoir repêcher.",
                    ephemeral=True
                )

            # autorise la peche
            fish = self.get_random_fish()

            if user_id not in inventaires:
                inventaires[user_id] = []
            inventaires[user_id].append(fish["name"])
            save_data(INVENTAIRES_FILE, inventaires)

            # Mettre à jour les données cooldown dans le fichier
            user_data["last_peche"] = now
            user_data["count"] += 1

            # Vérifier si on atteint 6 pêches = bloquer 2h30
            if user_data["count"] >= 6:
                user_data["block_until"] = now + (2 * 60 * 60 + 30 * 60)  # 2h30
                user_data["count"] = 0
                await interaction.response.send_message(
                    f"🎣 Vous avez pêché un **{fish['name']}** qui vaut **{fish['value']} pièces** !\n"
                    f"Vous êtes maintenant épuisé et devez attendre **2h30**⚠️  avant de pouvoir pêcher à nouveau."
                )
            else:
                await interaction.response.send_message(
                    f"🎣 Vous avez pêché un **{fish['name']}** qui vaut **{fish['value']} pièces** !\n"
                    f"Il vous reste {6 - user_data['count']} pêches avant le cooldown obligatoire de 2h30."
                )

            cooldowns[user_id] = user_data
            save_data(COOLDOWNS_FILE, cooldowns)

        #  Commande /inventaire
        @app_commands.command(name="inventaire", description="Voir et vendre votre inventaire de poissons.")
        async def inventaire(interaction: discord.Interaction):
            user_id_str = str(interaction.user.id)
            inventaires = load_data(INVENTAIRES_FILE)
            user_inv = inventaires.get(user_id_str, [])

            if not user_inv:
                await interaction.response.send_message("Votre inventaire est vide 🎣.")
                return

            # Compter les types de poissons
            counts = {}
            for fish in user_inv:
                counts[fish] = counts.get(fish, 0) + 1

            desc = "\n".join([f"**{name}** × {count}" for name, count in counts.items()])

            # Bouton Vendre tout
            class SellButton(discord.ui.View):
                def __init__(self, parent):
                    super().__init__(timeout=60)
                    self.parent = parent

                @discord.ui.button(label="Vendre tout", style=discord.ButtonStyle.green)
                async def sell(self, interaction2: discord.Interaction, button: discord.ui.Button):
                    if interaction2.user.id != interaction.user.id:
                        await interaction2.response.send_message("Ce n'est pas votre inventaire ! ❌ ", ephemeral=True)
                        return

                    # Recharger l'inventaire apres le jeux
                    inventaires = load_data(INVENTAIRES_FILE)
                    user_inv = inventaires.get(user_id_str, [])

                    if not user_inv:
                        await interaction2.response.send_message("Votre inventaire est vide ❌.", ephemeral=True)
                        return

                    # Calcul de la valeur totale des gains de con
                    total_value = 0
                    for fish_name in user_inv:
                        fish_info = next((f for f in self.parent.fish_data if f["name"] == fish_name), None)
                        if fish_info:
                            total_value += fish_info["value"]

                    # Vider l'inventaire du joueur
                    inventaires[user_id_str] = []
                    save_data(INVENTAIRES_FILE, inventaires)

                    # Créditer les thunes dans les soldes
                    banks = load_data(BANKS_FILE)
                    if user_id_str not in banks:
                        banks[user_id_str] = {"balance": total_value}
                    else:
                        banks[user_id_str]["balance"] = banks[user_id_str].get("balance", 0) + total_value

                    save_data(BANKS_FILE, banks)

                    await interaction2.response.edit_message(
                        content=(
                            f" Vous avez vendu {len(user_inv)} poissons pour un total de **{total_value} pièces ✅** !\n"
                            f" Nouveau solde : **{banks[user_id_str]['balance']} pièces** 💰."
                        ),
                        view=None
                    )

            embed = discord.Embed(
                title=f"Inventaire de {interaction.user.display_name}",
                description=desc,
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, view=SellButton(self))

        # ✅ Ajout 
        self.bot.tree.add_command(peche)
        self.bot.tree.add_command(inventaire)

async def setup(bot):
    await bot.add_cog(Peche(bot))
