# utils/permissions.py
import discord
from typing import Optional, Union

class Permissions:
    """Gestion unifiée des permissions et contrôles d'accès"""
    
    @staticmethod
    async def is_owner(bot: discord.Client, user: Union[discord.User, discord.Member]) -> bool:
        """Vérifie si l'utilisateur est le propriétaire du bot"""
        return await bot.is_owner(user)
    
    @staticmethod
    def is_room_owner(bot, channel_id: int, user_id: int) -> bool:
        """Vérifie si l'utilisateur est le propriétaire de la room temporaire en mémoire"""
        return bot.temp_channels.get(channel_id) == user_id
    
    @staticmethod
    def is_temp_room(bot, channel_id: int) -> bool:
        """Vérifie si le salon vocal donné est une room temporaire active"""
        return channel_id in bot.temp_channels
    
    @staticmethod
    async def can_manage_room(bot, channel: discord.VoiceChannel, user: discord.Member) -> bool:
        """Vérifie si l'utilisateur peut gérer la room temporaire (Propriétaire du bot ou proprio de la room)"""
        if await Permissions.is_owner(bot, user):
            return True
        if not Permissions.is_temp_room(bot, channel.id):
            return False
        return Permissions.is_room_owner(bot, channel.id, user.id)
    
    @staticmethod
    def is_admin(member: discord.Member) -> bool:
        """Vérifie si le membre possède les permissions d'administration"""
        return member.guild_permissions.administrator
    
    @staticmethod
    def is_moderator(member: discord.Member) -> bool:
        """Vérifie si le membre est modérateur"""
        perms = member.guild_permissions
        return perms.administrator or perms.kick_members or perms.ban_members or perms.manage_messages