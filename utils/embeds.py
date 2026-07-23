# utils/embeds.py
import discord
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union

class EmbedFactory:
    """Générateur centralisé d'embeds ultra-modernes et haut de gamme pour RymBot"""

    # Palette de couleurs néon/sombre hautement contrastée et élégante
    COLORS = {
        'primary': discord.Color.from_rgb(99, 102, 241),      # Indigo Néon
        'success': discord.Color.from_rgb(0, 230, 153),      # Émeraude Néon
        'error': discord.Color.from_rgb(255, 64, 96),        # Corail Vif
        'warning': discord.Color.from_rgb(255, 179, 0),      # Ambre Doré
        'info': discord.Color.from_rgb(0, 191, 255),        # Bleu Électrique
        'voice': discord.Color.from_rgb(157, 78, 221),       # Violet Lumineux
        'dark': discord.Color.from_rgb(30, 31, 35)           # Sombre Épuré
    }

    # Emojis stylisés
    EMOJIS = {
        'success': '✨',
        'error': '🚨',
        'warning': '⚠️',
        'info': '💡',
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
        footer_text: Optional[str] = "RymBot • Developped by Naythan",
        footer_icon: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        image_url: Optional[str] = None,
        fields: Optional[List[Dict[str, Any]]] = None,
        timestamp: bool = True,
        guild: Optional[discord.Guild] = None,
        bot_user: Optional[discord.User] = None
    ) -> discord.Embed:
        """Construit un embed Discord ultra-soigné au design moderne"""

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
        """Embed de succès moderne"""
        full_title = f"{EmbedFactory.EMOJIS['success']} {title}" if not any(title.startswith(e) for e in ['✨', '✅']) else title
        return EmbedFactory.build(title=full_title, description=description, color='success', **kwargs)

    @staticmethod
    def error(title: str, description: str, **kwargs) -> discord.Embed:
        """Embed d'erreur moderne"""
        full_title = f"{EmbedFactory.EMOJIS['error']} {title}" if not any(title.startswith(e) for e in ['🚨', '❌']) else title
        return EmbedFactory.build(title=full_title, description=description, color='error', **kwargs)

    @staticmethod
    def warning(title: str, description: str, **kwargs) -> discord.Embed:
        """Embed d'avertissement moderne"""
        full_title = f"{EmbedFactory.EMOJIS['warning']} {title}" if not title.startswith('⚠️') else title
        return EmbedFactory.build(title=full_title, description=description, color='warning', **kwargs)

    @staticmethod
    def info(title: str, description: str, **kwargs) -> discord.Embed:
        """Embed d'information moderne"""
        full_title = f"{EmbedFactory.EMOJIS['info']} {title}" if not any(title.startswith(e) for e in ['💡', 'ℹ️']) else title
        return EmbedFactory.build(title=full_title, description=description, color='info', **kwargs)
