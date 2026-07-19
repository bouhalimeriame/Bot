# bot.py
import os
import logging
import asyncio
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

from database.database import Database
from utils.config import Config
from utils.permissions import Permissions

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
load_dotenv()

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True

class RymBot(commands.Bot):
    """Bot principal de RymBot"""
    
    def __init__(self):
        # PAS DE PRÉFIXE - commandes directes
        super().__init__(
            command_prefix='',  # Préfixe vide pour commandes directes
            intents=intents,
            help_command=None
        )
        
        # Initialisation des composants
        self.db = Database()
        self.config = Config()
        self.permissions = Permissions()
        
        # Variables de session
        self.temp_channels = {}  # {channel_id: owner_id}
        
    async def setup_hook(self):
        """Configuration avant le démarrage du bot"""
        logger.info("Chargement des cogs...")
        
        # Chargement automatique des cogs
        for cog_file in Path("cogs").glob("*.py"):
            cog_name = f"cogs.{cog_file.stem}"
            try:
                await self.load_extension(cog_name)
                logger.info(f"Cog chargé: {cog_name}")
            except Exception as e:
                logger.error(f"Erreur lors du chargement de {cog_name}: {e}")
        
        # Création des tables SQLite
        await self.db.init_db()
        
        # Synchronisation des commandes
        await self.tree.sync()
        
        logger.info("Bot prêt !")
    
    async def create_default_channels(self):
        """Crée les salons par défaut sur tous les serveurs"""
        for guild in self.guilds:
            try:
                # Vérifier si le salon existe déjà
                existing = discord.utils.get(guild.voice_channels, name="Join der dark")
                if not existing:
                    # Créer le salon
                    await guild.create_voice_channel(
                        name="Join der dark",
                        reason="Création automatique du salon de création de rooms"
                    )
                    logger.info(f"✅ Salon 'Join der dark' créé sur {guild.name}")
                else:
                    logger.info(f"✅ Salon 'Join der dark' déjà présent sur {guild.name}")
            except discord.Forbidden:
                logger.error(f"❌ Pas de permission pour créer un salon sur {guild.name}")
            except Exception as e:
                logger.error(f"❌ Erreur lors de la création du salon sur {guild.name}: {e}")
    
    async def on_ready(self):
        """Événement déclenché quand le bot est prêt"""
        logger.info(f"{self.user} est connecté à Discord !")
        logger.info(f"Bot ID: {self.user.id}")
        logger.info(f"Nombre de serveurs: {len(self.guilds)}")
        
        # Créer les salons par défaut
        await self.create_default_channels()
        
        # Restauration des rooms après redémarrage
        await self.restore_rooms()
    
    async def restore_rooms(self):
        """Restauration des rooms après redémarrage"""
        try:
            rooms = await self.db.get_all_rooms()
            for room in rooms:
                room_id = room['room_id']
                owner_id = room['owner_id']
                
                # Vérifier si le salon existe toujours
                channel = self.get_channel(room_id)
                if channel:
                    self.temp_channels[room_id] = owner_id
                    logger.info(f"Room restaurée: {channel.name} (propriétaire: {owner_id})")
                else:
                    # Supprimer l'entrée si le salon n'existe plus
                    await self.db.remove_room(room_id)
                    logger.info(f"Room supprimée de la BDD: {room_id}")
        except Exception as e:
            logger.error(f"Erreur lors de la restauration des rooms: {e}")
    
    async def on_voice_state_update(self, member, before, after):
        """Gestion des événements vocaux"""
        try:
            # Vérifier si le salon "Join der dark" existe
            create_room = discord.utils.get(member.guild.voice_channels, name="Join der dark")
            
            if not create_room:
                # Si le salon n'existe pas, le créer
                try:
                    create_room = await member.guild.create_voice_channel(
                        name="Join der dark",
                        reason="Création automatique du salon de création de rooms"
                    )
                    logger.info(f"Salon 'Join der dark' créé sur {member.guild.name}")
                except Exception as e:
                    logger.error(f"Erreur lors de la création du salon: {e}")
                    return
            
            # Si le membre rejoint le salon de création
            if after.channel and after.channel.id == create_room.id:
                await self.create_temp_room(member)
            
            # Si le membre quitte un salon temporaire
            if before.channel and before.channel.id in self.temp_channels:
                # Vérifier si le salon est vide
                if len(before.channel.members) == 0:
                    await self.delete_temp_room(before.channel)
                else:
                    # Vérifier si le propriétaire a quitté
                    owner_id = self.temp_channels.get(before.channel.id)
                    if owner_id == member.id:
                        # Transférer la propriété au premier membre
                        if before.channel.members:
                            new_owner = before.channel.members[0]
                            self.temp_channels[before.channel.id] = new_owner.id
                            await self.db.update_room_owner(before.channel.id, new_owner.id)
                            await before.channel.send(f"🔑 {new_owner.mention} est maintenant propriétaire de cette room.")
        
        except Exception as e:
            logger.error(f"Erreur dans on_voice_state_update: {e}")
    
    async def create_temp_room(self, member):
        """Création d'une room temporaire"""
        try:
            guild = member.guild
            category = member.voice.channel.category
            
            # Création du salon vocal
            room_name = f"Room de {member.display_name}"
            channel = await guild.create_voice_channel(
                name=room_name,
                category=category,
                reason=f"Création de la room de {member.display_name}"
            )
            
            # Déplacement du membre
            await member.move_to(channel)
            
            # Enregistrement dans la BDD
            await self.db.add_room(channel.id, member.id)
            
            # Stockage en mémoire
            self.temp_channels[channel.id] = member.id
            
            # Message de bienvenue
            await channel.send(f"🎉 Bienvenue {member.mention} !")
            await channel.send("📝 Tapez `help` pour voir la liste des commandes.")
            
            logger.info(f"Room créée: {room_name} par {member.display_name}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la room: {e}")
    
    async def delete_temp_room(self, channel):
        """Suppression d'une room temporaire"""
        try:
            room_id = channel.id
            
            # Suppression de la BDD
            await self.db.remove_room(room_id)
            
            # Suppression de la mémoire
            if room_id in self.temp_channels:
                del self.temp_channels[room_id]
            
            # Suppression du salon
            await channel.delete(reason="Salon vide")
            
            logger.info(f"Room supprimée: {channel.name}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la room: {e}")

# Lancement du bot
async def main():
    bot = RymBot()
    
    try:
        # Récupérer le token (supporte les deux noms de variable)
        token = os.getenv('BOT_TOKEN') or os.getenv('TOKEN')
        
        if not token:
            logger.error("❌ Aucun token trouvé dans le fichier .env !")
            logger.error("Ajoutez BOT_TOKEN=... ou TOKEN=... dans votre fichier .env")
            return
        
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Arrêt du bot...")
        await bot.close()
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")

if __name__ == "__main__":
    asyncio.run(main())