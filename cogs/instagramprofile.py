import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from bs4 import BeautifulSoup

class Instagram(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="instagramprofile", description="Afficher les infos publiques d'un profil Instagram")
    @app_commands.describe(username="Nom d'utilisateur Instagram sans @")
    async def instagramprofile(self, interaction: discord.Interaction, username: str):
        await interaction.response.defer()

        url = f"https://www.instagram.com/{username}/"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await interaction.followup.send("❌ Utilisateur introuvable ou inaccessible.")
                    return

                html = await resp.text()

        # Parse avec BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        try:
            # Parse des stats via og:description
            og_desc = soup.find("meta", property="og:description")["content"]
            # Exemple : '123 Followers, 456 Following, 78 Posts - See Instagram photos and videos from John Doe (@johndoe)'
            parts = og_desc.split(" - ")[0].split(", ")
            followers = parts[0].split(" ")[0]
            following = parts[1].split(" ")[0]
            posts = parts[2].split(" ")[0]

            # Nom complet (dans le tag title ou h1)
            full_name_tag = soup.find("h1")
            full_name = full_name_tag.text if full_name_tag else "Nom non trouvé"

            # Bio (dans <meta name="description">)
            bio_tag = soup.find("meta", attrs={"name": "description"})
            bio = bio_tag["content"].split("(@")[0].strip() if bio_tag else "Aucune bio"

            # Photo de profil
            avatar_tag = soup.find("meta", property="og:image")
            avatar_url = avatar_tag["content"] if avatar_tag else None

        except Exception as e:
            await interaction.followup.send("❌ Erreur lors de l'extraction du profil.")
            return

        # Embed Discord
        embed = discord.Embed(
            title=f"@{username}",
            url=url,
            description=bio,
            color=discord.Color.magenta()
        )
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)
        embed.add_field(name="Nom complet", value=full_name, inline=True)
        embed.add_field(name="Posts", value=posts, inline=True)
        embed.add_field(name="Followers", value=followers, inline=True)
        embed.add_field(name="Following", value=following, inline=True)

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Instagram(bot))
