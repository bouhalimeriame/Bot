# cogs/music.py
import discord
from discord.ext import commands
import yt_dlp
import asyncio
from typing import Optional, Dict, List
import aiohttp

from utils.embeds import EmbedFactory
from views.music_view import MusicControlView

class MusicCog(commands.Cog, name="Musique"):
    """Cog complet pour le système de musique (YouTube & Spotify)"""
    
    def __init__(self, bot):
        self.bot = bot
        self.queue: Dict[int, List[Dict]] = {}
        self.now_playing: Dict[int, Dict] = {}
        self.voice_clients: Dict[int, discord.VoiceClient] = {}
        self.loop: Dict[int, bool] = {}
        self.volume: Dict[int, int] = {}
        
        self.ytdl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'default_search': 'ytsearch',
            'source_address': '0.0.0.0',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        }
        self.ytdl = yt_dlp.YoutubeDL(self.ytdl_opts)

    async def search_youtube(self, query: str) -> Optional[Dict]:
        """Recherche une vidéo ou lien sur YouTube"""
        try:
            loop = asyncio.get_event_loop()
            search_query = query if query.startswith('http') else f"ytsearch:{query}"
            
            data = await loop.run_in_executor(
                None, lambda: self.ytdl.extract_info(search_query, download=False)
            )
            
            if not data:
                return None
                
            if 'entries' in data:
                if not data['entries']:
                    return None
                entry = data['entries'][0]
            else:
                entry = data
                
            return {
                'title': entry.get('title', 'Inconnu'),
                'url': entry.get('webpage_url', ''),
                'audio_url': entry.get('url', ''),
                'duration': entry.get('duration', 0),
                'thumbnail': entry.get('thumbnail', ''),
                'uploader': entry.get('uploader', 'Artiste Inconnu'),
                'source': 'youtube'
            }
        except Exception as e:
            print(f"Erreur recherche YouTube: {e}")
            return None

    async def extract_spotify_info(self, url: str) -> Optional[Dict]:
        """Extrait les informations d'un lien Spotify"""
        try:
            clean_url = url.split('?')[0]
            async with aiohttp.ClientSession() as session:
                api_url = f"https://api.spotifydown.com/metadata/{clean_url}"
                headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
                async with session.get(api_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and data.get('success'):
                            title = data.get('title', '')
                            artist = data.get('artists', [''])[0]
                            return {
                                'title': f"{title} - {artist}",
                                'query': f"{title} {artist} audio",
                                'thumbnail': data.get('cover', ''),
                                'artist': artist,
                                'album': data.get('album', '')
                            }
            return None
        except Exception as e:
            print(f"Erreur extraction Spotify: {e}")
            return None

    async def ensure_voice(self, ctx: commands.Context) -> Optional[discord.VoiceClient]:
        """S'assure que l'utilisateur et le bot sont dans un salon vocal"""
        if not ctx.author.voice or not ctx.author.voice.channel:
            embed = EmbedFactory.error("Erreur Vocal", "❌ Vous devez être connecté à un salon vocal.", guild=ctx.guild)
            await ctx.send(embed=embed)
            return None
            
        target_channel = ctx.author.voice.channel
        
        if ctx.voice_client is None:
            vc = await target_channel.connect()
            self.voice_clients[ctx.guild.id] = vc
            return vc
        else:
            if ctx.voice_client.channel != target_channel:
                await ctx.voice_client.move_to(target_channel)
            return ctx.voice_client

    @commands.hybrid_command(name='join', description="Rejoint votre salon vocal")
    async def join_cmd(self, ctx: commands.Context):
        """Rejoint le salon vocal de l'utilisateur"""
        vc = await self.ensure_voice(ctx)
        if vc:
            embed = EmbedFactory.success("Salon Vocal", f"🔊 Rejoint **{vc.channel.name}** !", guild=ctx.guild)
            await ctx.send(embed=embed)

    @commands.hybrid_command(name='leave', description="Quitte le salon vocal")
    async def leave_cmd(self, ctx: commands.Context):
        """Quitte le salon vocal"""
        if ctx.voice_client:
            channel_name = ctx.voice_client.channel.name
            await ctx.voice_client.disconnect()
            self.voice_clients.pop(ctx.guild.id, None)
            self.queue.pop(ctx.guild.id, None)
            self.now_playing.pop(ctx.guild.id, None)
            embed = EmbedFactory.info("Déconnexion", f"🔇 Déconnecté du salon **{channel_name}**.", guild=ctx.guild)
            await ctx.send(embed=embed)
        else:
            embed = EmbedFactory.error("Erreur", "❌ Le bot n'est connecté à aucun salon vocal.", guild=ctx.guild)
            await ctx.send(embed=embed)

    @commands.hybrid_command(name='play', description="Recherche et joue une musique (YouTube ou Spotify)")
    async def play(self, ctx: commands.Context, *, query: str):
        """Recherche et ajoute une musique à la file"""
        vc = await self.ensure_voice(ctx)
        if not vc:
            return

        embed_searching = EmbedFactory.info("Recherche", f"🔍 Recherche de `{query}` en cours...", guild=ctx.guild)
        loading_msg = await ctx.send(embed=embed_searching)

        song = None
        if 'spotify.com' in query:
            spotify_info = await self.extract_spotify_info(query)
            if spotify_info:
                song = await self.search_youtube(spotify_info['query'])
                if song:
                    song['spotify_info'] = spotify_info
                    song['title'] = spotify_info['title']

        if not song:
            song = await self.search_youtube(query)

        if not song:
            embed_err = EmbedFactory.error("Aucun résultat", "❌ Aucun morceau correspondant n'a été trouvé.", guild=ctx.guild)
            if isinstance(loading_msg, discord.Message):
                return await loading_msg.edit(embed=embed_err)
            else:
                return await ctx.send(embed=embed_err)

        song['requester'] = ctx.author

        if ctx.guild.id not in self.queue:
            self.queue[ctx.guild.id] = []
            
        self.queue[ctx.guild.id].append(song)
        
        position = len(self.queue[ctx.guild.id])

        if not vc.is_playing() and not vc.is_paused():
            await self.play_next(ctx)
            embed_start = EmbedFactory.success("Musique", f"▶️ **{song['title']}** démarre !", guild=ctx.guild)
            if isinstance(loading_msg, discord.Message):
                await loading_msg.edit(embed=embed_start)
        else:
            mins, secs = divmod(song.get('duration', 0), 60)
            dur_str = f"{mins}:{secs:02d}" if song.get('duration', 0) > 0 else "Live"
            
            embed_added = EmbedFactory.build(
                title="📝 Ajoutée à la file d'attente",
                description=f"**[{song['title']}]({song['url']})**",
                color='music',
                thumbnail_url=song.get('thumbnail'),
                fields=[
                    {'name': "Position", 'value': f"`#{position}`", 'inline': True},
                    {'name': "Durée", 'value': f"`{dur_str}`", 'inline': True},
                    {'name': "Demandé par", 'value': ctx.author.mention, 'inline': True}
                ],
                guild=ctx.guild,
                author=ctx.author
            )
            if isinstance(loading_msg, discord.Message):
                await loading_msg.edit(embed=embed_added)

    @commands.hybrid_command(name='pause', description="Met en pause la musique")
    async def pause(self, ctx: commands.Context):
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            embed = EmbedFactory.error("Erreur", "❌ Aucune musique en cours d'exécution.", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        ctx.voice_client.pause()
        embed = EmbedFactory.info("Pause", "⏸️ La musique a été mise en pause.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='resume', description="Reprend la lecture en pause")
    async def resume(self, ctx: commands.Context):
        if not ctx.voice_client or not ctx.voice_client.is_paused():
            embed = EmbedFactory.error("Erreur", "❌ Aucune musique en pause.", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        ctx.voice_client.resume()
        embed = EmbedFactory.success("Reprise", "▶️ Reprise de la musique.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='skip', description="Passe à la chanson suivante")
    async def skip(self, ctx: commands.Context):
        if not ctx.voice_client or not (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            embed = EmbedFactory.error("Erreur", "❌ Aucune musique à passer.", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        ctx.voice_client.stop()
        embed = EmbedFactory.success("Passage", "⏭️ Passage au morceau suivant...", guild=ctx.guild)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='stop', description="Arrête la musique et vide la file")
    async def stop(self, ctx: commands.Context):
        if ctx.guild.id in self.queue:
            self.queue[ctx.guild.id].clear()
            
        if ctx.voice_client:
            ctx.voice_client.stop()
            await ctx.voice_client.disconnect()
            self.voice_clients.pop(ctx.guild.id, None)
            
        self.now_playing.pop(ctx.guild.id, None)
        embed = EmbedFactory.warning("Arrêt Musique", "⏹️ Musique arrêtée et file d'attente vidée.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='queue', description="Affiche la file d'attente")
    async def queue_cmd(self, ctx: commands.Context):
        queue_list = self.queue.get(ctx.guild.id, [])
        if not queue_list:
            embed = EmbedFactory.info("File d'attente", "📋 La file d'attente est vide.", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        fields = []
        for idx, song in enumerate(queue_list[:10], start=1):
            dur = song.get('duration', 0)
            mins, secs = divmod(dur, 60)
            dur_str = f"{mins}:{secs:02d}" if dur > 0 else "Live"
            req = song['requester'].display_name
            fields.append({
                'name': f"{idx}. {song['title'][:45]}",
                'value': f"⏱️ `{dur_str}` | Par: **{req}**",
                'inline': False
            })
            
        embed = EmbedFactory.build(
            title="📋 File d'attente actuelle",
            color='music',
            fields=fields,
            footer_text=f"RymBot • Total: {len(queue_list)} morceau(x)",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='nowplaying', description="Affiche les détails de la musique actuelle")
    async def nowplaying(self, ctx: commands.Context):
        if not ctx.voice_client or not (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            embed = EmbedFactory.error("Erreur", "❌ Aucune musique en cours de lecture.", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        song = self.now_playing.get(ctx.guild.id)
        if not song:
            embed = EmbedFactory.info("Musique", "🎵 Une musique est en cours de lecture.", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        mins, secs = divmod(song.get('duration', 0), 60)
        dur_str = f"{mins}:{secs:02d}" if song.get('duration', 0) > 0 else "Live"
        
        fields = [
            {'name': "Auteur / Chaîne", 'value': song.get('uploader', 'Inconnu'), 'inline': True},
            {'name': "Durée", 'value': f"`{dur_str}`", 'inline': True},
            {'name': "Demandé par", 'value': song['requester'].mention, 'inline': True}
        ]
        
        embed = EmbedFactory.build(
            title="🎵 Maintenant en lecture",
            description=f"**[{song['title']}]({song['url']})**",
            color='music',
            thumbnail_url=song.get('thumbnail'),
            fields=fields,
            guild=ctx.guild,
            bot_user=self.bot.user
        )
        view = MusicControlView(self, ctx.guild.id)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name='loop', description="Active/désactive la répétition du morceau")
    async def loop_cmd(self, ctx: commands.Context):
        current = self.loop.get(ctx.guild.id, False)
        self.loop[ctx.guild.id] = not current
        status_text = "activée" if self.loop[ctx.guild.id] else "désactivée"
        embed = EmbedFactory.info("Répétition", f"🔁 Répétition **{status_text}**.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='volume', description="Ajuste le volume d'écoute (0 à 100)")
    async def volume_cmd(self, ctx: commands.Context, volume: int):
        if volume < 0 or volume > 100:
            embed = EmbedFactory.error("Erreur Volume", "❌ Le volume doit être compris entre 0 et 100.", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        if not ctx.voice_client or not ctx.voice_client.source:
            embed = EmbedFactory.error("Erreur", "❌ Aucune source audio en cours.", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        ctx.voice_client.source.volume = volume / 100.0
        self.volume[ctx.guild.id] = volume
        embed = EmbedFactory.success("Volume", f"🔊 Volume réglé à **{volume}%**.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='shuffle', description="Mélange la file d'attente")
    async def shuffle_cmd(self, ctx: commands.Context):
        import random
        if ctx.guild.id in self.queue and self.queue[ctx.guild.id]:
            random.shuffle(self.queue[ctx.guild.id])
            embed = EmbedFactory.success("File d'attente", "🔀 File d'attente mélangée avec succès !", guild=ctx.guild)
            await ctx.send(embed=embed)
        else:
            embed = EmbedFactory.info("File d'attente", "📋 La file d'attente est vide.", guild=ctx.guild)
            await ctx.send(embed=embed)

    async def play_next(self, ctx: commands.Context):
        """Joue le morceau suivant dans la queue"""
        if ctx.guild.id in self.loop and self.loop[ctx.guild.id]:
            if ctx.guild.id in self.now_playing:
                song = self.now_playing[ctx.guild.id]
                await self._play_audio(ctx, song)
                return
                
        if ctx.guild.id not in self.queue or not self.queue[ctx.guild.id]:
            self.now_playing.pop(ctx.guild.id, None)
            return
            
        song = self.queue[ctx.guild.id].pop(0)
        await self._play_audio(ctx, song)

    async def _play_audio(self, ctx: commands.Context, song: dict):
        """Joue le flux audio via FFmpeg"""
        try:
            vc = ctx.voice_client
            if not vc:
                return
                
            audio_url = song.get('audio_url')
            if not audio_url:
                search_data = await self.search_youtube(song['title'])
                if search_data:
                    audio_url = search_data.get('audio_url')

            if not audio_url:
                embed = EmbedFactory.error("Erreur Audio", f"❌ Impossible de lire l'audio de **{song['title']}**.", guild=ctx.guild)
                await ctx.send(embed=embed)
                return await self.play_next(ctx)

            source = discord.FFmpegPCMAudio(
                audio_url,
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                options="-vn"
            )
            
            vol_val = self.volume.get(ctx.guild.id, 50) / 100.0
            transformed_source = discord.PCMVolumeTransformer(source, volume=vol_val)

            def after_playing(error):
                if error:
                    print(f"Erreur lecture audio: {error}")
                fut = self.play_next(ctx)
                asyncio.run_coroutine_threadsafe(fut, self.bot.loop)

            vc.play(transformed_source, after=after_playing)
            self.now_playing[ctx.guild.id] = song

            # Affichage de l'embed Now Playing avec boutons de contrôle
            mins, secs = divmod(song.get('duration', 0), 60)
            dur_str = f"{mins}:{secs:02d}" if song.get('duration', 0) > 0 else "Live"
            
            embed = EmbedFactory.build(
                title="▶️ Maintenant en lecture",
                description=f"**[{song['title']}]({song['url']})**",
                color='music',
                thumbnail_url=song.get('thumbnail'),
                fields=[
                    {'name': "Auteur", 'value': song.get('uploader', 'Inconnu'), 'inline': True},
                    {'name': "Durée", 'value': f"`{dur_str}`", 'inline': True},
                    {'name': "Demandé par", 'value': song['requester'].mention, 'inline': True}
                ],
                guild=ctx.guild,
                bot_user=self.bot.user
            )
            view = MusicControlView(self, ctx.guild.id)
            await ctx.send(embed=embed, view=view)

        except Exception as e:
            embed = EmbedFactory.error("Erreur de lecture", f"Une erreur est survenue: {str(e)}", guild=ctx.guild)
            await ctx.send(embed=embed)
            await self.play_next(ctx)

async def setup(bot):
    await bot.add_cog(MusicCog(bot))