# views/voice_view.py
import discord
from typing import Optional, List, Dict, Any
from utils.embeds import EmbedFactory
from utils.permissions import Permissions

class LimitModal(discord.ui.Modal, title="Modifier la limite d'utilisateurs"):
    limit_input = discord.ui.TextInput(
        label="Limite d'utilisateurs (1 à 99, ou 0 pour illimité)",
        placeholder="Ex: 5",
        min_length=1,
        max_length=2,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = int(self.limit_input.value)
            if val < 0 or val > 99:
                embed = EmbedFactory.error("Limite Invalide", "Veuillez entrer un nombre entre 0 et 99.", guild=interaction.guild)
                return await interaction.response.send_message(embed=embed, ephemeral=True)
                
            channel = interaction.user.voice.channel if interaction.user.voice else None
            if not channel or not Permissions.is_temp_room(interaction.client, channel.id):
                embed = EmbedFactory.error("Erreur", "Vous devez être dans votre room temporaire.", guild=interaction.guild)
                return await interaction.response.send_message(embed=embed, ephemeral=True)
                
            await channel.edit(user_limit=val)
            embed = EmbedFactory.success("Limite Mise à Jour", f"👥 La limite a été définie à **{val if val > 0 else 'Illimité'}** membres.", guild=interaction.guild)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            embed = EmbedFactory.error("Erreur", "Veuillez saisir un chiffre valide.", guild=interaction.guild)
            await interaction.response.send_message(embed=embed, ephemeral=True)

class RenameModal(discord.ui.Modal, title="Renommer la room"):
    name_input = discord.ui.TextInput(
        label="Nouveau nom du salon",
        placeholder="Room de ...",
        min_length=1,
        max_length=50,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.user.voice.channel if interaction.user.voice else None
        if not channel or not Permissions.is_temp_room(interaction.client, channel.id):
            embed = EmbedFactory.error("Erreur", "Vous devez être dans votre room temporaire.", guild=interaction.guild)
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        new_name = self.name_input.value.strip()
        await channel.edit(name=new_name)
        embed = EmbedFactory.success("Room Renommée", f"✏️ Le salon s'appelle désormais **{new_name}**.", guild=interaction.guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class VoiceRoomControlView(discord.ui.View):
    """Panneau de gestion interactif pour les rooms temporaires"""
    
    def __init__(self):
        super().__init__(timeout=None)

    async def _check_owner(self, interaction: discord.Interaction) -> Optional[discord.VoiceChannel]:
        if not interaction.user.voice or not interaction.user.voice.channel:
            embed = EmbedFactory.error("Erreur Salon Vocal", "Vous devez être connecté à un salon vocal.", guild=interaction.guild)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return None
            
        channel = interaction.user.voice.channel
        if not Permissions.is_temp_room(interaction.client, channel.id):
            embed = EmbedFactory.error("Erreur Salon", "Ce salon n'est pas une room temporaire.", guild=interaction.guild)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return None
            
        if not Permissions.is_room_owner(interaction.client, channel.id, interaction.user.id):
            embed = EmbedFactory.error("Permission Refusée", "Seul le propriétaire de la room peut effectuer cette action.", guild=interaction.guild)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return None
            
        return channel

    @discord.ui.button(label="Verrouiller / Déverrouiller", style=discord.ButtonStyle.primary, emoji="🔒", custom_id="voice_toggle_lock")
    async def toggle_lock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await self._check_owner(interaction)
        if not channel:
            return
            
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        is_currently_locked = overwrite.connect is False
        
        overwrite.connect = True if is_currently_locked else False
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        
        status_str = "🔓 déverrouillée" if is_currently_locked else "🔒 verrouillée"
        embed = EmbedFactory.success("Statut de la room", f"La room est maintenant **{status_str}**.", guild=interaction.guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Renommer", style=discord.ButtonStyle.secondary, emoji="✏️", custom_id="voice_rename")
    async def rename_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await self._check_owner(interaction)
        if not channel:
            return
        await interaction.response.send_modal(RenameModal())

    @discord.ui.button(label="Limite Membres", style=discord.ButtonStyle.secondary, emoji="👥", custom_id="voice_limit")
    async def limit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await self._check_owner(interaction)
        if not channel:
            return
        await interaction.response.send_modal(LimitModal())

    @discord.ui.button(label="Privé / Public", style=discord.ButtonStyle.secondary, emoji="🔐", custom_id="voice_toggle_private")
    async def toggle_private_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await self._check_owner(interaction)
        if not channel:
            return
            
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        is_hidden = overwrite.view_channel is False
        
        overwrite.view_channel = True if is_hidden else False
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        
        status_str = "🌍 publique" if is_hidden else "🔐 privée"
        embed = EmbedFactory.success("Visibilité de la room", f"La room est désormais **{status_str}**.", guild=interaction.guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Revendiquer", style=discord.ButtonStyle.success, emoji="🔑", custom_id="voice_claim")
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            embed = EmbedFactory.error("Erreur Salon Vocal", "Vous devez être dans un salon vocal.", guild=interaction.guild)
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        channel = interaction.user.voice.channel
        if not Permissions.is_temp_room(interaction.client, channel.id):
            embed = EmbedFactory.error("Erreur Salon", "Ce salon n'est pas une room temporaire.", guild=interaction.guild)
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        owner_id = interaction.client.temp_channels.get(channel.id)
        owner_member = interaction.guild.get_member(owner_id) if owner_id else None
        
        if owner_member and owner_member.voice and owner_member.voice.channel == channel:
            embed = EmbedFactory.error("Revendication Impossible", f"Le propriétaire actuel ({owner_member.mention}) est toujours présent.", guild=interaction.guild)
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        interaction.client.temp_channels[channel.id] = interaction.user.id
        await interaction.client.db.update_room_owner(channel.id, interaction.user.id)
        
        embed = EmbedFactory.success("Propriété Transférée", f"🔑 Vous êtes désormais le **propriétaire** de cette room vocal.", guild=interaction.guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)
