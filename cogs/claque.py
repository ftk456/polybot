import discord
from discord.ext import commands
from discord import app_commands
import random

class Claque(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        @app_commands.command(name="claque", description="Donne une claque à quelqu’un (virtuellement 😡)")
        @app_commands.describe(cible="Mentionne la personne à frapper")
        async def claque(interaction: discord.Interaction, cible: discord.Member):
            auteur = interaction.user

            if cible.id == auteur.id:
                await interaction.response.send_message(" Tu ne peux pas te frapper toi-même, respire mdrr ! 😅", ephemeral=True)
                return

            phrases = [
                f" **{auteur.mention}** a mis une bastos à **{cible.mention}** 💥 !",
                f" **{auteur.mention}** a giflé **{cible.mention}** 👋",
                f" **{auteur.mention}** a balancé un coup de poing à **{cible.mention}** 🥊!",
                f" **{auteur.mention}** a électrocuté **{cible.mention}** ⚡⚡.",
                f" **{cible.mention}** s’est pris une bonne patate de l'espace de **{auteur.mention}** 😤."
            ]

            message = random.choice(phrases)
            await interaction.response.send_message(message)

        self.bot.tree.add_command(claque)

async def setup(bot):
    await bot.add_cog(Claque(bot))
