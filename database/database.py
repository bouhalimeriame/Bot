# database/database.py
import aiosqlite
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class Database:
    """Gestion asynchrone de la base de données SQLite avec aiosqlite"""
    
    def __init__(self, db_path: str = "data/bot.db"):
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None
        
        # Création du dossier data si inexistant
        Path("data").mkdir(exist_ok=True)
    
    async def get_connection(self) -> aiosqlite.Connection:
        """Récupère ou initialise la connexion à la BDD"""
        if self._db is None:
            self._db = await aiosqlite.connect(self.db_path)
            self._db.row_factory = aiosqlite.Row
        return self._db

    async def init_db(self):
        """Initialise la base de données et crée les tables"""
        try:
            db = await self.get_connection()
            await self.create_tables(db)
            logger.info("✅ Base de données initialisée avec succès (aiosqlite).")
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation de la BDD: {e}")
            raise
    
    async def create_tables(self, db: aiosqlite.Connection):
        """Crée les tables nécessaires"""
        try:
            # Table des rooms temporaires
            await db.execute('''
                CREATE TABLE IF NOT EXISTS temp_rooms (
                    room_id INTEGER PRIMARY KEY,
                    owner_id INTEGER NOT NULL,
                    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table de configuration par serveur (guild)
            await db.execute('''
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    prefix TEXT DEFAULT '.',
                    welcome_channel_id INTEGER DEFAULT NULL,
                    goodbye_channel_id INTEGER DEFAULT NULL,
                    log_channel_id INTEGER DEFAULT NULL,
                    voice_log_channel_id INTEGER DEFAULT NULL,
                    auto_role_id INTEGER DEFAULT NULL,
                    welcome_message TEXT DEFAULT 'Bienvenue {member} sur **{guild}** ! 🎉',
                    goodbye_message TEXT DEFAULT 'Au revoir {member}, merci d''avoir fait partie de **{guild}** ! 👋',
                    main_color TEXT DEFAULT '#5865F2'
                )
            ''')
            
            await db.commit()
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création des tables: {e}")
            raise

    # ------------------- GESTION DES ROOMS TEMPORAIRES ------------------- #
    
    async def add_room(self, room_id: int, owner_id: int) -> bool:
        """Ajoute une room temporaire"""
        try:
            db = await self.get_connection()
            await db.execute(
                "INSERT OR REPLACE INTO temp_rooms (room_id, owner_id) VALUES (?, ?)",
                (room_id, owner_id)
            )
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de la room: {e}")
            return False
    
    async def remove_room(self, room_id: int) -> bool:
        """Supprime une room temporaire"""
        try:
            db = await self.get_connection()
            cursor = await db.execute("DELETE FROM temp_rooms WHERE room_id = ?", (room_id,))
            await db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la room: {e}")
            return False
    
    async def update_room_owner(self, room_id: int, new_owner_id: int) -> bool:
        """Met à jour le propriétaire d'une room"""
        try:
            db = await self.get_connection()
            cursor = await db.execute(
                "UPDATE temp_rooms SET owner_id = ? WHERE room_id = ?",
                (new_owner_id, room_id)
            )
            await db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du propriétaire: {e}")
            return False
    
    async def get_room_owner(self, room_id: int) -> Optional[int]:
        """Récupère l'ID du propriétaire d'une room"""
        try:
            db = await self.get_connection()
            async with db.execute("SELECT owner_id FROM temp_rooms WHERE room_id = ?", (room_id,)) as cursor:
                row = await cursor.fetchone()
                return row["owner_id"] if row else None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du propriétaire: {e}")
            return None
    
    async def get_all_rooms(self) -> List[Dict[str, Any]]:
        """Récupère toutes les rooms temporaires"""
        try:
            db = await self.get_connection()
            async with db.execute("SELECT room_id, owner_id, creation_date FROM temp_rooms") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des rooms: {e}")
            return []

    # ------------------- GESTION DES PARAMÈTRES PAR GUILD ------------------- #
    
    async def get_guild_settings(self, guild_id: int) -> Dict[str, Any]:
        """Récupère les paramètres d'un serveur ou les initialise s'ils n'existent pas"""
        default_settings = {
            "guild_id": guild_id,
            "prefix": ".",
            "welcome_channel_id": None,
            "goodbye_channel_id": None,
            "log_channel_id": None,
            "voice_log_channel_id": None,
            "auto_role_id": None,
            "welcome_message": "Bienvenue {member} sur **{guild}** ! 🎉",
            "goodbye_message": "Au revoir {member}, merci d'avoir fait partie de **{guild}** ! 👋",
            "main_color": "#5865F2"
        }
        try:
            db = await self.get_connection()
            async with db.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                
                # Inscription de la guild avec les valeurs par défaut
                await db.execute(
                    "INSERT INTO guild_settings (guild_id) VALUES (?)",
                    (guild_id,)
                )
                await db.commit()
                return default_settings
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des paramètres guild {guild_id}: {e}")
            return default_settings

    async def update_guild_setting(self, guild_id: int, key: str, value: Any) -> bool:
        """Met à jour un paramètre spécifique pour un serveur"""
        allowed_keys = {
            "prefix", "welcome_channel_id", "goodbye_channel_id",
            "log_channel_id", "voice_log_channel_id", "auto_role_id",
            "welcome_message", "goodbye_message", "main_color"
        }
        if key not in allowed_keys:
            logger.error(f"Clef de paramètre non autorisée: {key}")
            return False
            
        try:
            db = await self.get_connection()
            # S'assurer que la ligne existe
            await self.get_guild_settings(guild_id)
            
            query = f"UPDATE guild_settings SET {key} = ? WHERE guild_id = ?"
            await db.execute(query, (value, guild_id))
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du paramètre {key} pour {guild_id}: {e}")
            return False

    async def close(self):
        """Ferme proprement la connexion SQLite"""
        if self._db:
            await self._db.close()
            self._db = None
            logger.info("Connexion SQLite fermée.")