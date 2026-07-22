# cogs/logs.py
import discord
from discord.ext import commands
import logging
from typing import Optional, List, Dict, Any

from utils.embeds import EmbedFactory

logger = logging.getLogger(__name__)

class LogsCog(commands.Cog, name="Journalisation"):
    """Cog pour le système complet de logs du serveur et notifications vocales"""
    
    def __init__(self, bot):
        self.bot = bot

    async def get_log_channel(self, guild: discord.Guild, log_type: str = "log_channel_id") -> Optional[discord.TextChannel]:
        """Récupère le salon de logs configuré pour la guilde"""
        try:
            settings = await self.bot.db.get_guild_settings(guild.id)
            channel_id = settings.get(log_type) or settings.get("log_channel_id")
            if channel_id:
                channel = guild.get_channel(channel_id)
                if channel and isinstance(channel, discord.TextChannel):
                    return channel
            return None
        except Exception:
            return None

    # ------------------ LOGS VOCAUX (COMMANDE ET ÉVÉNEMENTS #6) ------------------ #

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Détection des entrées, sorties et déplacements dans les salons vocaux"""
        if member.bot:
            return

        guild = member.guild
        log_channel = await self.get_log_channel(guild, "voice_log_channel_id")
        if not log_channel:
            return

        # 1. Connexion à un salon vocal
        if before.channel is None and after.channel is not None:
            embed = EmbedFactory.build(
                title="🔊 Salon Vocal Rejoint",
                description=f"**{member.mention}** (`{member.display_name}`) a rejoint le salon vocal **{after.channel.name}**.",
                color='voice',
                guild=guild,
                author=member
            )
            await log_channel.send(embed=embed)

        # 2. Déconnexion d'un salon vocal
        elif before.channel is not None and after.channel is None:
            embed = EmbedFactory.build(
                title="🔇 Salon Vocal Quitté",
                description=f"**{member.mention}** (`{member.display_name}`) a quitté le salon vocal **{before.channel.name}**.",
                color='warning',
                guild=guild,
                author=member
            )
            await log_channel.send(embed=embed)

        # 3. Changement de salon vocal
        elif before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
            embed = EmbedFactory.build(
                title="➡️ Déplacement Vocal",
                description=f"**{member.mention}** (`{member.display_name}`) est passé de **\"{before.channel.name}\"** vers **\"{after.channel.name}\"**.",
                color='info',
                guild=guild,
                author=member
            )
            await log_channel.send(embed=embed)

    # ------------------ LOGS DE MESSAGES (#13) ------------------ #

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Notification lors de la suppression d'un message"""
        if message.author.bot or not message.guild:
            return

        log_channel = await self.get_log_channel(message.guild)
        if not log_channel:
            return

        content = message.content if message.content else "*[Aucun contenu texte / Média]*"
        
        fields = [
            {'name': "Auteur", 'value': f"{message.author.mention} (`{message.author.id}`)", 'inline': True},
            {'name': "Salon", 'value': message.channel.mention, 'inline': True},
            {'name': "Contenu du message", 'value': content[:1024], 'inline': False}
        ]
        
        embed = EmbedFactory.build(
            title="🗑️ Message Supprimé",
            color='error',
            fields=fields,
            guild=message.guild,
            author=message.author
        )
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Notification lors de la modification d'un message"""
        if before.author.bot or not before.guild:
            return
        if before.content == after.content:
            return

        log_channel = await self.get_log_channel(before.guild)
        if not log_channel:
            return

        fields = [
            {'name': "Auteur", 'value': f"{before.author.mention} (`{before.author.id}`)", 'inline': True},
            {'name': "Salon", 'value': before.channel.mention, 'inline': True},
            {'name': "Avant", 'value': before.content[:1000] if before.content else "*[Vide]*", 'inline': False},
            {'name': "Après", 'value': after.content[:1000] if after.content else "*[Vide]*", 'inline': False}
        ]
        
        embed = EmbedFactory.build(
            title="✏️ Message Modifié",
            color='warning',
            fields=fields,
            guild=before.guild,
            author=before.author
        )
        await log_channel.send(embed=embed)

    # ------------------ LOGS DE MODÉRATION (BANS #13) ------------------ #

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """Notification lors du bannissement d'un membre"""
        log_channel = await self.get_log_channel(guild)
        if not log_channel:
            return

        embed = EmbedFactory.build(
            title="🚫 Membre Banni du Serveur",
            description=f"**{user.name}** (`{user.id}`) a été banni de **{guild.name}**.",
            color='error',
            guild=guild,
            thumbnail_url=user.display_avatar.url if hasattr(user, 'display_avatar') else None
        )
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        """Notification lors du débannissement d'un membre"""
        log_channel = await self.get_log_channel(guild)
        if not log_channel:
            return

        embed = EmbedFactory.build(
            title="✅ Membre Débanni du Serveur",
            description=f"**{user.name}** (`{user.id}`) a été débanni de **{guild.name}**.",
            color='success',
            guild=guild,
            thumbnail_url=user.display_avatar.url if hasattr(user, 'display_avatar') else None
        )
        await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LogsCog(bot))
