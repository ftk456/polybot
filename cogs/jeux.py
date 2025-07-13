from discord.ext import commands
import random

class Gambling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def pileouface(self):
        resultat = random.randint(0, 1)
        return

#await bot.add_cog(Gambling(client))