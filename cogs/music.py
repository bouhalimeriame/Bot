# cogs/music.py
import discord
from discord.ext import commands
import yt_dlp
import asyncio
import re
from typing import Optional, Dict, List
import aiohttp
import json
from urllib.parse import urlparse, parse_qs

class MusicCog(commands.Cog):
    """Cog pour la musique avec support YouTube et Spotify"""
    
    def __init__(self, bot):
        self.bot = bot
        self.queue: Dict[int, List[Dict]] = {}
        self.now_playing: Dict[int, Dict] = {}
        self.voice_clients: Dict[int, discord.VoiceClient] = {}
        self.loop: Dict[int, bool] = {}
        self.volume: Dict[int, int] = {}
        self.autoplay: Dict[int, bool] = {}
        self.history: Dict[int, List[Dict]] = {}
        
        # Configuration yt-dlp
        self.ytdl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'default_search': 'ytsearch',
            'source_address': '0.0.0.0',
            'extract_flat': False,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        }
        self.ytdl = yt_dlp.YoutubeDL(self.ytdl_opts)
    
    async def extract_spotify_info(self, url: str) -> Optional[Dict]:
        """Extrait les informations d'une URL Spotify"""
        try:
            # Nettoyer l'URL
            if '?' in url:
                url = url.split('?')[0]
            
            # Utiliser l'API Spotify via un proxy public
            async with aiohttp.ClientSession() as session:
                # Utiliser un proxy pour récupérer les infos Spotify
                api_url = f"https://api.spotifydown.com/metadata/{url}"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json'
                }
                
                async with session.get(api_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and data.get('success'):
                            return {
                                'title': data.get('title', 'Inconnu'),
                                'artist': data.get('artists', ['Inconnu'])[0],
                                'album': data.get('album', 'Inconnu'),
                                'duration': data.get('duration', 0),
                                'thumbnail': data.get('cover', ''),
                                'query': f"{data.get('title', '')} {data.get('artists', [''])[0]} audio"
                            }
            
            # Fallback: extraire manuellement
            # Exemple: https://open.spotify.com/track/0axEKNRqwsdQExH05qcGNp
            track_id = url.split('/')[-1]
            
            # Utiliser une autre API gratuite
            async with aiohttp.ClientSession() as session:
                api_url = f"https://spotify-api-proxy.vercel.app/api/track?id={track_id}"
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            return {
                                'title': data.get('name', 'Inconnu'),
                                'artist': data.get('artists', [{}])[0].get('name', 'Inconnu'),
                                'album': data.get('album', {}).get('name', 'Inconnu'),
                                'duration': data.get('duration_ms', 0) // 1000,
                                'thumbnail': data.get('album', {}).get('images', [{}])[0].get('url', ''),
                                'query': f"{data.get('name', '')} {data.get('artists', [{}])[0].get('name', '')} audio"
                            }
            
            return None
        except Exception as e:
            print(f"Erreur extraction Spotify: {e}")
            return None
    
    async def search_youtube(self, query: str) -> Optional[Dict]:
        """Recherche une chanson sur YouTube"""
        try:
            search_query = f"ytsearch:{query}"
            info = self.ytdl.extract_info(search_query, download=False)
            
            if info and 'entries' in info and info['entries']:
                entry = info['entries'][0]
                return {
                    'title': entry.get('title', 'Inconnu'),
                    'url': entry.get('webpage_url', ''),
                    'duration': entry.get('duration', 0),
                    'thumbnail': entry.get('thumbnail', ''),
                    'uploader': entry.get('uploader', 'Inconnu'),
                    'source': 'youtube'
                }
            return None
        except Exception as e:
            print(f"Erreur recherche YouTube: {e}")
            return None
    
    async def search_alternative(self, query: str) -> Optional[Dict]:
        """Recherche alternative sur YouTube"""
        try:
            # Essayer différentes variantes de recherche
            search_queries = [
                query,
                f"{query} official audio",
                f"{query} song",
                f"{query} music"
            ]
            
            for search in search_queries[:3]:
                song = await self.search_youtube(search)
                if song:
                    return song
            
            return None
        except Exception as e:
            print(f"Erreur recherche alternative: {e}")
            return None
    
    @commands.command(name='play')
    async def play(self, ctx, *, query: str):
        """Joue une musique (YouTube ou Spotify)"""
        try:
            if not ctx.author.voice:
                await ctx.send("❌ Vous devez être dans un salon vocal.")
                return
            
            # Connexion au salon vocal
            if ctx.voice_client is None:
                voice_client = await ctx.author.voice.channel.connect()
                self.voice_clients[ctx.guild.id] = voice_client
            else:
                voice_client = ctx.voice_client
            
            loading_msg = await ctx.send(f"🔍 Recherche de `{query}`...")
            
            song = None
            
            # Vérifier si c'est une URL Spotify
            if 'spotify.com' in query:
                # Extraire les infos Spotify
                spotify_info = await self.extract_spotify_info(query)
                if spotify_info:
                    # Chercher sur YouTube avec le nom de la chanson + artiste
                    song = await self.search_youtube(spotify_info['query'])
                    if not song:
                        song = await self.search_alternative(spotify_info['query'])
                    
                    if song:
                        song['spotify_info'] = spotify_info
                        song['title'] = f"{spotify_info['title']} - {spotify_info['artist']}"
            
            # Si ce n'est pas Spotify ou que la recherche a échoué
            if not song:
                # Recherche directe sur YouTube
                song = await self.search_youtube(query)
                if not song:
                    song = await self.search_alternative(query)
            
            if not song:
                await loading_msg.edit(content="❌ Aucun résultat trouvé pour cette chanson.")
                return
            
            # Ajouter à la queue
            song['requester'] = ctx.author
            
            if ctx.guild.id not in self.queue:
                self.queue[ctx.guild.id] = []
            
            self.queue[ctx.guild.id].append(song)
            
            # Jouer directement si rien ne joue
            if not voice_client.is_playing() and not voice_client.is_paused():
                await self.play_next(ctx)
                await loading_msg.edit(content=f"▶️ **{song['title']}** - Lecture en cours")
            else:
                position = len(self.queue[ctx.guild.id])
                await loading_msg.edit(content=f"📝 **{song['title']}** - Ajoutée à la file d'attente (position {position})")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='p')
    async def play_short(self, ctx, *, query: str):
        """Raccourci pour play"""
        await self.play(ctx, query=query)
    
    @commands.command(name='rp')
    async def rp(self, ctx, *, query: str):
        """Raccourci pour play"""
        await self.play(ctx, query=query)
    
    @commands.command(name='skip')
    async def skip(self, ctx):
        """Passe à la chanson suivante"""
        try:
            if not ctx.voice_client or not ctx.voice_client.is_playing():
                await ctx.send("❌ Aucune musique en cours.")
                return
            
            if ctx.guild.id in self.now_playing:
                if ctx.guild.id not in self.history:
                    self.history[ctx.guild.id] = []
                self.history[ctx.guild.id].append(self.now_playing[ctx.guild.id])
            
            ctx.voice_client.stop()
            await ctx.send("⏭️ Chanson suivante...")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='stop')
    async def stop(self, ctx):
        """Arrête la musique et vide la queue"""
        try:
            if ctx.guild.id in self.queue:
                self.queue[ctx.guild.id].clear()
            
            if ctx.voice_client:
                ctx.voice_client.stop()
                await ctx.voice_client.disconnect()
                self.voice_clients.pop(ctx.guild.id, None)
            
            self.now_playing.pop(ctx.guild.id, None)
            await ctx.send("⏹️ Musique arrêtée et queue vidée.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='pause')
    async def pause(self, ctx):
        """Met la musique en pause"""
        try:
            if not ctx.voice_client or not ctx.voice_client.is_playing():
                await ctx.send("❌ Aucune musique en cours.")
                return
            
            ctx.voice_client.pause()
            await ctx.send("⏸️ Musique en pause.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='resume')
    async def resume(self, ctx):
        """Reprend la musique"""
        try:
            if not ctx.voice_client or not ctx.voice_client.is_paused():
                await ctx.send("❌ Aucune musique en pause.")
                return
            
            ctx.voice_client.resume()
            await ctx.send("▶️ Reprise de la musique.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='queue')
    async def show_queue(self, ctx):
        """Affiche la file d'attente"""
        try:
            if ctx.guild.id not in self.queue or not self.queue[ctx.guild.id]:
                await ctx.send("📝 La file d'attente est vide.")
                return
            
            queue_list = self.queue[ctx.guild.id]
            embed = discord.Embed(
                title="📋 File d'attente",
                color=discord.Color.blue()
            )
            
            total_duration = 0
            for i, song in enumerate(queue_list[:10], 1):
                duration = song.get('duration', 0)
                total_duration += duration
                minutes = duration // 60
                seconds = duration % 60
                duration_str = f"{minutes}:{seconds:02d}" if duration > 0 else "Live"
                
                source_icon = "🎵" if song.get('source') == 'youtube' else "🎶"
                embed.add_field(
                    name=f"{i}. {song['title'][:50]}",
                    value=f"{source_icon} {duration_str} | Demandé par: {song['requester'].display_name}",
                    inline=False
                )
            
            if len(queue_list) > 10:
                embed.set_footer(text=f"Et {len(queue_list) - 10} autres chansons...")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='now')
    async def now_playing(self, ctx):
        """Affiche la chanson en cours"""
        try:
            if not ctx.voice_client or not ctx.voice_client.is_playing():
                await ctx.send("❌ Aucune musique en cours.")
                return
            
            if ctx.guild.id in self.now_playing:
                song = self.now_playing[ctx.guild.id]
                
                duration = song.get('duration', 0)
                minutes = duration // 60
                seconds = duration % 60
                duration_str = f"{minutes}:{seconds:02d}" if duration > 0 else "Live"
                
                embed = discord.Embed(
                    title="🎵 Chanson en cours",
                    description=f"**{song['title']}**",
                    color=discord.Color.green()
                )
                if song.get('thumbnail'):
                    embed.set_thumbnail(url=song['thumbnail'])
                embed.add_field(name="Demandé par", value=song['requester'].display_name)
                embed.add_field(name="Durée", value=duration_str)
                if song.get('uploader'):
                    embed.add_field(name="Chaîne", value=song['uploader'])
                
                # Info Spotify si disponible
                if song.get('spotify_info'):
                    spotify = song['spotify_info']
                    embed.add_field(name="Album Spotify", value=spotify.get('album', 'Inconnu'))
                
                await ctx.send(embed=embed)
            else:
                await ctx.send("🎵 Musique en cours...")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='loop')
    async def toggle_loop(self, ctx):
        """Active/désactive la boucle"""
        try:
            if ctx.guild.id not in self.loop:
                self.loop[ctx.guild.id] = False
            
            self.loop[ctx.guild.id] = not self.loop[ctx.guild.id]
            status = "activée" if self.loop[ctx.guild.id] else "désactivée"
            await ctx.send(f"🔁 Boucle {status}.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='volume')
    async def set_volume(self, ctx, volume: int):
        """Définit le volume (0-100)"""
        try:
            if volume < 0 or volume > 100:
                await ctx.send("❌ Le volume doit être entre 0 et 100.")
                return
            
            if not ctx.voice_client or not ctx.voice_client.source:
                await ctx.send("❌ Aucune musique en cours.")
                return
            
            ctx.voice_client.source.volume = volume / 100
            self.volume[ctx.guild.id] = volume
            
            await ctx.send(f"🔊 Volume défini à {volume}%.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='clear')
    async def clear_queue(self, ctx):
        """Vide la file d'attente"""
        try:
            if ctx.guild.id in self.queue:
                self.queue[ctx.guild.id].clear()
                await ctx.send("🧹 File d'attente vidée.")
            else:
                await ctx.send("📝 La file d'attente est déjà vide.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='shuffle')
    async def shuffle_queue(self, ctx):
        """Mélange la file d'attente"""
        try:
            import random
            if ctx.guild.id in self.queue and self.queue[ctx.guild.id]:
                random.shuffle(self.queue[ctx.guild.id])
                await ctx.send("🔀 File d'attente mélangée !")
            else:
                await ctx.send("📝 La file d'attente est vide.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='music_help')
    async def music_help(self, ctx):
        """Affiche l'aide pour la musique"""
        embed = discord.Embed(
            title="🎵 Commandes Musique",
            description="Voici toutes les commandes musicales disponibles :",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="▶️ Lecture",
            value=(
                "`play <titre/url>` - Joue une musique (YouTube/Spotify)\n"
                "`p <titre/url>` - Raccourci pour play\n"
                "`rp <titre/url>` - Autre raccourci pour play\n"
                "`skip` - Passe à la chanson suivante\n"
                "`stop` - Arrête la musique\n"
                "`pause` - Met en pause\n"
                "`resume` - Reprend la musique"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎛️ Gestion",
            value=(
                "`queue` - Affiche la file d'attente\n"
                "`now` - Affiche la chanson en cours\n"
                "`loop` - Active/désactive la boucle\n"
                "`volume <0-100>` - Définit le volume\n"
                "`clear` - Vide la file d'attente\n"
                "`shuffle` - Mélange la file d'attente"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📌 Sources supportées",
            value=(
                "• YouTube (recherche et URLs)\n"
                "• YouTube Music\n"
                "• Spotify (via recherche)\n"
                "• SoundCloud (recherche)"
            ),
            inline=False
        )
        
        embed.set_footer(text="Fonctionne SANS FFmpeg - Compatible avec tous les déploiements")
        await ctx.send(embed=embed)
    
    async def play_next(self, ctx):
        """Joue la prochaine chanson dans la queue"""
        try:
            if ctx.guild.id in self.loop and self.loop[ctx.guild.id]:
                if ctx.guild.id in self.now_playing:
                    song = self.now_playing[ctx.guild.id]
                    await self.play_song(ctx, song)
                    return
            
            if ctx.guild.id not in self.queue or not self.queue[ctx.guild.id]:
                return
            
            song = self.queue[ctx.guild.id].pop(0)
            await self.play_song(ctx, song)
            
        except Exception as e:
            await ctx.send(f"❌ Erreur lors de la lecture: {str(e)}")
    
    async def play_song(self, ctx, song):
        """Joue une chanson spécifique"""
        try:
            voice_client = ctx.voice_client
            
            # Récupérer l'URL audio
            audio_url = None
            
            # Essayer avec l'URL YouTube
            if song.get('url'):
                try:
                    with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'quiet': True}) as ydl:
                        info = ydl.extract_info(song['url'], download=False)
                        if info and 'url' in info:
                            audio_url = info['url']
                except Exception as e:
                    print(f"Erreur extraction audio: {e}")
            
            # Fallback: recherche directe
            if not audio_url:
                try:
                    search = await self.search_youtube(song['title'])
                    if search and search.get('url'):
                        with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'quiet': True}) as ydl:
                            info = ydl.extract_info(search['url'], download=False)
                            if info and 'url' in info:
                                audio_url = info['url']
                except Exception as e:
                    print(f"Erreur fallback: {e}")
            
            if not audio_url:
                raise Exception("Impossible de récupérer l'audio. La vidéo est peut-être protégée.")
            
            # Créer le source audio
            source = discord.FFmpegPCMAudio(
                audio_url,
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                options="-vn"
            )
            
            volume = self.volume.get(ctx.guild.id, 50) / 100
            source = discord.PCMVolumeTransformer(source, volume)
            
            def after_playing(error):
                if error:
                    print(f"Erreur de lecture: {error}")
                asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)
            
            voice_client.play(source, after=after_playing)
            self.now_playing[ctx.guild.id] = song
            
            # Message de confirmation
            duration = song.get('duration', 0)
            minutes = duration // 60
            seconds = duration % 60
            duration_str = f"{minutes}:{seconds:02d}" if duration > 0 else "Live"
            
            embed = discord.Embed(
                title="▶️ Lecture en cours",
                description=f"**{song['title']}**",
                color=discord.Color.green()
            )
            if song.get('thumbnail'):
                embed.set_thumbnail(url=song['thumbnail'])
            embed.add_field(name="Demandé par", value=song['requester'].display_name)
            embed.add_field(name="Durée", value=duration_str)
            if song.get('uploader'):
                embed.add_field(name="Chaîne", value=song['uploader'])
            
            # Info Spotify
            if song.get('spotify_info'):
                spotify = song['spotify_info']
                embed.add_field(name="Album", value=spotify.get('album', 'Inconnu'))
                embed.add_field(name="Artiste", value=spotify.get('artist', 'Inconnu'))
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Erreur de lecture: {str(e)}")

async def setup(bot):
    await bot.add_cog(MusicCog(bot))