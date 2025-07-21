import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from collections import Counter
import itertools
import json
import os

active_games = {}

# 
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

# 
RANK_ORDER = "23456789TJQKA"
RANK_VALUES = {r: i for i, r in enumerate(RANK_ORDER, 2)}

def card_rank(card):
    return RANK_VALUES[card[0]]

def card_suit(card):
    return card[1]

def evaluate_hand(cards):
    ranks = [card_rank(c) for c in cards]
    suits = [card_suit(c) for c in cards]

    suit_counts = Counter(suits)
    rank_counts = Counter(ranks)

    flush_suit = None
    for s, count in suit_counts.items():
        if count >= 5:
            flush_suit = s
            break

    flush_cards = []
    if flush_suit:
        flush_cards = sorted([card_rank(c) for c in cards if card_suit(c) == flush_suit], reverse=True)

    distinct_ranks = set(ranks)
    if 14 in distinct_ranks:
        distinct_ranks.add(1)

    straights = []
    for low in range(1, 11):
        if all((low + i) in distinct_ranks for i in range(5)):
            straights.append(low + 4)

    straight_high = max(straights) if straights else None

    straight_flush_high = None
    if flush_suit:
        flush_ranks_set = set(flush_cards)
        if 14 in flush_ranks_set:
            flush_ranks_set.add(1)
        for low in range(1, 11):
            if all((low + i) in flush_ranks_set for i in range(5)):
                straight_flush_high = low + 4
                break

    if straight_flush_high:
        return ((9, straight_flush_high), "Quinte Flush")

    four = [r for r, c in rank_counts.items() if c == 4]
    if four:
        kicker = max([r for r in ranks if r != four[0]])
        return ((8, four[0], kicker), "Carré")

    trips = [r for r, c in rank_counts.items() if c >= 3]
    pairs = [r for r, c in rank_counts.items() if c >= 2]
    if trips:
        trips_best = max(trips)
        others = [r for r in pairs if r != trips_best]
        if others:
            pair_best = max(others)
            return ((7, trips_best, pair_best), "Full House")

    if flush_suit:
        return ((6, flush_cards[:5]), "Couleur")

    if straight_high:
        return ((5, straight_high), "Suite")

    if trips:
        kicker = sorted([r for r in ranks if r != trips[0]], reverse=True)[:2]
        return ((4, trips[0], kicker), "Brelan")

    pairs_all = [r for r, c in rank_counts.items() if c >= 2]
    if len(pairs_all) >= 2:
        high, low = sorted(pairs_all, reverse=True)[:2]
        kicker = max([r for r in ranks if r != high and r != low])
        return ((3, high, low, kicker), "Deux Paires")

    if len(pairs_all) >= 1:
        pair = max(pairs_all)
        kicker = sorted([r for r in ranks if r != pair], reverse=True)[:3]
        return ((2, pair, kicker), "Paire")

    best = sorted(ranks, reverse=True)[:5]
    return ((1, best), "Carte Haute")

# 
class PokerGame:
    def __init__(self, host_id):
        self.host_id = host_id
        self.players = set()
        self.active_players = set()
        self.hands = {}
        self.started = False
        self.community_cards = []
        self.deck = [f"{rank}{suit}" for rank in RANK_ORDER for suit in "♠♥♦♣"]
        random.shuffle(self.deck)
        self.phase = 0
        self.bets = {}
        self.pot = 0

    def add_player(self, user_id):
        if self.started:
            return False
        self.players.add(user_id)
        return True

    def deal_private(self):
        for player in self.players:
            self.hands[player] = [self.deck.pop(), self.deck.pop()]
        self.active_players = set(self.players)

    def reveal_next_phase(self):
        if self.phase == 0:
            self.community_cards = [self.deck.pop() for _ in range(3)]
        elif self.phase == 1:
            self.community_cards.append(self.deck.pop())
        elif self.phase == 2:
            self.community_cards.append(self.deck.pop())
        self.phase += 1

    def is_showdown(self):
        return self.phase >= 3 or len(self.active_players) <= 1

#
class BetView(discord.ui.View):
    def __init__(self, game: PokerGame, channel, bot, poker_view):
        super().__init__(timeout=60)
        self.game = game
        self.channel = channel
        self.bot = bot
        self.poker_view = poker_view
        self.responses = set()

    async def check_all_bets(self):
        if self.responses >= self.game.players:
            await self.channel.send("Tous les joueurs ont misé. La partie commence !")
            self.stop()
            await self.poker_view.start_game(self.channel)

    async def handle_bet(self, interaction, amount):
        user_id = interaction.user.id
        balance = get_balance(user_id)
        if balance < amount:
            await interaction.response.send_message(f"Tu n'as pas assez d'argent. Solde actuel : {balance}.", ephemeral=True)
            return

        adjust_balance(user_id, -amount)
        self.game.bets[user_id] = amount
        self.game.pot += amount

        self.responses.add(user_id)
        await interaction.response.send_message(f"Mise acceptée ! Tu as misé {amount}.", ephemeral=True)
        await self.check_all_bets()

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

class PokerView(discord.ui.View):
    def __init__(self, game: PokerGame, channel_id, bot):
        super().__init__(timeout=None)
        self.game = game
        self.channel_id = channel_id
        self.bot = bot
        self.responses = {}

    @discord.ui.button(label="Rejoindre la table", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game.started:
            await interaction.response.send_message("La partie a déjà commencé.", ephemeral=True)
            return
        added = self.game.add_player(interaction.user.id)
        if not added:
            await interaction.response.send_message("Erreur pour rejoindre.", ephemeral=True)
            return
        await interaction.response.send_message(f"{interaction.user.mention} a rejoint la table !", ephemeral=False)

    @discord.ui.button(label="Démarrer la partie", style=discord.ButtonStyle.primary)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.game.host_id:
            await interaction.response.send_message("Seul l'hôte peut démarrer la partie.", ephemeral=True)
            return
        if len(self.game.players) < 2:
            await interaction.response.send_message("Il faut au moins 2 joueurs dans le jeux pour commencer.", ephemeral=True)
            return

        self.game.started = True
        self.clear_items()
        await interaction.response.edit_message(content="La partie commence ! Choisissez vos mises.", view=None)
        await self.ask_bets(interaction.channel)

    async def ask_bets(self, channel):
        bet_view = BetView(self.game, channel, self.bot, self)
        await channel.send(
            "📌📌 **Choisissez votre mise pour participer au pot commun !**📌📌\n"
            "Boutons disponibles : 25, 50, 75, 100",
            view=bet_view
        )

    async def start_game(self, channel):
        self.game.deal_private()
        for uid in self.game.players:
            user = await self.bot.fetch_user(uid)
            hand = self.game.hands[uid]
            try:
                await user.send(f"**Ta main privée :** {hand[0]} {hand[1]}")
            except:
                pass

        await channel.send(
            f"Les cartes privées ont été distribuées en DM aux joueurs : {', '.join(f'<@{uid}>' for uid in self.game.players)}"
        )

        await self.next_phase(channel)

    async def next_phase(self, channel):
        if self.game.is_showdown():
            await self.showdown(channel)
            return

        self.game.reveal_next_phase()
        phase_name = ["FLOP", "TURN", "RIVER"]
        text = f"**{phase_name[self.game.phase - 1]}** : {' '.join(self.game.community_cards)}\n"
        text += "Joueurs encore en jeu : " + ', '.join(f"<@{uid}>" for uid in self.game.active_players)
        text += "\nDécidez si vous continuez ou vous vous retirez !"

        view = DecisionView(self.game, self.channel_id, self.bot, self)
        await channel.send(text, view=view)

    async def showdown(self, channel):
        if not self.game.active_players:
            await channel.send("Tout le monde s'est retiré. Pas de vainqueur.")
            active_games.pop(self.channel_id, None)
            return

        await channel.send(
            f"**SHOWDOWN !**\nJoueurs restants : {', '.join(f'<@{uid}>' for uid in self.game.active_players)}"
        )

        reveal = ""
        results = {}
        for uid in self.game.active_players:
            full_hand = self.game.hands[uid] + self.game.community_cards
            score, desc = evaluate_hand(full_hand)
            results[uid] = (score, desc)
            hand_str = f"{self.game.hands[uid][0]} {self.game.hands[uid][1]}"
            reveal += f"<@{uid}> : {hand_str} → {desc}\n"

        await channel.send("**Mains dévoilées :**\n" + reveal)

        winner = max(results.items(), key=lambda item: item[1][0])[0]
        adjust_balance(winner, self.game.pot)
        await channel.send(
            f"🏆 **<@{winner}> remporte la partie avec {results[winner][1]} ! Félicitations !**\n"
            f"Il gagne le pot de {self.game.pot}."
        )

        active_games.pop(self.channel_id, None)

class DecisionView(discord.ui.View):
    def __init__(self, game: PokerGame, channel_id, bot, poker_view):
        super().__init__(timeout=60)
        self.game = game
        self.channel_id = channel_id
        self.bot = bot
        self.poker_view = poker_view
        self.responses = set()

    @discord.ui.button(label="Continuer", style=discord.ButtonStyle.success)
    async def continue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.game.active_players:
            await interaction.response.send_message("Tu n'es plus dans la partie.", ephemeral=True)
            return
        self.responses.add(interaction.user.id)
        await interaction.response.send_message("Tu continues !", ephemeral=True)
        await self.check_all_responses(interaction)

    @discord.ui.button(label="Se retirer", style=discord.ButtonStyle.danger)
    async def fold_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.game.active_players:
            await interaction.response.send_message("Tu n'es plus dans la partie.", ephemeral=True)
            return
        self.game.active_players.remove(interaction.user.id)
        self.responses.add(interaction.user.id)
        await interaction.response.send_message("Tu t'es retiré !", ephemeral=True)
        await self.check_all_responses(interaction)

    async def check_all_responses(self, interaction):
        if self.responses >= self.game.active_players:
            await interaction.channel.send("Tous les joueurs ont choisi. Passage à la phase suivante...")
            await self.poker_view.next_phase(interaction.channel)
            self.stop()

# 
class Poker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="poker", description="Créer une partie de poker")
    async def poker(self, interaction: discord.Interaction):
        if interaction.channel.id in active_games:
            await interaction.response.send_message("Il y a déjà une partie ici !", ephemeral=True)
            return

        game = PokerGame(host_id=interaction.user.id)
        game.add_player(interaction.user.id)
        active_games[interaction.channel.id] = game

        view = PokerView(game, interaction.channel.id, self.bot)
        await interaction.response.send_message(
            f"{interaction.user.mention} a créé une table de poker ! Cliquez pour rejoindre ou démarrer.",
            view=view
        )

    @app_commands.command(name="solde", description="Voir ton solde")
    async def solde(self, interaction: discord.Interaction):
        balance = get_balance(interaction.user.id)
        await interaction.response.send_message(f" Ton solde est de {balance} 💰.")

async def setup(bot):
    await bot.add_cog(Poker(bot))
