import discord
from discord.ext import commands
from discord import app_commands
import json
import os

BANK_FILE = "data/members_banks.json"
SHOP_FILE = "data/shop_config.json"
LOGS_CHANNEL_NAME = "bot_mg"  # À adapter selon le nom de ton salon

def load_data(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r") as f:
        return json.load(f)

def save_data(data, file):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

#  Vérification perm admin
async def is_admin_check(interaction: discord.Interaction) -> bool:
    return interaction.user.guild_permissions.administrator

class Magasin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        #  Commande pour ouvrir la boutique
        @app_commands.command(name="magasin", description="Ouvre la boutique du serveur")
        async def magasin(interaction: discord.Interaction):
            shop_config = load_data(SHOP_FILE)
            if not shop_config:
                await interaction.response.send_message("🛒 Aucun article en vente actuellement.", ephemeral=True)
                return

            embed = discord.Embed(title="🛒 Boutique du serveur", description="Choisissez un article :", color=discord.Color.gold())
            view = MagasinView(shop_config)

            for key, item in shop_config.items():
                embed.add_field(name=item['titre'], value=f"Prix : {item['prix']} 💰", inline=False)

            await interaction.response.send_message(embed=embed, view=view)

        #  Ajouter ou modifier un article
        @app_commands.command(name="configmagasin", description="Configure un article dans le magasin")
        @app_commands.check(is_admin_check)
        async def configmagasin(interaction: discord.Interaction, cle: str, titre: str, prix: int, role: discord.Role):
            shop_config = load_data(SHOP_FILE)
            shop_config[cle] = {
                "titre": titre,
                "prix": prix,
                "role_id": role.id
            }
            save_data(shop_config, SHOP_FILE)
            await interaction.response.send_message(f" Article `{titre}` ajouté/modifié avec succès ✅.")

        # 🗑️ Supprimer un article
        @app_commands.command(name="configmagasindelete", description="Supprime un article du magasin")
        @app_commands.check(is_admin_check)
        async def configmagasindelete(interaction: discord.Interaction, cle: str):
            shop_config = load_data(SHOP_FILE)
            if cle not in shop_config:
                await interaction.response.send_message(f" Aucun article avec la clé `{cle}` trouvé ❌.", ephemeral=True)
                return

            del shop_config[cle]
            save_data(shop_config, SHOP_FILE)
            await interaction.response.send_message(f"🗑️ Article `{cle}` supprimé du magasin.")

        # Gestion des erreurs de permission
        @configmagasin.error
        @configmagasindelete.error
        async def admin_check_failed(interaction: discord.Interaction, error):
            if isinstance(error, app_commands.errors.CheckFailure):
                await interaction.response.send_message("Tu dois être administrateur pour utiliser cette commande.", ephemeral=True)

        self.bot.tree.add_command(magasin)
        self.bot.tree.add_command(configmagasin)
        self.bot.tree.add_command(configmagasindelete)

# boutons magasins
class MagasinView(discord.ui.View):
    def __init__(self, shop_config):
        super().__init__(timeout=None)
        for key in shop_config:
            self.add_item(AcheterButton(label=shop_config[key]["titre"], custom_id=f"acheter_{key}", key=key))

#  Bouton d’achat
class AcheterButton(discord.ui.Button):
    def __init__(self, label, custom_id, key):
        super().__init__(label=label, style=discord.ButtonStyle.green, custom_id=custom_id)
        self.key = key

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        bank = load_data(BANK_FILE)
        shop = load_data(SHOP_FILE)
        item = shop.get(self.key)

        if not item:
            await interaction.response.send_message("Cet objet n'existe plus.", ephemeral=True)
            return

        prix = item["prix"]
        role_id = item["role_id"]
        user_data = bank.get(user_id, {"balance": 0})

        if user_data.get("balance", 0) < prix:
            await interaction.response.send_message(f" Tu n’as pas assez d’argent (Prix : {prix} 💰).", ephemeral=True)
            return

        member = interaction.user
        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.response.send_message(" Le rôle configuré n’existe pas.", ephemeral=True)
            return

        if role in member.roles:
            await interaction.response.send_message(" Tu possèdes déjà ce rôle.", ephemeral=True)
            return

        # Débit de l'argent dans le fichier
        user_data["balance"] -= prix
        bank[user_id] = user_data
        save_data(bank, BANK_FILE)

        try:
            await member.add_roles(role, reason="Achat via /magasin")
            await interaction.response.send_message(f" Tu as acheté : **{item['titre']}** pour {prix} 💰 ✅.", ephemeral=True)

            # Logs dans le salon
            logs_channel = discord.utils.get(interaction.guild.text_channels, name=LOGS_CHANNEL_NAME)
            if logs_channel:
                await logs_channel.send(f"📥 {member.mention} a acheté **{item['titre']}** ({prix} 💰).")

        except discord.Forbidden:
            await interaction.response.send_message(" Je n’ai pas la permission d’attribuer ce rôle.", ephemeral=True)

#  Chargement dans bot
async def setup(bot):
    await bot.add_cog(Magasin(bot))
