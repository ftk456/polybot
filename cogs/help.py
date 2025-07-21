import discord
from discord.ext import commands
from discord import app_commands

class HelpView(discord.ui.View):
    def __init__(self, embeds):
        super().__init__(timeout=None)
        self.embeds = embeds
        self.current = 0

    @discord.ui.button(label="Modérations", style=discord.ButtonStyle.primary, custom_id="help_mod")
    async def mod_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.embeds[0], view=self)

    @discord.ui.button(label="Jeux", style=discord.ButtonStyle.success, custom_id="help_jeux")
    async def jeux_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.embeds[1], view=self)

    @discord.ui.button(label="Extra", style=discord.ButtonStyle.secondary, custom_id="help_extra")
    async def extra_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.embeds[2], view=self)

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Affiche l'aide du bot avec les différentes catégories")
    async def help(self, interaction: discord.Interaction):
        embeds = []

        embed_mod = discord.Embed(
            title="📌 Aide - Catégorie : Modérations",
            description=(
                "**/kick** - Expulser un membre\n"
                "**/ban** - Bannir un membre\n"
                "**/unban** - Débannir un membre\n"
                "**/mute** - Mute un membre\n"
                "**/unmute** - Unmute un membre\n"
                "**/tempmute** - Mute temporairement un membre\n"
                "**/warn** - Avertir un membre\n"
                "**/hswarn** - Voir les warns d'un membre\n"
            ),
            color=discord.Color.red()
        )
        embeds.append(embed_mod)

        embed_jeux = discord.Embed(
            title="🎲 Aide - Catégorie : Jeux",
            description=(
                "**/jeux** - Commandes jeux générales\n"
                "**/peche** - Aller pêcher\n"
                "**/poker** - Jouer au poker\n"
                "**/blackjack** - Jouer au blackjack\n"
                "**/roulette** - Jouer a la roulette russe avec les membres\n"
                "**/claque** - Ce bastonne avec un membre"
            ),
            color=discord.Color.green()
        )
        embeds.append(embed_jeux)

        embed_extra = discord.Embed(
            title="✨ Aide - Catégorie : Extra",
            description=(
                "**/botp** - Commande spéciale du bot\n"
                "**/role** - Commande spéciale pour les admins pour attribué un role vite\n"
                "**/economie** - Gestion de l'économie du serveur\n"
                "**/serverinfo** - Infos sur le serveur\n"
                "**/userinfo** - Infos sur un utilisateur\n"
                "**/botinfo** - Infos sur le bot\n"
                "**/clear** - Supprime les messages\n"
                "**/magasin** - Voir le magasin\n"
                "**/configmagasin** - Config le magasin\n"
                "**/configmagasindelete** - Supp des articles du magasin\n"
                "**/ticket** - Permet de crée u ticket depuis n'importe ou\n"
                "**/robloxprofile** - Permet de voir le profile d'un compte roblox\n"
                "**/instagramprofile** - Permet de voir le porfile instagram\n"
                "**/statusbot** - Permet de personnalisée le status du bot et le rich presence\n"
            ),
            color=discord.Color.blue()
        )
        embeds.append(embed_extra)

        view = HelpView(embeds)
        await interaction.response.send_message(embed=embeds[0], view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Help(bot))
