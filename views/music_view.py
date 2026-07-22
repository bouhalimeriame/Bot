# views/music_view.py
import discord
from typing import TYPE_CHECKING
from utils.embeds import EmbedFactory

if TYPE_CHECKING:
    from cogs.music import MusicCog

class MusicControlView(discord.ui.View):
    """Panneau de contrôle interactif à boutons pour le lecteur de musique"""
    
    def __init__(self, cog: 'MusicCog', guild_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id

    @discord.ui.button(label="Pause / Reprise", style=discord.ButtonStyle.primary, emoji="⏯️", custom_id="music_pause_resume")
    async def pause_resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if not voice_client:
            embed = EmbedFactory.error("Erreur Musique", "Le bot n'est connecté à aucun salon vocal.", guild=interaction.guild)
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        if voice_client.is_playing():
            voice_client.pause()
            embed = EmbedFactory.info("Pause", "⏸️ La musique a été mise en pause.", guild=interaction.guild)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif voice_client.is_paused():
            voice_client.resume()
            embed = EmbedFactory.success("Reprise", "▶️ La musique a repris.", guild=interaction.guild)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = EmbedFactory.warning("Information", "Aucune musique n'est active.", guild=interaction.guild)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Passer", style=discord.ButtonStyle.secondary, emoji="⏭️", custom_id="music_skip")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if not voice_client or not (voice_client.is_playing() or voice_client.is_paused()):
            embed = EmbedFactory.error("Erreur Musique", "Aucune musique en cours à passer.", guild=interaction.guild)
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        voice_client.stop()
        embed = EmbedFactory.success("Musique Suivante", "⏭️ Passage à la chanson suivante...", guild=interaction.guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Arrêter", style=discord.ButtonStyle.danger, emoji="⏹️", custom_id="music_stop")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if self.guild_id in self.cog.queue:
            self.cog.queue[self.guild_id].clear()
            
        if voice_client:
            voice_client.stop()
            await voice_client.disconnect()
            self.cog.voice_clients.pop(self.guild_id, None)
            
        self.cog.now_playing.pop(self.guild_id, None)
        embed = EmbedFactory.warning("Musique Arrêtée", "⏹️ La musique a été arrêtée et la file d'attente vidée.", guild=interaction.guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Boucle", style=discord.ButtonStyle.secondary, emoji="🔁", custom_id="music_loop")
    async def loop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        current = self.cog.loop.get(self.guild_id, False)
        new_state = not current
        self.cog.loop[self.guild_id] = new_state
        
        status_text = "activée" if new_state else "désactivée"
        emoji = "🔁" if new_state else "➡️"
        embed = EmbedFactory.info("Mode Boucle", f"{emoji} La répétition est maintenant **{status_text}**.", guild=interaction.guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="File d'attente", style=discord.ButtonStyle.secondary, emoji="📋", custom_id="music_queue")
    async def queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        queue_list = self.cog.queue.get(self.guild_id, [])
        if not queue_list:
            embed = EmbedFactory.info("File d'attente", "📋 La file d'attente est actuellement vide.", guild=interaction.guild)
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        fields = []
        for idx, song in enumerate(queue_list[:10], start=1):
            dur = song.get('duration', 0)
            mins, secs = divmod(dur, 60)
            dur_str = f"{mins}:{secs:02d}" if dur > 0 else "Live"
            req = song['requester'].display_name if hasattr(song['requester'], 'display_name') else str(song['requester'])
            fields.append({
                'name': f"{idx}. {song['title'][:45]}",
                'value': f"⏱️ `{dur_str}` | Demandé par: **{req}**",
                'inline': False
            })
            
        footer = f"RymBot • Total: {len(queue_list)} chanson(s) en attente"
        embed = EmbedFactory.build(
            title="📋 File d'attente musicale",
            color='music',
            fields=fields,
            footer_text=footer,
            guild=interaction.guild
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
