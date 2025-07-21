import discord
from discord.ext import commands
from discord import app_commands

class UserInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        # marche
        @app_commands.command(
            name="userinfo",
            description="Affiche tes informations publiques ou celles d'un autre membre"
        )
        @app_commands.describe(
            membre="Le membre dont tu veux voir les infos (laisser vide pour toi)"
        )
        async def userinfo(interaction: discord.Interaction, membre: discord.User = None):
            user = membre or interaction.user

            embed = discord.Embed(
                title=f"Informations sur {user}",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=user.avatar.url if user.avatar else discord.Embed.Empty)
            embed.add_field(name="Nom", value=f"{user.name}#{user.discriminator}", inline=True)
            embed.add_field(name="ID", value=user.id, inline=True)
            embed.add_field(name="Créé le", value=user.created_at.strftime("%d/%m/%Y à %H:%M:%S"), inline=False)
            embed.set_footer(text=f"Demandé par {interaction.user.display_name}")

            await interaction.response.send_message(embed=embed)

        # Ajout 
        if not any(cmd.name == "userinfo" for cmd in self.bot.tree.get_commands()):
            self.bot.tree.add_command(userinfo)

async def setup(bot):
    await bot.add_cog(UserInfo(bot))
