import discord
from discord.ext import commands
from discord import app_commands

class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        # declare la commande
        @app_commands.command(
            name="kick",
            description="kick un membre du serveur."
        )
        @app_commands.describe(
            membre="Le membre à kick",
            raison="La raison du kick (optionnelle)"
        )
        async def kick(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison fournie."):
            # Vérifie permissions du sev
            if not interaction.user.guild_permissions.kick_members:
                await interaction.response.send_message("Tu n'as pas la permission de kick des membres.", ephemeral=True)
                return

            if not interaction.guild.me.guild_permissions.kick_members:
                await interaction.response.send_message(" Je n'ai pas la permission de kick des membres sur ce serveur ❌.", ephemeral=True)
                return

            # ✅ Tente de kick le pelo
            try:
                await membre.kick(reason=raison)
                await interaction.response.send_message(
                    f"✅ {membre.mention} a été kick du serv.\n**Raison :** {raison}"
                )
            except Exception as e:
                await interaction.response.send_message(
                    f" Impossible de kick {membre.mention}.\nErreur : {e}",
                    ephemeral=True
                )

        # ✅ Ajout si pas déjà présent dans le main
        if not any(cmd.name == "kick" for cmd in self.bot.tree.get_commands()):
            self.bot.tree.add_command(kick)

async def setup(bot):
    await bot.add_cog(Kick(bot))
