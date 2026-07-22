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
from utils.embeds import EmbedFactory
from views.voice_view import VoiceRoomControlView

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True

async def get_prefix(bot, message: discord.Message):
    """Récupère le préfixe dynamique pour le serveur actuel"""
    if not message.guild:
        return commands.when_mentioned_or(".")(bot, message)
    try:
        settings = await bot.db.get_guild_settings(message.guild.id)
        prefix = settings.get("prefix", ".")
    except Exception:
        prefix = "."
    return commands.when_mentioned_or(prefix)(bot, message)

class RymBot(commands.Bot):
    """Bot principal RymBot avec support Hybride (Slash + Préfixe)"""
    
    def __init__(self):
        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            help_command=None
        )
        
        self.db = Database()
        self.config = Config()
        self.permissions = Permissions()
        self.temp_channels = {}  # {channel_id: owner_id}
        
    async def setup_hook(self):
        """Configuration initiale avant la connexion"""
        logger.info("⚡ Initialisation de RymBot...")
        
        # Initialisation de la base de données SQLite
        await self.db.init_db()
        
        # Chargement automatique des cogs
        cogs_dir = Path("cogs")
        if cogs_dir.exists():
            for cog_file in cogs_dir.glob("*.py"):
                if cog_file.name.startswith("__"):
                    continue
                cog_name = f"cogs.{cog_file.stem}"
                try:
                    await self.load_extension(cog_name)
                    logger.info(f"✅ Cog chargé: {cog_name}")
                except Exception as e:
                    logger.error(f"❌ Erreur lors du chargement de {cog_name}: {e}")
        
        # Synchronisation des commandes slash
        try:
            synced = await self.tree.sync()
            logger.info(f"🔮 Synchronisé {len(synced)} commande(s) Slash (Tree).")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la synchronisation du tree: {e}")
        
        logger.info("🚀 RymBot prêt à fonctionner !")

    async def create_default_channels(self):
        """Vérifie et crée le salon 'Join der dark' sur chaque serveur"""
        for guild in self.guilds:
            try:
                existing = discord.utils.get(guild.voice_channels, name="Join der dark")
                if not existing:
                    await guild.create_voice_channel(
                        name="Join der dark",
                        reason="Salon de création de rooms temporaires RymBot"
                    )
                    logger.info(f"✅ Salon 'Join der dark' créé sur {guild.name}")
            except discord.Forbidden:
                logger.warning(f"⚠️ Permissions insuffisantes sur {guild.name} pour créer le salon vocal.")
            except Exception as e:
                logger.error(f"❌ Erreur création salon sur {guild.name}: {e}")

    async def restore_rooms(self):
        """Restaure les rooms temporaires enregistrées en base après redémarrage"""
        try:
            rooms = await self.db.get_all_rooms()
            for room in rooms:
                room_id = room['room_id']
                owner_id = room['owner_id']
                channel = self.get_channel(room_id)
                if channel and isinstance(channel, discord.VoiceChannel):
                    self.temp_channels[room_id] = owner_id
                    logger.info(f"🔑 Room restaurée: {channel.name} (Propriétaire: {owner_id})")
                else:
                    await self.db.remove_room(room_id)
        except Exception as e:
            logger.error(f"❌ Erreur lors de la restauration des rooms: {e}")

    async def on_ready(self):
        """Événement déclenché à la connexion"""
        logger.info(f"✨ Connecté en tant que {self.user} (ID: {self.user.id})")
        logger.info(f"🌐 Connecté à {len(self.guilds)} serveur(s).")
        
        # Statut initial du bot
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name=".help | /help 🎵"
        )
        await self.change_presence(activity=activity)
        
        await self.create_default_channels()
        await self.restore_rooms()

    async def on_voice_state_update(self, member, before, after):
        """Gestion des salons vocaux temporaires"""
        if member.bot:
            return
            
        try:
            # Salon générateur "Join der dark"
            create_room = discord.utils.get(member.guild.voice_channels, name="Join der dark")
            
            if not create_room:
                try:
                    create_room = await member.guild.create_voice_channel(
                        name="Join der dark",
                        reason="Création automatique du salon générateur"
                    )
                except Exception:
                    return
            
            # 1. Le membre rejoint le salon générateur
            if after.channel and after.channel.id == create_room.id:
                await self.create_temp_room(member)
            
            # 2. Le membre quitte une room temporaire
            if before.channel and before.channel.id in self.temp_channels:
                temp_chan = before.channel
                if len(temp_chan.members) == 0:
                    await self.delete_temp_room(temp_chan)
                else:
                    owner_id = self.temp_channels.get(temp_chan.id)
                    if owner_id == member.id:
                        new_owner = temp_chan.members[0]
                        self.temp_channels[temp_chan.id] = new_owner.id
                        await self.db.update_room_owner(temp_chan.id, new_owner.id)
                        
                        embed = EmbedFactory.info(
                            "Nouveau Propriétaire",
                            f"🔑 {new_owner.mention} est désormais le propriétaire de ce salon vocal.",
                            guild=member.guild
                        )
                        try:
                            await temp_chan.send(embed=embed)
                        except Exception:
                            pass
        except Exception as e:
            logger.error(f"Erreur on_voice_state_update bot.py: {e}")

    async def create_temp_room(self, member: discord.Member):
        """Création d'une room temporaire avec panneau d'options interactif"""
        try:
            guild = member.guild
            category = member.voice.channel.category if member.voice else None
            
            room_name = f"🔊 Room de {member.display_name}"
            channel = await guild.create_voice_channel(
                name=room_name,
                category=category,
                reason=f"Room temporaire pour {member.display_name}"
            )
            
            await member.move_to(channel)
            await self.db.add_room(channel.id, member.id)
            self.temp_channels[channel.id] = member.id
            
            # Envoi du panneau de contrôle d'interface
            embed = EmbedFactory.build(
                title=f"🎉 Room de {member.display_name}",
                description=(
                    f"Bienvenue dans votre salon vocal temporaire {member.mention} !\n\n"
                    "Utilisez les boutons ci-dessous ou la commande `.help` / `/help` pour gérer votre salon."
                ),
                color='voice',
                guild=guild,
                author=member
            )
            view = VoiceRoomControlView()
            await channel.send(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la room: {e}")

    async def delete_temp_room(self, channel: discord.VoiceChannel):
        """Suppression propre d'une room temporaire vide"""
        try:
            room_id = channel.id
            await self.db.remove_room(room_id)
            self.temp_channels.pop(room_id, None)
            await channel.delete(reason="Room temporaire vide")
        except Exception as e:
            logger.error(f"Erreur suppression room {channel.id}: {e}")

async def main():
    bot = RymBot()
    token = os.getenv('BOT_TOKEN') or os.getenv('TOKEN')
    
    if not token:
        logger.error("❌ Aucun TOKEN trouvé dans l'environnement / fichier .env !")
        return
        
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Arrêt du bot...")
        await bot.close()
    except Exception as e:
        logger.error(f"Erreur fatale lors de l'exécution: {e}")

if __name__ == "__main__":
    asyncio.run(main())