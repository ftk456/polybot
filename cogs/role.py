import discord
from discord.ext import commands
from discord import app_commands

# verif perm admin
async def is_admin(interaction: discord.Interaction) -> bool:
    return interaction.user.guild_permissions.administrator

class Role(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        @app_commands.command(name="role", description="Attribue un rôle à un membre (admin uniquement)")
        @app_commands.check(is_admin)
        async def role(interaction: discord.Interaction, membre: discord.Member, role: discord.Role):
            if role in membre.roles:
                await interaction.response.send_message(f" {membre.mention} a déjà le rôle {role.mention}.", ephemeral=True)
                return

            try:
                await membre.add_roles(role, reason=f"Ajouté par {interaction.user}")
                await interaction.response.send_message(f" Le rôle {role.mention} a été attribué à {membre.mention}. ✅")
            except discord.Forbidden:
                await interaction.response.send_message("Je n’ai pas la permission de donner ce rôle.", ephemeral=True)

        @role.error
        async def role_error(interaction: discord.Interaction, error):
            if isinstance(error, app_commands.errors.CheckFailure):
                await interaction.response.send_message(" Tu dois être administrateur pour utiliser cette commande.", ephemeral=True)

        self.bot.tree.add_command(role)

async def setup(bot):
    await bot.add_cog(Role(bot))
