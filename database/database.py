# database/database.py
import sqlite3
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class Database:
    """Gestion de la base de données SQLite"""
    
    def __init__(self, db_path: str = "data/bot.db"):
        self.db_path = db_path
        self.connection = None
        
        # Création du dossier data si inexistant
        Path("data").mkdir(exist_ok=True)
    
    async def init_db(self):
        """Initialise la base de données"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            
            # Création des tables
            await self.create_tables()
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la BDD: {e}")
            raise
    
    async def create_tables(self):
        """Crée les tables nécessaires"""
        try:
            cursor = self.connection.cursor()
            
            # Table des rooms temporaires
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS temp_rooms (
                    room_id INTEGER PRIMARY KEY,
                    owner_id INTEGER NOT NULL,
                    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table des utilisateurs (pour le futur)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.connection.commit()
            logger.info("Base de données initialisée avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création des tables: {e}")
            raise
    
    async def add_room(self, room_id: int, owner_id: int) -> bool:
        """Ajoute une room temporaire dans la BDD"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO temp_rooms (room_id, owner_id) VALUES (?, ?)",
                (room_id, owner_id)
            )
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de la room: {e}")
            return False
    
    async def remove_room(self, room_id: int) -> bool:
        """Supprime une room temporaire de la BDD"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "DELETE FROM temp_rooms WHERE room_id = ?",
                (room_id,)
            )
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la room: {e}")
            return False
    
    async def update_room_owner(self, room_id: int, new_owner_id: int) -> bool:
        """Met à jour le propriétaire d'une room"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "UPDATE temp_rooms SET owner_id = ? WHERE room_id = ?",
                (new_owner_id, room_id)
            )
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du propriétaire: {e}")
            return False
    
    async def get_room_owner(self, room_id: int) -> Optional[int]:
        """Récupère le propriétaire d'une room"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT owner_id FROM temp_rooms WHERE room_id = ?",
                (room_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du propriétaire: {e}")
            return None
    
    async def get_all_rooms(self) -> List[Dict[str, Any]]:
        """Récupère toutes les rooms temporaires"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM temp_rooms")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des rooms: {e}")
            return []
    
    async def room_exists(self, room_id: int) -> bool:
        """Vérifie si une room existe dans la BDD"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT 1 FROM temp_rooms WHERE room_id = ?",
                (room_id,)
            )
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de la room: {e}")
            return False
    
    async def close(self):
        """Ferme la connexion à la base de données"""
        if self.connection:
            self.connection.close()
            logger.info("Connexion à la BDD fermée")
    
    def __del__(self):
        """Destructeur pour fermer la connexion"""
        if hasattr(self, 'connection') and self.connection:
            try:
                self.connection.close()
            except:
                pass