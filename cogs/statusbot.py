import discord
from discord import app_commands
from discord.ext import commands
import json
import os

STATUS_FILE = "data/status_data.json"

def save_status(status: str, activity: str):
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump({"status": status, "activity": activity}, f)

def load_status():
    if not os.path.exists(STATUS_FILE):
        return {"status": "online", "activity": "En ligne !"}
    with open(STATUS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

class StatusBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.apply_saved_status()

    def apply_saved_status(self):
        data = load_status()
        status_map = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "offline": discord.Status.invisible
        }
        self.bot.loop.create_task(self.bot.change_presence(
            status=status_map.get(data["status"], discord.Status.online),
            activity=discord.Game(name=data["activity"])
        ))

    @app_commands.command(name="statusbot", description="Change le statut du bot et son activité (admin uniquement).")
    @app_commands.describe(
        status="Choisis un statut pour le bot",
        activity="Texte de l'activité (ex: Joue à Polyvaland...)"
    )
    @app_commands.choices(status=[
        app_commands.Choice(name="Connecté", value="online"),
        app_commands.Choice(name="Inactif", value="idle"),
        app_commands.Choice(name="Ne pas déranger", value="dnd"),
        app_commands.Choice(name="Déconnecté", value="offline")
    ])
    async def statusbot(self, interaction: discord.Interaction, status: app_commands.Choice[str], activity: str):
        await interaction.response.defer(ephemeral=True)

        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("Tu dois être admin pour utiliser cette commande.")
            return

        status_map = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "offline": discord.Status.invisible
        }

        await self.bot.change_presence(
            status=status_map[status.value],
            activity=discord.Game(name=activity)
        )

        save_status(status.value, activity)

        await interaction.followup.send(
            f" Statut changé ✅ en **{status.name}** avec l'activité : *{activity}*"
        )

async def setup(bot):
    await bot.add_cog(StatusBot(bot))
