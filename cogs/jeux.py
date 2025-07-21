import discord
from discord.ext import commands
from discord import app_commands
import random

class Jeux(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        # ✅ Déclare le groupe dynamique dans cog_load
        jeux_group = app_commands.Group(
            name="jeux",
            description="Commandes de jeux 🎲"
        )

        @jeux_group.command(name="dice", description="Lance un dé à 6 faces 🎲")
        async def dice(interaction: discord.Interaction):
            result = random.randint(1, 6)
            await interaction.response.send_message(f"🎲 Tu as lancé le dé : {result}")

        @jeux_group.command(name="coinflip", description="Pile ou face 🪙")
        async def coinflip(interaction: discord.Interaction):
            side = random.choice(["Pile", "Face"])
            await interaction.response.send_message(f"🪙 Le résultat est : {side}")

        # ✅ Vérifie avant d'ajouter
        if not any(cmd.name == jeux_group.name for cmd in self.bot.tree.get_commands()):
            self.bot.tree.add_command(jeux_group)

async def setup(bot):
    await bot.add_cog(Jeux(bot))
