import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os

# ----------- BANK SYSTEM (copié dedans) -----------
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

# ----------- Blackjack COG -----------
class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def draw_card(self):
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = ['♠', '♥', '♦', '♣']
        return f"{random.choice(ranks)}{random.choice(suits)}"

    def hand_value(self, cards):
        value = 0
        aces = 0
        for card in cards:
            rank = card[:-1]
            if rank in ['J', 'Q', 'K']:
                value += 10
            elif rank == 'A':
                aces += 1
                value += 11
            else:
                value += int(rank)
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value

    @app_commands.command(name="blackjack", description="Joue au blackjack contre le bot !")
    async def blackjack(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "📌 **Choisis ta mise pour cette partie de blackjack !**\nBoutons : 25, 50, 75, 100",
            view=BlackjackBetView(self.bot, interaction.user, interaction.channel)
        )

# ----------- Bet View -----------
class BlackjackBetView(discord.ui.View):
    def __init__(self, bot, user, channel):
        super().__init__(timeout=60)
        self.bot = bot
        self.user = user
        self.channel = channel

    async def handle_bet(self, interaction, amount):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Ce n'est pas ta partie !", ephemeral=True)
            return

        balance = get_balance(self.user.id)
        if balance < amount:
            await interaction.response.send_message(
                f"Tu n'as pas assez d'argent. Solde actuel : {balance}.", ephemeral=True
            )
            return

        adjust_balance(self.user.id, -amount)
        await interaction.response.send_message(
            f"✅ Mise de {amount} acceptée ! Bonne chance !", ephemeral=True
        )
        await self.channel.send(
            f"{self.user.mention} a misé {amount} ! La partie commence..."
        )
        await self.start_blackjack(amount)
        self.stop()

    async def start_blackjack(self, bet):
        bj_cog = self.bot.get_cog('Blackjack')
        player_cards = [bj_cog.draw_card(), bj_cog.draw_card()]
        dealer_cards = [bj_cog.draw_card(), bj_cog.draw_card()]

        await self.channel.send(
            f"**Tes cartes :** {' '.join(player_cards)} (total {bj_cog.hand_value(player_cards)})\n"
            f"**Carte visible du croupier :** {dealer_cards[0]}"
        )

        await self.channel.send(
            f"{self.user.mention}, à toi de jouer !",
            view=BlackjackPlayView(self.bot, self.user, self.channel, player_cards, dealer_cards, bet)
        )

    @discord.ui.button(label="25", style=discord.ButtonStyle.secondary)
    async def bet_25(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_bet(interaction, 25)

    @discord.ui.button(label="50", style=discord.ButtonStyle.secondary)
    async def bet_50(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_bet(interaction, 50)

    @discord.ui.button(label="75", style=discord.ButtonStyle.secondary)
    async def bet_75(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_bet(interaction, 75)

    @discord.ui.button(label="100", style=discord.ButtonStyle.secondary)
    async def bet_100(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_bet(interaction, 100)

# ----------- Play View -----------
class BlackjackPlayView(discord.ui.View):
    def __init__(self, bot, user, channel, player_cards, dealer_cards, bet):
        super().__init__(timeout=120)
        self.bot = bot
        self.user = user
        self.channel = channel
        self.player_cards = player_cards
        self.dealer_cards = dealer_cards
        self.bet = bet

    async def end_game(self, interaction, result_text):
        await interaction.channel.send(result_text)
        self.stop()

    @discord.ui.button(label="Tirer", style=discord.ButtonStyle.success)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Ce n'est pas ta partie !", ephemeral=True)
            return

        bj_cog = self.bot.get_cog('Blackjack')
        new_card = bj_cog.draw_card()
        self.player_cards.append(new_card)
        total = bj_cog.hand_value(self.player_cards)

        await interaction.response.send_message(
            f"🃏 Tu as tiré {new_card}.\n**Tes cartes :** {' '.join(self.player_cards)} (total {total})",
            ephemeral=False
        )

        if total > 21:
            await self.end_game(interaction, f"💥 {self.user.mention} tu dépasses 21 ! Tu perds ta mise de {self.bet}.")
        else:
            await interaction.channel.send(f"{self.user.mention}, que veux-tu faire ?", view=self)

    @discord.ui.button(label="Rester", style=discord.ButtonStyle.primary)
    async def stay(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Ce n'est pas ta partie !", ephemeral=True)
            return

        await interaction.response.send_message("Tu restes. C'est au croupier.", ephemeral=False)

        bj_cog = self.bot.get_cog('Blackjack')
        dealer_total = bj_cog.hand_value(self.dealer_cards)
        dealer_cards_str = ' '.join(self.dealer_cards)
        await self.channel.send(
            f"**Croupier montre :** {dealer_cards_str} (total {dealer_total})"
        )

        while dealer_total < 17:
            new_card = bj_cog.draw_card()
            self.dealer_cards.append(new_card)
            dealer_total = bj_cog.hand_value(self.dealer_cards)
            await self.channel.send(
                f"🃏 Le croupier tire {new_card}. Total : {dealer_total}"
            )

        player_total = bj_cog.hand_value(self.player_cards)
        result = ""
        if dealer_total > 21 or player_total > dealer_total:
            adjust_balance(self.user.id, self.bet * 2)
            result = f"🏆 {self.user.mention} tu gagnes ! Tu remportes {self.bet * 2}."
        elif dealer_total == player_total:
            adjust_balance(self.user.id, self.bet)
            result = f"🤝 Égalité. {self.user.mention} récupère sa mise."
        else:
            result = f"😢 {self.user.mention} tu perds ta mise de {self.bet}."

        await self.end_game(interaction, result)

# ----------- Setup function -----------
async def setup(bot):
    await bot.add_cog(Blackjack(bot))
