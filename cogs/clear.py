import discord
from discord.ext import commands
from discord import app_commands

class Clear(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clear", description="Supprime un nombre de messages dans le salon.")
    @app_commands.describe(nombre="Nombre de messages à supprimer (1-100)")
    async def clear(self, interaction: discord.Interaction, nombre: int):
        if not interaction.channel.permissions_for(interaction.user).manage_messages:
            await interaction.response.send_message("❌ Tu n'as pas la permission de gérer les messages.", ephemeral=True)
            return

        if nombre < 1 or nombre > 100:
            await interaction.response.send_message("❌ Choisis un nombre entre 1 et 100.", ephemeral=True)
            return

        try:
            deleted = await interaction.channel.purge(limit=nombre)
            await interaction.response.send_message(f"✅ {len(deleted)} messages supprimés.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Je n'ai pas la permission de supprimer des messages.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur : {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Clear(bot))
