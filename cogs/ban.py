import discord
from discord.ext import commands
from discord import app_commands

class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        # ✅ Commande slash déclarée dans cog_load comme jeux.py
        @app_commands.command(
            name="ban",
            description="Bannir un membre du serv."
        )
        @app_commands.describe(
            membre="Le membre à bannir",
            raison="La raison du bannissement"
        )
        async def ban(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison donnée"):
            # ✅ Vérifie les permissions de l'utilisateur qui exécute la commande
            if not interaction.user.guild_permissions.ban_members:
                await interaction.response.send_message(
                    " Vous n'avez pas la permission de bannir des membres.",
                    ephemeral=True
                )
                return

            # ✅ Vérifie que le bot a la permission
            if not interaction.guild.me.guild_permissions.ban_members:
                await interaction.response.send_message(
                    " Je n'ai pas la permission de bannir des membres sur ce serveur ❌❌❌❌.",
                    ephemeral=True
                )
                return

            # ✅ Essaye de bannir
            try:
                await membre.ban(reason=raison)
                await interaction.response.send_message(
                    f" {membre.mention} a été **banni** du serveur ✅.\n**Raison :** {raison}"
                )
            except Exception as e:
                await interaction.response.send_message(
                    f" Erreur durant le ban  : {e}",
                    ephemeral=True
                )

        # ✅ Ajoute la commande à l'arbre de commandes
        self.bot.tree.add_command(ban)

async def setup(bot):
    await bot.add_cog(Mod(bot))
