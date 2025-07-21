import discord
from discord.ext import commands
from discord import app_commands

# Remplace cette valeur par l'ID réel du rôle Muted sur ton serveur
MUTED_ROLE_ID = 1394500442922160178

class MuteRoleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        @app_commands.command(
            name="mute",
            description="Ajoute le rôle Muted à un membre."
        )
        @app_commands.describe(
            membre="Le membre à mute",
            raison="La raison du mute"
        )
        async def mute(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison donnée"):
            #  Vérifie permissions utilisateur
            if not interaction.user.guild_permissions.manage_roles:
                await interaction.response.send_message(
                    " Vous n'avez pas la permission de gérer les rôles.",
                    ephemeral=True
                )
                return

            #  Vérifie permissions bot
            if not interaction.guild.me.guild_permissions.manage_roles:
                await interaction.response.send_message(
                    " Je n'ai pas la permission de gérer les rôles sur ce serveur.",
                    ephemeral=True
                )
                return

            # Vérifie hiérarchie des rôles dans le serv
            if membre.top_role >= interaction.guild.me.top_role:
                await interaction.response.send_message(
                    "Je ne peux pas mute ce membre (son rôle est plus haut ou égal au mien).",
                    ephemeral=True
                )
                return

            # Récupère le rôle via son ID discord
            muted_role = interaction.guild.get_role(MUTED_ROLE_ID)
            if muted_role is None:
                await interaction.response.send_message(
                    f" Le rôle avec l'ID `{MUTED_ROLE_ID}` n'existe pas sur ce serveur ❌.",
                    ephemeral=True
                )
                return

            # Vérifie s'il est déjà mute dans le serv
            if muted_role in membre.roles:
                await interaction.response.send_message(
                    f" {membre.mention} est déjà mute ❌.",
                    ephemeral=True
                )
                return

            # Ajoute le rôle
            try:
                await membre.add_roles(muted_role, reason=raison)
                await interaction.response.send_message(
                    f" {membre.mention} a été **mute** ✅ avec le rôle {muted_role.mention}.\n**Raison :** {raison}"
                )
            except Exception as e:
                await interaction.response.send_message(
                    f" Erreur lors de l'ajout du rôle : {e}",
                    ephemeral=True
                )

        # Ajout
        self.bot.tree.add_command(mute)

async def setup(bot):
    await bot.add_cog(MuteRoleCog(bot))
