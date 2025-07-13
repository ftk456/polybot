import discord
import cogs.jeux
import cogs.economie

class MyClient(discord.Client):
    async def on_ready(self):
        print("Le bot est en marche !")

    async def on_message(self):
        pass

intents = discord.Intents.default()
client = MyClient(intents=intents)
client.run("")