# utils/config.py
import os
from typing import Optional

class Config:
    """Configuration du bot"""
    
    # Préfixe du bot (peut être modifié dans .env)
    PREFIX = os.getenv('BOT_PREFIX', '!')
    
    # Couleurs pour les embeds
    COLORS = {
        'success': 0x00ff00,
        'error': 0xff0000,
        'warning': 0xffa500,
        'info': 0x3498db,
        'default': 0x7289da
    }
    
    # Emojis
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
        'warning': '⚠️'
    }
    
    # Messages d'erreur
    ERRORS = {
        'not_owner': "❌ Vous n'êtes pas propriétaire de cette room.",
        'not_in_voice': "❌ Vous devez être dans un salon vocal.",
        'not_temp_channel': "❌ Ce salon n'est pas une room temporaire.",
        'no_permission': "❌ Vous n'avez pas la permission d'utiliser cette commande.",
        'invalid_limit': "❌ La limite doit être comprise entre 1 et 99.",
        'invalid_bitrate': "❌ Valeur invalide. Choisissez parmi: 64, 96, 128"
    }
    
    # Messages de succès
    SUCCESS = {
        'limit_set': "✅ Limite définie à {limit} utilisateurs.",
        'room_locked': "🔒 Room verrouillée.",
        'room_unlocked': "🔓 Room déverrouillée.",
        'room_private': "🔐 Room rendue privée.",
        'room_public': "🌍 Room rendue publique.",
        'room_renamed': "✅ Room renommée en: {name}",
        'room_claimed': "🔑 Vous êtes maintenant propriétaire de cette room.",
        'user_kicked': "👢 {user} a été expulsé de la room.",
        'user_banned': "🚫 {user} a été banni de la room.",
        'ownership_transferred': "🔑 La propriété a été transférée à {user}.",
        'room_hidden': "👻 Room cachée.",
        'room_shown': "👀 Room visible.",
        'bitrate_set': "✅ Débit binaire défini à {bitrate} kbps."
    }
    
    @staticmethod
    def get_prefix():
        """Retourne le préfixe configuré"""
        return Config.PREFIX
    
    @staticmethod
    def get_color(color_name: str = 'default') -> int:
        """Retourne une couleur par son nom"""
        return Config.COLORS.get(color_name, Config.COLORS['default'])
    
    @staticmethod
    def get_emoji(emoji_name: str) -> str:
        """Retourne un emoji par son nom"""
        return Config.EMOJIS.get(emoji_name, '')
    
    @staticmethod
    def get_error(error_name: str) -> str:
        """Retourne un message d'erreur par son nom"""
        return Config.ERRORS.get(error_name, "❌ Une erreur est survenue.")
    
    @staticmethod
    def get_success(success_name: str, **kwargs) -> str:
        """Retourne un message de succès formaté"""
        message = Config.SUCCESS.get(success_name, "✅ Opération réussie.")
        return message.format(**kwargs)