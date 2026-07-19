# utils/permissions.py
import discord
from typing import Optional, Union

class Permissions:
    """Gestion des permissions"""
    
    @staticmethod
    async def is_owner(bot, user: Union[discord.User, discord.Member]) -> bool:
        """Vérifie si l'utilisateur est le propriétaire du bot"""
        return await bot.is_owner(user)
    
    @staticmethod
    async def is_room_owner(bot, channel: discord.VoiceChannel, user: discord.Member) -> bool:
        """Vérifie si l'utilisateur est propriétaire de la room"""
        return bot.temp_channels.get(channel.id) == user.id
    
    @staticmethod
    async def is_in_temp_room(bot, channel: discord.VoiceChannel) -> bool:
        """Vérifie si le salon est une room temporaire"""
        return channel.id in bot.temp_channels
    
    @staticmethod
    async def can_manage_room(bot, channel: discord.VoiceChannel, user: discord.Member) -> bool:
        """Vérifie si l'utilisateur peut gérer la room"""
        # Le propriétaire du bot peut tout gérer
        if await Permissions.is_owner(bot, user):
            return True
        
        # Vérifier si c'est une room temporaire
        if not await Permissions.is_in_temp_room(bot, channel):
            return False
        
        # Vérifier si l'utilisateur est le propriétaire
        return await Permissions.is_room_owner(bot, channel, user)
    
    @staticmethod
    async def get_room_owner(bot, channel: discord.VoiceChannel) -> Optional[int]:
        """Récupère l'ID du propriétaire de la room"""
        return bot.temp_channels.get(channel.id)
    
    @staticmethod
    async def transfer_ownership(bot, channel: discord.VoiceChannel, new_owner_id: int) -> bool:
        """Transfère la propriété d'une room"""
        if channel.id not in bot.temp_channels:
            return False
        
        bot.temp_channels[channel.id] = new_owner_id
        return True
    
    @staticmethod
    def has_permission(member: discord.Member, permission: str) -> bool:
        """Vérifie si un membre a une permission spécifique"""
        return getattr(member.guild_permissions, permission, False)
    
    @staticmethod
    async def is_admin(member: discord.Member) -> bool:
        """Vérifie si le membre est administrateur"""
        return member.guild_permissions.administrator
    
    @staticmethod
    async def is_moderator(member: discord.Member) -> bool:
        """Vérifie si le membre est modérateur"""
        return (member.guild_permissions.kick_members or 
                member.guild_permissions.ban_members or 
                member.guild_permissions.manage_messages)
    
    @staticmethod
    async def get_member_permissions(member: discord.Member) -> list:
        """Retourne la liste des permissions du membre"""
        permissions = []
        for perm, value in member.guild_permissions:
            if value:
                permissions.append(perm)
        return permissions