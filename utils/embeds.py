# utils/embeds.py
import discord
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union

class EmbedFactory:
    """Générateur centralisé d'embeds modernes et professionnels pour RymBot"""
    
    # Couleurs thématiques harmonieuses
    COLORS = {
        'primary': discord.Color.from_rgb(88, 101, 242),     # Blurple Discord
        'success': discord.Color.from_rgb(87, 242, 135),     # Vert vif
        'error': discord.Color.from_rgb(237, 66, 69),       # Rouge corail
        'warning': discord.Color.from_rgb(254, 231, 92),     # Jaune soleil
        'info': discord.Color.from_rgb(52, 152, 219),       # Bleu ciel
        'music': discord.Color.from_rgb(155, 89, 182),      # Violet
        'voice': discord.Color.from_rgb(46, 204, 113),      # Émeraude
        'dark': discord.Color.from_rgb(43, 45, 49)          # Sombre élégant
    }
    
    # Emojis principaux
    EMOJIS = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'music': '🎵',
        'voice': '🔊',
        'voice_off': '🔇',
        'voice_switch': '➡️',
        'crown': '👑',
        'shield': '🛡️',
        'gear': '⚙️',
        'star': '⭐',
        'welcome': '🎉',
        'goodbye': '👋'
    }

    @staticmethod
    def build(
        title: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[Union[discord.Color, int, str]] = None,
        author: Optional[Union[discord.Member, discord.User, str]] = None,
        author_icon: Optional[str] = None,
        footer_text: Optional[str] = "RymBot • Bot Discord Professionnel",
        footer_icon: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        image_url: Optional[str] = None,
        fields: Optional[List[Dict[str, Any]]] = None,
        timestamp: bool = True,
        guild: Optional[discord.Guild] = None,
        bot_user: Optional[discord.User] = None
    ) -> discord.Embed:
        """Construit un embed Discord standardisé et hautement stylisé"""
        
        # Résolution de la couleur
        if isinstance(color, str):
            if color.startswith('#'):
                color_hex = int(color.lstrip('#'), 16)
                color_obj = discord.Color(color_hex)
            else:
                color_obj = EmbedFactory.COLORS.get(color, EmbedFactory.COLORS['primary'])
        elif isinstance(color, int):
            color_obj = discord.Color(color)
        elif isinstance(color, discord.Color):
            color_obj = color
        else:
            color_obj = EmbedFactory.COLORS['primary']
            
        embed = discord.Embed(
            title=title,
            description=description,
            color=color_obj
        )
        
        if timestamp:
            embed.timestamp = datetime.now(timezone.utc)
            
        # Configuration de l'auteur
        if author:
            if isinstance(author, (discord.Member, discord.User)):
                author_name = author.display_name
                author_avatar = author.display_avatar.url if hasattr(author, 'display_avatar') else author.avatar.url
                embed.set_author(name=author_name, icon_url=author_icon or author_avatar)
            else:
                embed.set_author(name=str(author), icon_url=author_icon)
                
        # Configuration du Footer et de l'icône de guilde/bot
        footer_icon_final = footer_icon
        if not footer_icon_final and guild and guild.icon:
            footer_icon_final = guild.icon.url
        elif not footer_icon_final and bot_user and bot_user.display_avatar:
            footer_icon_final = bot_user.display_avatar.url
            
        if footer_text:
            embed.set_footer(text=footer_text, icon_url=footer_icon_final)
            
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)
            
        if image_url:
            embed.set_image(url=image_url)
            
        if fields:
            for f in fields:
                embed.add_field(
                    name=f.get('name', '\u200b'),
                    value=f.get('value', '\u200b'),
                    inline=f.get('inline', False)
                )
                
        return embed

    @staticmethod
    def success(title: str, description: str, **kwargs) -> discord.Embed:
        """Embed de succès"""
        full_title = f"{EmbedFactory.EMOJIS['success']} {title}" if not title.startswith('✅') else title
        return EmbedFactory.build(title=full_title, description=description, color='success', **kwargs)

    @staticmethod
    def error(title: str, description: str, **kwargs) -> discord.Embed:
        """Embed d'erreur"""
        full_title = f"{EmbedFactory.EMOJIS['error']} {title}" if not title.startswith('❌') else title
        return EmbedFactory.build(title=full_title, description=description, color='error', **kwargs)

    @staticmethod
    def warning(title: str, description: str, **kwargs) -> discord.Embed:
        """Embed d'avertissement"""
        full_title = f"{EmbedFactory.EMOJIS['warning']} {title}" if not title.startswith('⚠️') else title
        return EmbedFactory.build(title=full_title, description=description, color='warning', **kwargs)

    @staticmethod
    def info(title: str, description: str, **kwargs) -> discord.Embed:
        """Embed d'information"""
        full_title = f"{EmbedFactory.EMOJIS['info']} {title}" if not title.startswith('ℹ️') else title
        return EmbedFactory.build(title=full_title, description=description, color='info', **kwargs)
