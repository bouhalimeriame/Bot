# views/voice_view.py
import discord
from typing import Optional, List, Dict, Any
from utils.embeds import EmbedFactory
from utils.permissions import Permissions

class LimitModal(discord.ui.Modal, title="👥 Modifier la limite d'utilisateurs"):
    limit_input = discord.ui.TextInput(
        label="Nombre max d'utilisateurs (1 à 99, 0 = Illimité)",
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
                embed = EmbedFactory.error("Erreur", "Vous devez être connecté à votre salon vocal temporaire.", guild=interaction.guild)
                return await interaction.response.send_message(embed=embed, ephemeral=True)
                
            await channel.edit(user_limit=val)
            limit_str = f"**{val} membres**" if val > 0 else "**Illimité**"
            embed = EmbedFactory.success("Limite Mise à Jour", f"👥 La limite du salon est désormais fixée à {limit_str}.", guild=interaction.guild)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            embed = EmbedFactory.error("Erreur", "Veuillez saisir un chiffre entier valide.", guild=interaction.guild)
            await interaction.response.send_message(embed=embed, ephemeral=True)

class RenameModal(discord.ui.Modal, title="✏️ Renommer le salon vocal"):
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
            embed = EmbedFactory.error("Erreur", "Vous devez être connecté à votre salon vocal temporaire.", guild=interaction.guild)
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        new_name = self.name_input.value.strip()
        await channel.edit(name=new_name)
        embed = EmbedFactory.success("Salon Renommé", f"✏️ Votre salon vocal a été renommé en **{new_name}**.", guild=interaction.guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class KickModal(discord.ui.Modal, title="👢 Expulser un membre de la room"):
    user_input = discord.ui.TextInput(
        label="Nom d'utilisateur ou ID du membre",
        placeholder="Ex: Naythan",
        min_length=1,
        max_length=50,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.user.voice.channel if interaction.user.voice else None
        if not channel or not Permissions.is_temp_room(interaction.client, channel.id):
            embed = EmbedFactory.error("Erreur", "Vous devez être dans votre salon vocal.", guild=interaction.guild)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        query = self.user_input.value.strip().lower()
        target_member = None
        for member in channel.members:
            if query in member.name.lower() or query in member.display_name.lower() or str(member.id) == query:
                target_member = member
                break

        if not target_member:
            embed = EmbedFactory.error("Membre Introuvable", f"❌ Aucun membre nommé `{self.user_input.value}` n'est présent dans ce salon.", guild=interaction.guild)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if target_member.id == interaction.user.id:
            embed = EmbedFactory.error("Erreur", "❌ Vous ne pouvez pas vous expulser vous-même.", guild=interaction.guild)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await target_member.move_to(None)
        embed = EmbedFactory.success("Expulsion Réussie", f"👢 **{target_member.display_name}** a été expulsé de votre salon vocal.", guild=interaction.guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class VoiceRoomControlView(discord.ui.View):
    """Panneau de contrôle interactif moderne pour salons vocaux temporaires"""
    
    def __init__(self):
        super().__init__(timeout=None)

    async def _check_owner(self, interaction: discord.Interaction) -> Optional[discord.VoiceChannel]:
        if not interaction.user.voice or not interaction.user.voice.channel:
            embed = EmbedFactory.error("Erreur Salon Vocal", "Vous devez être connecté à votre salon vocal.", guild=interaction.guild)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return None
            
        channel = interaction.user.voice.channel
        if not Permissions.is_temp_room(interaction.client, channel.id):
            embed = EmbedFactory.error("Erreur Salon", "Ce salon n'est pas une room temporaire active.", guild=interaction.guild)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return None
            
        if not Permissions.is_room_owner(interaction.client, channel.id, interaction.user.id):
            embed = EmbedFactory.error("Permission Refusée", "Seul le propriétaire actuel de la room peut effectuer cette action.", guild=interaction.guild)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return None
            
        return channel

    # ROW 0
    @discord.ui.button(label="Verrouiller", style=discord.ButtonStyle.primary, emoji="🔒", row=0, custom_id="voice_lock")
    async def lock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await self._check_owner(interaction)
        if not channel:
            return
            
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.connect = False
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        
        embed = EmbedFactory.success("Room Verrouillée", "🔒 Le salon est désormais **verrouillé** aux nouveaux membres.", guild=interaction.guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Renommer", style=discord.ButtonStyle.secondary, emoji="✏️", row=0, custom_id="voice_rename")
    async def rename_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await self._check_owner(interaction)
        if not channel:
            return
        await interaction.response.send_modal(RenameModal())

    @discord.ui.button(label="Limiter Membres", style=discord.ButtonStyle.secondary, emoji="👥", row=0, custom_id="voice_limit")
    async def limit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await self._check_owner(interaction)
        if not channel:
            return
        await interaction.response.send_modal(LimitModal())

    # ROW 1
    @discord.ui.button(label="Public", style=discord.ButtonStyle.success, emoji="🌍", row=1, custom_id="voice_public")
    async def public_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await self._check_owner(interaction)
        if not channel:
            return
            
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.view_channel = True
        overwrite.connect = True
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        
        embed = EmbedFactory.success("Salon Public", "🌍 Le salon est désormais **public et visible** par tous.", guild=interaction.guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Privé", style=discord.ButtonStyle.secondary, emoji="🔐", row=1, custom_id="voice_private")
    async def private_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await self._check_owner(interaction)
        if not channel:
            return
            
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.view_channel = False
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        
        embed = EmbedFactory.success("Salon Privé", "🔐 Le salon a été rendu **privé (masqué)**.", guild=interaction.guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Revendiquer", style=discord.ButtonStyle.primary, emoji="🔑", row=1, custom_id="voice_claim")
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            embed = EmbedFactory.error("Erreur Salon Vocal", "Vous devez être dans un salon vocal.", guild=interaction.guild)
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        channel = interaction.user.voice.channel
        if not Permissions.is_temp_room(interaction.client, channel.id):
            embed = EmbedFactory.error("Erreur Salon", "Ce salon n'est pas une room temporaire active.", guild=interaction.guild)
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        owner_id = interaction.client.temp_channels.get(channel.id)
        owner_member = interaction.guild.get_member(owner_id) if owner_id else None
        
        if owner_member and owner_member.voice and owner_member.voice.channel == channel:
            embed = EmbedFactory.error("Revendication Impossible", f"Le propriétaire actuel ({owner_member.mention}) est toujours présent dans la room.", guild=interaction.guild)
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        interaction.client.temp_channels[channel.id] = interaction.user.id
        await interaction.client.db.update_room_owner(channel.id, interaction.user.id)
        
        embed = EmbedFactory.success("Propriété Obtenue", f"🔑 Vous êtes désormais le **nouveau propriétaire** de cette room.", guild=interaction.guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Expulser", style=discord.ButtonStyle.danger, emoji="👢", row=1, custom_id="voice_kick")
    async def kick_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await self._check_owner(interaction)
        if not channel:
            return
        await interaction.response.send_modal(KickModal())
