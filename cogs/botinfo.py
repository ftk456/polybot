import discord
from discord.ext import commands
from discord import app_commands

class BotInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot_owner_id = 833997795416473620  # Remplace par ton ID Discord

    async def cog_load(self):
        @app_commands.command(name="botinfo", description="Affiche les infos du bot")
        async def botinfo(interaction: discord.Interaction):
            owner = self.bot.get_user(self.bot_owner_id) or await self.bot.fetch_user(self.bot_owner_id)
            nb_guilds = len(self.bot.guilds)
            latency = round(self.bot.latency * 1000)

            embed = discord.Embed(title="🤖 Informations du bot", color=discord.Color.blurple())
            embed.add_field(name=" Créateur 👤", value=f"{owner.mention if owner else 'Inconnu'}", inline=False)
            embed.add_field(name="Serveurs 🌐", value=f"{nb_guilds}", inline=False)
            embed.add_field(name=" Latence 📡", value=f"{latency} ms", inline=False)
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar.url)

            await interaction.response.send_message(embed=embed)

        self.bot.tree.add_command(botinfo)

async def setup(bot):
    await bot.add_cog(BotInfo(bot))
