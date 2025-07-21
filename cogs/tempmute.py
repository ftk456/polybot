import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta

class TempMute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        @app_commands.command(
            name="tempmute",
            description="Mute un membre pendant X minutes (timeout)."
        )
        @app_commands.describe(
            membre="Le membre à mute",
            temps="Durée du mute en minutes",
            raison="La raison du mute"
        )
        async def tempmute(
            interaction: discord.Interaction,
            membre: discord.Member,
            temps: int,
            raison: str = "Aucune raison donnée"
        ):
            # Vérifie permissions des membres
            if not interaction.user.guild_permissions.moderate_members:
                await interaction.response.send_message(
                    " Vous n'avez pas la permission de mute des membres ❌.",
                    ephemeral=True
                )
                return

            # Vérifie perm bot
            if not interaction.guild.me.guild_permissions.moderate_members:
                await interaction.response.send_message(
                    "Je n'ai pas la permission de mute des membres sur ce serveur ❌.",
                    ephemeral=True
                )
                return

            # Vérifie la hiérarchie des roles 
            if membre.top_role >= interaction.guild.me.top_role:
                await interaction.response.send_message(
                    "Je ne peux pas mute ce membre (son rôle est plus haut ou égal au mien) ❌.",
                    ephemeral=True
                )
                return

            # Vérifie durée 
            if temps <= 0 or temps > 40320:  # 28 jours max
                await interaction.response.send_message(
                    "La durée doit être comprise entre 1 et 40320 minutes (28 jours).",
                    ephemeral=True
                )
                return

            try:
                await membre.edit(
                    timed_out_until=discord.utils.utcnow() + timedelta(minutes=temps),
                    reason=raison
                )
                await interaction.response.send_message(
                    f" {membre.mention} a été **mute** ✅ pour {temps} minutes.\n**Raison :** {raison}"
                )
            except Exception as e:
                await interaction.response.send_message(
                    f"Erreur lors du mute : {e}",
                    ephemeral=True
                )

        # Ajout
        self.bot.tree.add_command(tempmute)

async def setup(bot):
    await bot.add_cog(TempMute(bot))
