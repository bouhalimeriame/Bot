# utils/config.py
import os
from typing import Optional

class Config:
    """Configuration globale du bot"""
    
    DEFAULT_PREFIX = os.getenv('BOT_PREFIX', '.')
    
    # Couleurs hexadécimales pour les embeds
    COLORS = {
        'success': 0x57F287,
        'error': 0xED4245,
        'warning': 0xFEE75C,
        'info': 0x3498DB,
        'primary': 0x5865F2,
        'music': 0x9B59B6,
        'voice': 0x2ECC71,
        'dark': 0x2B2D31
    }
    
    # Emojis du système
    EMOJIS = {
        'create_room': '➕',
        'lock': '🔒',
        'unlock': '🔓',
        'private': '🔐',
        'public': '🌍',
        'rename': '✏️',
        'claim': '🔑',
        'kick': '👢',
        'ban': '🚫',
        'transfer': '↗️',
        'hide': '👻',
        'show': '👀',
        'bitrate': '📊',
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'music_play': '▶️',
        'music_pause': '⏸️',
        'music_stop': '⏹️',
        'music_skip': '⏭️',
        'music_loop': '🔁',
        'music_queue': '📋',
        'voice_join': '🔊',
        'voice_leave': '🔇',
        'voice_switch': '➡️'
    }
    
    # Messages d'erreur pré-formatés
    ERRORS = {
        'not_owner': "Vous n'êtes pas le propriétaire de cette room.",
        'not_in_voice': "Vous devez être connecté à un salon vocal.",
        'not_temp_channel': "Ce salon n'est pas une room temporaire.",
        'no_permission': "Vous n'avez pas les permissions nécessaires pour exécuter cette commande.",
        'invalid_limit': "La limite d'utilisateurs doit être comprise entre 1 et 99.",
        'invalid_bitrate': "Valeur de bitrate invalide. Choisissez parmi: 64, 96, 128 kbps."
    }

    @staticmethod
    def get_color(color_name: str = 'primary') -> int:
        return Config.COLORS.get(color_name, Config.COLORS['primary'])
    
    @staticmethod
    def get_emoji(emoji_name: str) -> str:
        return Config.EMOJIS.get(emoji_name, '')
    
    @staticmethod
    def get_error(error_name: str) -> str:
        return Config.ERRORS.get(error_name, "Une erreur inattendue est survenue.")