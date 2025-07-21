import discord
from discord.ext import commands
from discord import app_commands
import json
import time
import os

DATA_FILE = "data/members_banks.json"
CLAIM_COOLDOWN_SECONDS = 24 * 60 * 60
CLAIM_BONUS = 100

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

class Economie(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        # code pou le /
        economie_group = app_commands.Group(
            name="economie",
            description="Commandes pour l'économie 💰"
        )

        # ✅ /economie balance [membre]
        @economie_group.command(
            name="balance",
            description="Affiche votre solde ou celui d'un autre membre 💰"
        )
        @app_commands.describe(membre="Le membre dont vous voulez voir le solde")
        async def balance(interaction: discord.Interaction, membre: discord.User = None):
            data = load_data()
            target = membre or interaction.user
            user_id = str(target.id)
            solde = data.get(user_id, {}).get("balance", 0)

            if membre:
                await interaction.response.send_message(
                    f"💰 Solde de {target.mention} : {solde}€."
                )
            else:
                await interaction.response.send_message(
                    f"{target.mention}, votre solde est de {solde}€."
                )

        # ✅ /economie claim qui permet de recup la thune
        @economie_group.command(
            name="claim",
            description="Réclamez votre bonus quotidien 💸"
        )
        async def claim(interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            data = load_data()
            user_data = data.get(user_id, {"balance": 0, "last_claim": 0})

            now = int(time.time())
            elapsed = now - user_data.get("last_claim", 0)

            if elapsed < CLAIM_COOLDOWN_SECONDS:
                remaining = CLAIM_COOLDOWN_SECONDS - elapsed
                hours = remaining // 3600
                minutes = (remaining % 3600) // 60
                await interaction.response.send_message(
                    f"{interaction.user.mention}, vous devez attendre {hours}h {minutes}m avant de réclamer à nouveau votre daily."
                )
                return

            user_data["balance"] += CLAIM_BONUS
            user_data["last_claim"] = now
            data[user_id] = user_data
            save_data(data)

            await interaction.response.send_message(
                f"{interaction.user.mention}, vous avez reçu {CLAIM_BONUS}€ ! Nouveau solde : {user_data['balance']}€."
            )

        # ✅ /economie leaderboard
        @economie_group.command(
            name="leaderboard",
            description="Montre le top 10 des joueurs les plus riches 🏆"
        )
        async def leaderboard(interaction: discord.Interaction):
            data = load_data()

            # Trier les utilisateurs par balance
            top = sorted(
                data.items(),
                key=lambda x: x[1].get("balance", 0),
                reverse=True
            )[:10]

            if not top:
                await interaction.response.send_message("Aucun joueur enregistré pour le leaderboard.")
                return

            embed = discord.Embed(
                title="🏆 Leaderboard des plus riches",
                color=discord.Color.gold()
            )
            for rank, (user_id, info) in enumerate(top, start=1):
                member = interaction.guild.get_member(int(user_id))
                name = member.mention if member else f"<@{user_id}>"
                balance = info.get("balance", 0)
                embed.add_field(name=f"#{rank} {name}", value=f"{balance}€", inline=False)

            await interaction.response.send_message(embed=embed)

        # evite les doublons
        if not any(cmd.name == economie_group.name for cmd in self.bot.tree.get_commands()):
            self.bot.tree.add_command(economie_group)

async def setup(bot):
    await bot.add_cog(Economie(bot))
