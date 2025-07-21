import discord
from discord.ext import commands
from discord import app_commands
import asyncio


TICKET_CATEGORY_ID = 1394127977029304510  # ← Remplace par l'ID de ta catégorie "Tickets"
MOD_ROLE_IDS = [1181666653629579264, 222222222222222222]  # ← Remplace par les IDs de tes rôles staff

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_counter = 0

    async def cog_load(self):
        @app_commands.command(name="ticket", description="Crée un ticket privé avec le staff")
        @app_commands.describe(raison="Explique pourquoi tu ouvres un ticket")
        async def ticket(interaction: discord.Interaction, raison: str):
            guild = interaction.guild
            auteur = interaction.user
            category = discord.utils.get(guild.categories, id=TICKET_CATEGORY_ID)

            if not category:
                await interaction.response.send_message("❌ Catégorie introuvable. Vérifie l'ID dans le code.", ephemeral=True)
                return

            self.ticket_counter += 1
            ticket_name = f"ticket-{self.ticket_counter}"

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                auteur: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }

            for role_id in MOD_ROLE_IDS:
                role = guild.get_role(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

            salon = await guild.create_text_channel(
                name=ticket_name,
                category=category,
                overwrites=overwrites,
                reason=f"Ticket de {auteur.name} - {raison}"
            )

            await interaction.response.send_message(
                f"🎟️ Ton ticket a été créé ici : {salon.mention}", ephemeral=True
            )

            embed = discord.Embed(title="🎫 Nouveau ticket", color=discord.Color.blue())
            embed.add_field(name="Utilisateur", value=auteur.mention, inline=False)
            embed.add_field(name="Raison", value=raison, inline=False)
            embed.set_footer(text=f"Ticket #{self.ticket_counter}")

            view = FermerTicketView()

            await salon.send(content=f"{auteur.mention}", embed=embed, view=view)

        self.bot.tree.add_command(ticket)

class FermerTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(FermerButton())

import asyncio  # ← AJOUT 

class FermerButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🔒 Fermer le ticket", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("🧹 Fermeture du ticket dans 3 secondes...", ephemeral=True)
        await asyncio.sleep(3)
        try:
            await interaction.channel.delete(reason=f"Ticket fermé par {interaction.user}")
        except discord.Forbidden:
            await interaction.followup.send("❌ Je n'ai pas la permission de supprimer ce salon.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur : {e}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Ticket(bot))
