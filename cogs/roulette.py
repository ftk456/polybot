import discord
from discord.ext import commands
from discord import app_commands
import random

active_rr_games = {}

class RouletteRusseGame:
    def __init__(self, host_id):
        self.host_id = host_id
        self.players = []
        self.alive_players = []
        self.started = False
        self.current_index = 0

    def add_player(self, user_id):
        if self.started or user_id in self.players:
            return False
        self.players.append(user_id)
        return True

    def start(self):
        self.started = True
        self.alive_players = self.players.copy()
        self.current_index = 0

    def next_player(self):
        if len(self.alive_players) <= 1:
            return None
        self.current_index %= len(self.alive_players)
        return self.alive_players[self.current_index]

    def fire(self):
        # 1 chance sur 6 de mourir
        bullet = random.randint(1, 6)
        if bullet == 1:
            eliminated = self.alive_players.pop(self.current_index)
            # Si encore des joueurs, on remet l'index au bon endroit
            if self.current_index >= len(self.alive_players):
                self.current_index = 0
            return eliminated
        else:
            # Tour suivant
            self.current_index = (self.current_index + 1) % len(self.alive_players)
            return None

class RouletteRusseView(discord.ui.View):
    def __init__(self, game: RouletteRusseGame, channel_id, bot):
        super().__init__(timeout=None)
        self.game = game
        self.channel_id = channel_id
        self.bot = bot

    @discord.ui.button(label="Rejoindre la partie", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game.started:
            await interaction.response.send_message("La partie a déjà commencé.", ephemeral=True)
            return
        added = self.game.add_player(interaction.user.id)
        if not added:
            await interaction.response.send_message("Tu es déjà inscrit ou la partie est en cours.", ephemeral=True)
            return
        await interaction.response.send_message(f"{interaction.user.mention} a rejoint la partie !", ephemeral=False)

    @discord.ui.button(label="Démarrer", style=discord.ButtonStyle.primary)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.game.host_id:
            await interaction.response.send_message("Seul l'hôte peut démarrer la partie.", ephemeral=True)
            return
        if len(self.game.players) < 2:
            await interaction.response.send_message("Il faut au moins 2 joueurs pour jouer !", ephemeral=True)
            return

        self.game.start()
        self.clear_items()
        await interaction.response.edit_message(content="La roulette russe commence !", view=None)

        await self.next_turn(interaction.channel)

    async def next_turn(self, channel):
        if len(self.game.alive_players) == 1:
            winner = self.game.alive_players[0]
            await channel.send(f"🏆 <@{winner}> est le seul survivant et remporte la partie !")
            active_rr_games.pop(self.channel_id, None)
            return

        current_player = self.game.next_player()
        await channel.send(
            f"🎯 C'est au tour de <@{current_player}> de presser la détente...",
            view=TriggerView(self.game, self.channel_id, self.bot, self)
        )

class TriggerView(discord.ui.View):
    def __init__(self, game: RouletteRusseGame, channel_id, bot, roulette_view):
        super().__init__(timeout=60)
        self.game = game
        self.channel_id = channel_id
        self.bot = bot
        self.roulette_view = roulette_view

    @discord.ui.button(label="Appuyer sur la détente", style=discord.ButtonStyle.danger)
    async def trigger(self, interaction: discord.Interaction, button: discord.ui.Button):
        current_player = self.game.next_player()
        if interaction.user.id != current_player:
            await interaction.response.send_message("Ce n'est pas ton tour !", ephemeral=True)
            return

        await interaction.response.defer()

        eliminated = self.game.fire()
        channel = interaction.channel

        if eliminated:
            await channel.send(f" **Bang !** 💥 <@{eliminated}> est éliminé !")
        else:
            await channel.send(f" *Clic...*💨 <@{interaction.user.id}> survit !")

        await self.roulette_view.next_turn(channel)

# 
class RouletteRusse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="roulette", description="Créer une partie de roulette russe")
    async def rouletterusse(self, interaction: discord.Interaction):
        if interaction.channel.id in active_rr_games:
            await interaction.response.send_message("Il y a déjà une partie ici !", ephemeral=True)
            return

        game = RouletteRusseGame(host_id=interaction.user.id)
        game.add_player(interaction.user.id)
        active_rr_games[interaction.channel.id] = game

        view = RouletteRusseView(game, interaction.channel.id, self.bot)
        await interaction.response.send_message(
            f"{interaction.user.mention} a lancé une partie de roulette russe ! Cliquez pour rejoindre ou démarrer.",
            view=view
        )

async def setup(bot):
    await bot.add_cog(RouletteRusse(bot))
