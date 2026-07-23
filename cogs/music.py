# cogs/music.py
import os
import re
import logging
import asyncio
from typing import Optional, Dict, List, Any
import aiohttp
import discord
from discord.ext import commands
import yt_dlp

from utils.embeds import EmbedFactory
from views.music_view import MusicControlView

logger = logging.getLogger(__name__)

def get_cookies_path() -> Optional[str]:
    """Détecte ou génère un fichier cookies.txt pour yt-dlp."""
    cookie_path = os.getenv('COOKIES_FILE') or os.getenv('YOUTUBE_COOKIES_PATH') or 'cookies.txt'
    if os.path.exists(cookie_path) and os.path.getsize(cookie_path) > 0:
        logger.info(f"🍪 Cookies YouTube détectés sur le disque: {cookie_path}")
        return cookie_path

    raw_cookies = os.getenv('YOUTUBE_COOKIES')
    b64_cookies = os.getenv('YOUTUBE_COOKIES_BASE64')

    if raw_cookies or b64_cookies:
        try:
            content = raw_cookies
            if b64_cookies:
                import base64
                content = base64.b64decode(b64_cookies).decode('utf-8')

            target_path = 'cookies.txt'
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content.strip())
            logger.info(f"🍪 Fichier cookies.txt créé avec succès via l'environnement -> {target_path}")
            return target_path
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création de cookies.txt: {e}")

    return None

class MusicCog(commands.Cog, name="Musique"):
    """Cog complet et sécurisé pour le système de musique (YouTube & Spotify)"""

    def __init__(self, bot):
        self.bot = bot
        self.queue: Dict[int, List[Dict]] = {}
        self.now_playing: Dict[int, Dict] = {}
        self.voice_clients: Dict[int, discord.VoiceClient] = {}
        self.loop: Dict[int, bool] = {}
        self.volume: Dict[int, int] = {}

        cookie_file = get_cookies_path()

        self.ytdl_opts: Dict[str, Any] = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'default_search': 'ytsearch',
            'source_address': '0.0.0.0',
            'nocheckcertificate': True,
            'cachedir': False,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'mweb', 'web']
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
        }

        if cookie_file:
            self.ytdl_opts['cookiefile'] = cookie_file

        self.ytdl = yt_dlp.YoutubeDL(self.ytdl_opts)

    async def search_youtube(self, query: str) -> Dict[str, Any]:
        """
        Recherche une vidéo ou un lien sur YouTube avec gestion stricte d'erreurs.
        Garantit de ne jamais lever 'NoneType' object has no attribute 'get'.
        """
        try:
            loop = asyncio.get_event_loop()

            if query.startswith(('http://', 'https://')):
                search_query = query
            else:
                search_query = f"ytsearch5:{query}"

            data = await loop.run_in_executor(
                None, lambda: self.ytdl.extract_info(search_query, download=False)
            )

            if not data:
                return {'success': False, 'data': None, 'error_type': 'not_found', 'error_msg': "Aucune donnée retournée par YouTube."}

            entry = None
            if isinstance(data, dict):
                if 'entries' in data:
                    # Filtre rigoureux contre les éléments None générés par ignoreerrors
                    entries = [e for e in data['entries'] if isinstance(e, dict) and (e.get('title') or e.get('url'))]
                    if not entries:
                        return {'success': False, 'data': None, 'error_type': 'not_found', 'error_msg': "Aucun résultat valide trouvé dans la recherche."}
                    entry = entries[0]
                else:
                    entry = data

            if not entry or not isinstance(entry, dict):
                return {'success': False, 'data': None, 'error_type': 'not_found', 'error_msg': "Format de résultat invalide."}

            # Extraction sécurisée des champs sans risque d'erreur NoneType
            title = entry.get('title') or 'Titre Inconnu'
            webpage_url = entry.get('webpage_url') or entry.get('url') or query

            audio_url = entry.get('url')
            if not audio_url and 'formats' in entry and isinstance(entry['formats'], list):
                formats = [f for f in entry['formats'] if isinstance(f, dict) and f.get('acodec') != 'none' and f.get('url')]
                if formats:
                    best_format = max(formats, key=lambda f: f.get('abr') or f.get('tbr') or 0)
                    audio_url = best_format.get('url')

            if not audio_url:
                audio_url = webpage_url

            duration = entry.get('duration') or 0

            thumbnail = entry.get('thumbnail') or ''
            if not thumbnail and entry.get('thumbnails') and isinstance(entry['thumbnails'], list):
                valid_thumbs = [t for t in entry['thumbnails'] if isinstance(t, dict) and t.get('url')]
                if valid_thumbs:
                    thumbnail = valid_thumbs[-1]['url']

            uploader = entry.get('uploader') or entry.get('channel') or 'Artiste Inconnu'

            song_info = {
                'title': title,
                'url': webpage_url,
                'audio_url': audio_url,
                'duration': duration,
                'thumbnail': thumbnail,
                'uploader': uploader,
                'source': 'youtube'
            }

            return {'success': True, 'data': song_info, 'error_type': None, 'error_msg': None}

        except yt_dlp.utils.DownloadError as e:
            err_str = str(e)
            logger.error(f"DownloadError YouTube: {err_str}")
            if "Sign in to confirm" in err_str or "bot" in err_str.lower():
                return {
                    'success': False,
                    'data': None,
                    'error_type': 'bot_block',
                    'error_msg': "YouTube exige une authentification pour vérifier l'accès (détection de bot)."
                }
            return {'success': False, 'data': None, 'error_type': 'error', 'error_msg': f"Erreur YouTube: {err_str}"}
        except Exception as e:
            logger.error(f"Erreur recherche YouTube: {e}", exc_info=True)
            return {'success': False, 'data': None, 'error_type': 'error', 'error_msg': str(e)}

    async def extract_spotify_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Extrait les informations d'un lien Spotify (oEmbed API + OpenGraph parsing)"""
        try:
            clean_url = url.split('?')[0]
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7'
            }

            async with aiohttp.ClientSession() as session:
                track_title = ""
                artist_name = ""
                thumbnail = ""

                # 1. API officielle Spotify oEmbed
                oembed_url = f"https://open.spotify.com/oembed?url={clean_url}"
                try:
                    async with session.get(oembed_url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data and 'title' in data:
                                track_title = data.get('title', '').strip()
                                thumbnail = data.get('thumbnail_url', '')
                except Exception as e:
                    logger.warning(f"Spotify oEmbed fallback: {e}")

                # 2. Parsing HTML OpenGraph
                try:
                    async with session.get(clean_url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as page_res:
                        if page_res.status == 200:
                            html = await page_res.text()

                            if not track_title:
                                og_title = re.search(r'<meta property="og:title" content="([^"]+)"', html)
                                if og_title:
                                    track_title = og_title.group(1).strip()

                            if not thumbnail:
                                og_img = re.search(r'<meta property="og:image" content="([^"]+)"', html)
                                if og_img:
                                    thumbnail = og_img.group(1).strip()

                            og_desc = re.search(r'<meta property="og:description" content="([^"]+)"', html)
                            if og_desc:
                                desc_text = og_desc.group(1)
                                parts = [p.strip() for p in desc_text.replace('·', '•').replace('-', '•').split('•')]
                                if len(parts) >= 1 and parts[0] != track_title:
                                    artist_name = parts[0]
                except Exception as e:
                    logger.warning(f"Spotify HTML parsing fallback: {e}")

                if not track_title:
                    return None

                full_title = f"{track_title} - {artist_name}" if (artist_name and artist_name.lower() not in track_title.lower()) else track_title
                search_query = f"{track_title} {artist_name} audio" if artist_name else f"{track_title} audio"

                return {
                    'title': full_title,
                    'query': search_query,
                    'thumbnail': thumbnail,
                    'artist': artist_name or "Spotify",
                }
        except Exception as e:
            logger.error(f"Erreur extraction Spotify: {e}")
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
        """Recherche et ajoute une musique à la file d'attente"""
        vc = await self.ensure_voice(ctx)
        if not vc:
            return

        embed_searching = EmbedFactory.info("Recherche", f"🔍 Recherche de `{query}` en cours...", guild=ctx.guild)
        loading_msg = await ctx.send(embed=embed_searching)

        song = None
        is_spotify = 'spotify.com' in query

        if is_spotify:
            spotify_info = await self.extract_spotify_info(query)
            if spotify_info:
                res = await self.search_youtube(spotify_info['query'])
                if res['success'] and res['data']:
                    song = res['data']
                    song['title'] = spotify_info['title']
                    if spotify_info.get('thumbnail'):
                        song['thumbnail'] = spotify_info['thumbnail']
                elif res['error_type'] == 'bot_block':
                    embed_err = EmbedFactory.error(
                        "YouTube — Authentification Requise",
                        "⚠️ YouTube a bloqué la requête (détection de bot sur le serveur d'hébergement).\n\n"
                        "**Solution :** Configurez la variable `YOUTUBE_COOKIES` sur Railway ou fournissez un fichier `cookies.txt`.",
                        guild=ctx.guild
                    )
                    if isinstance(loading_msg, discord.Message):
                        return await loading_msg.edit(embed=embed_err)
                    else:
                        return await ctx.send(embed=embed_err)

            if not song:
                embed_err = EmbedFactory.error(
                    "Spotify — Morceau Introuvable",
                    "❌ Impossible de trouver ce morceau sur YouTube.\n"
                    "💡 **Conseil :** Essayez d'indiquer directement le **nom du morceau et l'artiste**.",
                    guild=ctx.guild
                )
                if isinstance(loading_msg, discord.Message):
                    return await loading_msg.edit(embed=embed_err)
                else:
                    return await ctx.send(embed=embed_err)
        else:
            res = await self.search_youtube(query)
            if res['success'] and res['data']:
                song = res['data']
            elif res['error_type'] == 'bot_block':
                embed_err = EmbedFactory.error(
                    "YouTube — Détection de Bot",
                    "❌ YouTube bloque l'accès automatique depuis ce serveur d'hébergement.\n\n"
                    "**Solutions :**\n"
                    "1. Ajoutez la variable d'environnement `YOUTUBE_COOKIES` dans Railway avec vos cookies YouTube.\n"
                    "2. Ou ajoutez un fichier `cookies.txt` à la racine du projet.\n"
                    "3. Ou essayez avec un nom de titre précis au lieu d'une URL.",
                    guild=ctx.guild
                )
                if isinstance(loading_msg, discord.Message):
                    return await loading_msg.edit(embed=embed_err)
                else:
                    return await ctx.send(embed=embed_err)
            else:
                embed_err = EmbedFactory.error(
                    "Morceau Introuvable",
                    f"❌ Aucun morceau correspondant à `{query}` n'a été trouvé.",
                    guild=ctx.guild
                )
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
            req = song['requester'].display_name if hasattr(song.get('requester'), 'display_name') else str(song.get('requester', 'Membre'))
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

        req_mention = song['requester'].mention if 'requester' in song and hasattr(song['requester'], 'mention') else "Inconnu"

        fields = [
            {'name': "Auteur / Chaîne", 'value': song.get('uploader', 'Inconnu'), 'inline': True},
            {'name': "Durée", 'value': f"`{dur_str}`", 'inline': True},
            {'name': "Demandé par", 'value': req_mention, 'inline': True}
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
            if not audio_url or not audio_url.startswith('http'):
                search_res = await self.search_youtube(song['title'])
                if search_res['success'] and search_res['data']:
                    audio_url = search_res['data'].get('audio_url')

            if not audio_url:
                embed = EmbedFactory.error("Erreur Audio", f"❌ Impossible d'extraire l'audio pour **{song['title']}**.", guild=ctx.guild)
                await ctx.send(embed=embed)
                return await self.play_next(ctx)

            ffmpeg_before_options = (
                "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 "
                "-probesize 10000000 -analyzeduration 10000000"
            )
            ffmpeg_options = "-vn"

            source = discord.FFmpegPCMAudio(
                audio_url,
                before_options=ffmpeg_before_options,
                options=ffmpeg_options
            )

            vol_val = self.volume.get(ctx.guild.id, 50) / 100.0
            transformed_source = discord.PCMVolumeTransformer(source, volume=vol_val)

            def after_playing(error):
                if error:
                    logger.error(f"Erreur lecture audio FFmpeg: {error}")
                fut = self.play_next(ctx)
                asyncio.run_coroutine_threadsafe(fut, self.bot.loop)

            vc.play(transformed_source, after=after_playing)
            self.now_playing[ctx.guild.id] = song

            mins, secs = divmod(song.get('duration', 0), 60)
            dur_str = f"{mins}:{secs:02d}" if song.get('duration', 0) > 0 else "Live"

            req_mention = song['requester'].mention if 'requester' in song and hasattr(song['requester'], 'mention') else "Inconnu"

            embed = EmbedFactory.build(
                title="▶️ Maintenant en lecture",
                description=f"**[{song['title']}]({song['url']})**",
                color='music',
                thumbnail_url=song.get('thumbnail'),
                fields=[
                    {'name': "Auteur", 'value': song.get('uploader', 'Inconnu'), 'inline': True},
                    {'name': "Durée", 'value': f"`{dur_str}`", 'inline': True},
                    {'name': "Demandé par", 'value': req_mention, 'inline': True}
                ],
                guild=ctx.guild,
                bot_user=self.bot.user
            )
            view = MusicControlView(self, ctx.guild.id)
            await ctx.send(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Erreur lors du lancement audio: {e}", exc_info=True)
            embed = EmbedFactory.error("Erreur de lecture", f"Une erreur audio est survenue : {str(e)}", guild=ctx.guild)
            await ctx.send(embed=embed)
            await self.play_next(ctx)

async def setup(bot):
    await bot.add_cog(MusicCog(bot))