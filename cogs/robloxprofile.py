import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import datetime

class Roblox(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="robloxprofile", description="Afficher les infos publiques d'un profil Roblox")
    @app_commands.describe(username="Nom d'utilisateur Roblox")
    async def robloxprofile(self, interaction: discord.Interaction, username: str):
        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:
            # Obtenir l'ID à partir du nom
            url_id = "https://users.roblox.com/v1/usernames/users"
            payload = {"usernames": [username], "excludeBannedUsers": False}
            async with session.post(url_id, json=payload) as resp:
                data = await resp.json()
                if not data["data"]:
                    await interaction.followup.send("❌ Utilisateur introuvable.")
                    return
                user_data = data["data"][0]
                user_id = user_data["id"]

            # Profil général
            async with session.get(f"https://users.roblox.com/v1/users/{user_id}") as resp:
                profile = await resp.json()

            # Nombre d'amis
            async with session.get(f"https://friends.roblox.com/v1/users/{user_id}/friends/count") as resp:
                friends = await resp.json()

            # Followers
            async with session.get(f"https://friends.roblox.com/v1/users/{user_id}/followers/count") as resp:
                followers = await resp.json()

            # Following
            async with session.get(f"https://friends.roblox.com/v1/users/{user_id}/followings/count") as resp:
                followings = await resp.json()

            # Avatar thumbnail
            thumb_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"
            async with session.get(thumb_url) as resp:
                thumb_data = await resp.json()
                avatar_url = thumb_data["data"][0]["imageUrl"] if thumb_data["data"] else None

            # Status
            async with session.get(f"https://users.roblox.com/v1/users/{user_id}/status") as resp:
                status_data = await resp.json()
                status = status_data.get("status", "Aucun statut")
                if not status:
                    status = "Offline"

            # Vérifier badge verified
            badge_keywords = [
                "102611803",
                "Verified Bonafide Plaidafied",
                "Casquette écossaise de vérification"
            ]
            inventory_url = f"https://www.roblox.com/users/{user_id}/inventory/"
            async with session.get(inventory_url) as resp:
                html = await resp.text()
                has_verified_badge = any(keyword.lower() in html.lower() for keyword in badge_keywords)

        # Date création
        created = datetime.datetime.fromisoformat(profile["created"].replace("Z", "+00:00"))
        created_str = created.strftime("%d %B %Y")

        # Embed
        embed = discord.Embed(
            title=f"{profile['name']}",
            url=f"https://www.roblox.com/users/{user_id}/profile",
            color=discord.Color.dark_gray()
        )
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)
        embed.add_field(
            name="Social",
            value=f"Friends: {friends.get('count', 0)} | Followers: {followers.get('count', 0)} | Following: {followings.get('count', 0)}",
            inline=False
        )
        embed.add_field(name="ID", value=str(user_id), inline=True)
        embed.add_field(name="Compte Verif ?", value="✅ Yes" if has_verified_badge else "❌ No", inline=True)
        embed.add_field(name="Status Online/Offline", value=status, inline=True)
        embed.add_field(name="Date de création", value=created_str, inline=True)

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Roblox(bot))
