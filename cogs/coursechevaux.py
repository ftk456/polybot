import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os
import asyncio

# ----------- BANK SYSTEM (intégré) -----------
BANK_FILE = "data/members_banks.json"

def load_banks():
    if not os.path.exists(BANK_FILE):
        return {}
    with open(BANK_FILE, "r") as f:
        return json.load(f)

def save_banks(banks):
    with open(BANK_FILE, "w") as f:
        json.dump(banks, f, indent=2)

def adjust_balance(user_id, amount):
    user_id = str(user_id)
    banks = load_banks()
    if user_id not in banks:
        banks[user_id] = {"balance": 500}
    banks[user_id]["balance"] += amount
    save_banks(banks)

def get_balance(user_id):
    user_id = str(user_id)
    banks = load_banks()
    if user_id not in banks:
        banks[user_id] = {"balance": 500}
        save_banks(banks)
    return banks[user_id]["balance"]

# ----------- GAME LOGIC -----------
active_races = {}

class CourseChevauxGame:
    def __init__(self, host_id):
        self.host_id = host_id
        self.players = set()
        self.started = False
        self.bets = {}  # user_id -> {"amount": int, "horse": int}
        self.total_pot = 0

    def add_player(self, user_id):
        if self.started or user_id in self.players:
            return False
        self.players.add(user_id)
        return True

    def record_bet(self, user_id, amount, horse):
        self.bets[user_id] = {"amount": amount, "horse": horse}
        self.total_pot += amount

    def all_have_bet(self):
        return len(self.bets) == len(self.players)

# ----------- JOIN VIEW -----------
class CourseView(discord.ui.View):
    def __init__(self, game: CourseChevauxGame, channel_id, bot):
        super().__init__(timeout=None)
        self.game = game
        self.channel_id = channel_id
        self.bot = bot

    @discord.ui.button(label="Rejoindre la course", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game.started:
            await interaction.response.send_message("La course a déjà commencé.", ephemeral=True)
            return
        added = self.game.add_player(interaction.user.id)
        if not added:
            await interaction.response.send_message("Tu es déjà inscrit ou la partie est en cours.", ephemeral=True)
            return
        await interaction.response.send_message(f"{interaction.user.mention} a rejoint la course !", ephemeral=False)

    @discord.ui.button(label="Démarrer les paris", style=discord.ButtonStyle.primary)
    async def start_betting(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.game.host_id:
            await interaction.response.send_message("Seul l'hôte peut démarrer la course.", ephemeral=True)
            return
        if len(self.game.players) < 2:
            await interaction.response.send_message("Il faut au moins 2 joueurs pour lancer la course !", ephemeral=True)
            return

        self.game.started = True
        self.clear_items()
        await interaction.response.edit_message(content="Les paris commencent !", view=None)

        await self.ask_bets(interaction.channel)

    async def ask_bets(self, channel):
        await channel.send(
            f"📌 **Participants :** {', '.join(f'<@{uid}>' for uid in self.game.players)}\n"
            "➡️ **Choisissez votre mise et votre cheval (1-6) !**",
        )
        await channel.send(
            " Cliquez pour parier :",
            view=BetMenuView(self.game, channel, self.bot)
        )

# ----------- BET MENU VIEW -----------
class BetMenuView(discord.ui.View):
    def __init__(self, game: CourseChevauxGame, channel, bot):
        super().__init__(timeout=120)
        self.game = game
        self.channel = channel
        self.bot = bot
        self.waiting_for = {uid: {"amount": None, "horse": None} for uid in game.players}

    async def check_all_bets(self):
        if all(v["amount"] and v["horse"] for v in self.waiting_for.values()):
            for uid, bet in self.waiting_for.items():
                self.game.record_bet(uid, bet["amount"], bet["horse"])
            await self.channel.send(" Tous les joueurs ont parié ! ✅ La course démarre...")
            await run_race(self.channel, self.game)
            self.stop()

    async def handle_bet(self, interaction, amount=None, horse=None):
        uid = interaction.user.id
        if uid not in self.waiting_for:
            await interaction.response.send_message("Tu n'es pas dans cette partie !", ephemeral=True)
            return

        if amount:
            if self.waiting_for[uid]["amount"] is not None:
                await interaction.response.send_message(" Tu as déjà choisi ta mise. ✅", ephemeral=True)
                return
            balance = get_balance(uid)
            if balance < amount:
                await interaction.response.send_message(
                    f" Pas assez d'argent ❌. Solde actuel : {balance}.", ephemeral=True
                )
                return
            self.waiting_for[uid]["amount"] = amount
            adjust_balance(uid, -amount)
            await interaction.response.send_message(f" Mise enregistrée 💰 : {amount}.", ephemeral=True)

        if horse:
            if self.waiting_for[uid]["horse"] is not None:
                await interaction.response.send_message(" Tu as déjà choisi ton cheval. ✅", ephemeral=True)
                return
            self.waiting_for[uid]["horse"] = horse
            await interaction.response.send_message(f" Cheval choisi 🐎 : {horse}.", ephemeral=True)

        await self.check_all_bets()

    # Boutons de mise
    @discord.ui.button(label="25", style=discord.ButtonStyle.secondary)
    async def bet_25(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_bet(interaction, amount=25)

    @discord.ui.button(label="50", style=discord.ButtonStyle.secondary)
    async def bet_50(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_bet(interaction, amount=50)

    @discord.ui.button(label="75", style=discord.ButtonStyle.secondary)
    async def bet_75(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_bet(interaction, amount=75)

    @discord.ui.button(label="100", style=discord.ButtonStyle.secondary)
    async def bet_100(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_bet(interaction, amount=100)

    # Boutons de cheval
    @discord.ui.button(label="Cheval 1", style=discord.ButtonStyle.success)
    async def horse_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_bet(interaction, horse=1)

    @discord.ui.button(label="Cheval 2", style=discord.ButtonStyle.success)
    async def horse_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_bet(interaction, horse=2)

    @discord.ui.button(label="Cheval 3", style=discord.ButtonStyle.success)
    async def horse_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_bet(interaction, horse=3)

    @discord.ui.button(label="Cheval 4", style=discord.ButtonStyle.success)
    async def horse_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_bet(interaction, horse=4)

    @discord.ui.button(label="Cheval 5", style=discord.ButtonStyle.success)
    async def horse_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_bet(interaction, horse=5)

    @discord.ui.button(label="Cheval 6", style=discord.ButtonStyle.success)
    async def horse_6(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_bet(interaction, horse=6)

# ----------- COURSE LOGIC WITH ANIMATION -----------
async def run_race(channel, game: CourseChevauxGame):
    horses = [1, 2, 3, 4, 5, 6]
    steps = random.randint(3, 5)

    await channel.send("🏁 **La course commence !** Préparez-vous...")

    for i in range(steps - 1):
        leader = random.choice(horses)
        await asyncio.sleep(2)
        await channel.send(f"🐎 Le Cheval {leader} prend la tête !")

    await asyncio.sleep(2)
    winning_horse = random.randint(1, 6)
    await channel.send(f"🏆🏆🏆 **Le cheval gagnant est le {winning_horse} !** 🎉")

    winners = [uid for uid, bet in game.bets.items() if bet["horse"] == winning_horse]
    losers = [uid for uid in game.bets if uid not in winners]

    if not winners:
        await channel.send(" Aucun joueur n'avait misé sur ce cheval. Les mises sont perdu ! 😢😢")
    else:
        share = game.total_pot // len(winners)
        for uid in winners:
            adjust_balance(uid, share)
        await channel.send(
            f" Les gagnants : {', '.join(f'<@{uid}>' for uid in winners)} remportent chacun **{share}** ! 🎉🎉🎉"
        )

    active_races.pop(channel.id, None)

# ----------- COG -----------
class CourseChevaux(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="coursecheveaux", description="Organiser une course de chevaux avec des paris fictif")
    async def coursecheveaux(self, interaction: discord.Interaction):
        if interaction.channel.id in active_races:
            await interaction.response.send_message(" Il y a déjà une course en cours ici. ❌", ephemeral=True)
            return

        game = CourseChevauxGame(host_id=interaction.user.id)
        game.add_player(interaction.user.id)
        active_races[interaction.channel.id] = game

        view = CourseView(game, interaction.channel.id, self.bot)
        await interaction.response.send_message(
            f"{interaction.user.mention} a lancé une course de chevaux ! Cliquez pour rejoindre ou démarrer.",
            view=view
        )

async def setup(bot):
    await bot.add_cog(CourseChevaux(bot))
