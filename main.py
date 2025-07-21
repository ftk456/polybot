import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ✅ Nom des cogs à charger
COGS = [
    "cogs.jeux",
    "cogs.economie",
    "cogs.serverinfo",
    "cogs.userinfo",
    "cogs.kick",
    "cogs.magasin",
    "cogs.botp",
    "cogs.peche",
    "cogs.ban",
    "cogs.unban",
    "cogs.mute",
    "cogs.unmute",
    "cogs.tempmute",
    "cogs.warn",
    "cogs.hswarn",
    "cogs.poker",
    "cogs.help",
    "cogs.blackjack",
    "cogs.roulette",
    "cogs.clear",
    "cogs.coursechevaux",
    "cogs.claque",
    "cogs.botinfo",
    "cogs.role",
    "cogs.ticket",
    "cogs.robloxprofile",
    "cogs.instagramprofile",
    "cogs.statusbot",
]

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    await bot.tree.sync()
    print("✅ Slash commands ON")
    print("✅ Bot prêt. : [reload] [stop] tape ca dans le cmd pour fast restart ou stop le bot")

async def load_extensions():
    for ext in COGS:
        try:
            await bot.load_extension(ext)
            print(f"✅ Code chargée : {ext}")
        except commands.errors.ExtensionAlreadyLoaded:
            await bot.reload_extension(ext)
            print(f"♻️ Code rechargée : {ext}")

async def cmd_input():
    while True:
        cmd = await asyncio.get_event_loop().run_in_executor(None, input, "> ")
        cmd = cmd.strip().lower()

        if cmd == "reload":
            print("♻️ Relancement des cogs...")
            await load_extensions()
            await bot.tree.sync()
            print("✅ Tous les cogs rechargés et slash fonctionne.")
        elif cmd == "stop":
            print("Fermeture du bot...")
            await bot.close()
            break
        else:
            print("Commande inconnue. Utilise : reload / stop")

async def main():
    async with bot:
        # Lancer le bot + la lecture du CMD en parallèle pour quil marche
        await asyncio.gather(
            load_extensions(),
            bot.start(""),
            cmd_input(),
        )

asyncio.run(main())