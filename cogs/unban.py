import discord
from discord.ext import commands
from discord import app_commands

class Mods(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        # affiche le / dans le serv
        @app_commands.command(
            name="unban",
            description="Débannir un utilisateur du serveur via son ID."
        )
        @app_commands.describe(
            user_id="L'ID de l'utilisateur à débannir",
            raison="La raison du débannissement"
        )
        async def unban(interaction: discord.Interaction, user_id: str, raison: str = "Aucune raison donnée"):
            #  Vérifie les perm
            if not interaction.user.guild_permissions.ban_members:
                await interaction.response.send_message(
                    "Vous n'avez pas la permission de débannir des membres.",
                    ephemeral=True
                )
                return

            if not interaction.guild.me.guild_permissions.ban_members:
                await interaction.response.send_message(
                    " Je n'ai pas la permission de débannir des membres sur ce serveur.",
                    ephemeral=True
                )
                return

            try:
                user = await self.bot.fetch_user(int(user_id))
                await interaction.guild.unban(user, reason=raison)
                await interaction.response.send_message(
                    f" {user.mention} a été **débanni** du serveur ✅.\n**Raison :** {raison}"
                )
            except discord.NotFound:
                await interaction.response.send_message(
                    " Aucun ban trouvé avec cet ID ❌.",
                    ephemeral=True
                )
            except Exception as e:
                await interaction.response.send_message(
                    f" Erreur lors du débannissement : {e}",
                    ephemeral=True
                )

        # Ajout
        self.bot.tree.add_command(unban)

async def setup(bot):
    await bot.add_cog(Mods(bot))