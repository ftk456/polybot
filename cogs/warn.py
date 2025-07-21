import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# Chemin du fichier pour stocker les warns
WARN_FILE = "data/warn.json"

# Fonctions pour le json
def load_warns():
    if not os.path.exists(WARN_FILE):
        with open(WARN_FILE, "w") as f:
            json.dump({}, f)
    with open(WARN_FILE, "r") as f:
        return json.load(f)

def save_warns(data):
    with open(WARN_FILE, "w") as f:
        json.dump(data, f, indent=4)

class Warn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        @app_commands.command(
            name="warn",
            description="Ajoute un avertissement à un membre."
        )
        @app_commands.describe(
            membre="Le membre à warn",
            raison="La raison du warn"
        )
        async def warn(interaction: discord.Interaction, membre: discord.Member, raison: str):
            #  Vérifie permissions des membres
            if not interaction.user.guild_permissions.manage_messages:
                await interaction.response.send_message(
                    " Vous n'avez pas la permission de gérer les messages (requis pour warn).",
                    ephemeral=True
                )
                return

            #  Vérifie permissions bot
            if not interaction.guild.me.guild_permissions.manage_messages:
                await interaction.response.send_message(
                    " Je n'ai pas la permission de gérer les messages sur ce serveur.",
                    ephemeral=True
                )
                return

            #  Charge les données du fichier
            warns = load_warns()
            user_id = str(membre.id)

            if user_id not in warns:
                warns[user_id] = []
            warns[user_id].append(raison)
            save_warns(warns)

            await interaction.response.send_message(
                f" {membre.mention} a reçu un avertissement ✅.\n**Raison :** {raison}"
            )

        #  Ajoute la commande au /
        self.bot.tree.add_command(warn)

async def setup(bot):
    await bot.add_cog(Warn(bot))
