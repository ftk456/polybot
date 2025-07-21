import discord
from discord.ext import commands
from discord import app_commands
import json
import os

WARN_FILE = "data/warn.json"

def load_warns():
    if not os.path.exists(WARN_FILE):
        with open(WARN_FILE, "w") as f:
            json.dump({}, f)
    with open(WARN_FILE, "r") as f:
        return json.load(f)

class HSWarn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        @app_commands.command(
            name="hswarn",
            description="Affiche tous les warns d'un utilisateur."
        )
        @app_commands.describe(
            membre="Le membre dont afficher les avertissements"
        )
        async def hswarn(interaction: discord.Interaction, membre: discord.Member):
            warns = load_warns()
            user_id = str(membre.id)

            user_warns = warns.get(user_id, [])

            if not user_warns:
                await interaction.response.send_message(
                    f" {membre.mention} n'a **aucun avertissement**.",
                    ephemeral=True
                )
                return

            # Crée la liste formatée
            warn_list = "\n".join([f"{idx+1}. {reason}" for idx, reason in enumerate(user_warns)])

            embed = discord.Embed(
                title=f" Avertissements pour {membre.display_name} 📋",
                description=warn_list,
                color=discord.Color.orange()
            )

            await interaction.response.send_message(embed=embed)

        # ✅ Ajout de la commande
        self.bot.tree.add_command(hswarn)

async def setup(bot):
    await bot.add_cog(HSWarn(bot))
