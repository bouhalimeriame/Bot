# cogs/voice.py
import discord
from discord.ext import commands
from typing import Optional

from utils.embeds import EmbedFactory
from utils.permissions import Permissions

class VoiceCog(commands.Cog, name="Voice"):
    """Cog de gestion des rooms vocales temporaires"""
    
    def __init__(self, bot):
        self.bot = bot

    async def _check_room_owner(self, ctx: commands.Context) -> Optional[discord.VoiceChannel]:
        """Vérification helper pour s'assurer que le membre gère sa propre room temporaire"""
        if not ctx.author.voice or not ctx.author.voice.channel:
            embed = EmbedFactory.error("Erreur Vocal", "❌ Vous devez être connecté à un salon vocal.", guild=ctx.guild)
            await ctx.send(embed=embed)
            return None
            
        channel = ctx.author.voice.channel
        if not Permissions.is_temp_room(self.bot, channel.id):
            embed = EmbedFactory.error("Erreur Salon", "❌ Ce salon n'est pas une room temporaire.", guild=ctx.guild)
            await ctx.send(embed=embed)
            return None
            
        if not Permissions.is_room_owner(self.bot, channel.id, ctx.author.id):
            embed = EmbedFactory.error("Permission Refusée", "❌ Vous n'êtes pas le propriétaire de cette room.", guild=ctx.guild)
            await ctx.send(embed=embed)
            return None
            
        return channel

    @commands.hybrid_command(name='der', description="Définit le nombre d'utilisateurs max dans la room (1-99)")
    async def set_user_limit(self, ctx: commands.Context, limit: int):
        channel = await self._check_room_owner(ctx)
        if not channel:
            return
            
        if limit < 1 or limit > 99:
            embed = EmbedFactory.error("Limite Invalide", "❌ La limite doit être comprise entre 1 et 99.", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        await channel.edit(user_limit=limit)
        embed = EmbedFactory.success("Limite d'Utilisateurs", f"👥 Limite définie à **{limit}** membres.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='lock', description="Verrouille la room")
    async def lock_room(self, ctx: commands.Context):
        channel = await self._check_room_owner(ctx)
        if not channel:
            return
            
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.connect = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        
        embed = EmbedFactory.success("Room Verrouillée", "🔒 Le salon est désormais verrouillé.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='unlock', description="Déverrouille la room")
    async def unlock_room(self, ctx: commands.Context):
        channel = await self._check_room_owner(ctx)
        if not channel:
            return
            
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.connect = True
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        
        embed = EmbedFactory.success("Room Déverrouillée", "🔓 Le salon est désormais déverrouillé.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='private', description="Rend la room privée")
    async def set_private(self, ctx: commands.Context):
        channel = await self._check_room_owner(ctx)
        if not channel:
            return
            
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        
        embed = EmbedFactory.success("Room Privée", "🔐 Le salon est rendu privé (masqué).", guild=ctx.guild)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='public', description="Rend la room publique")
    async def set_public(self, ctx: commands.Context):
        channel = await self._check_room_owner(ctx)
        if not channel:
            return
            
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = True
        overwrite.connect = True
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        
        embed = EmbedFactory.success("Room Publique", "🌍 Le salon est désormais public.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='rename', description="Renomme la room")
    async def rename_room(self, ctx: commands.Context, *, new_name: str):
        channel = await self._check_room_owner(ctx)
        if not channel:
            return
            
        if len(new_name) > 100:
            embed = EmbedFactory.error("Nom Trop Long", "❌ Le nom doit faire au maximum 100 caractères.", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        await channel.edit(name=new_name)
        embed = EmbedFactory.success("Room Renommée", f"✏️ Salon renommé en **{new_name}**.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='claim', description="Revendique la propriété si le propriétaire est absent")
    async def claim_room(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            embed = EmbedFactory.error("Erreur Vocal", "❌ Vous devez être connecté à un salon vocal.", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        channel = ctx.author.voice.channel
        if not Permissions.is_temp_room(self.bot, channel.id):
            embed = EmbedFactory.error("Erreur Salon", "❌ Ce salon n'est pas une room temporaire.", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        owner_id = self.bot.temp_channels.get(channel.id)
        owner_member = ctx.guild.get_member(owner_id) if owner_id else None
        
        if owner_member and owner_member.voice and owner_member.voice.channel == channel:
            embed = EmbedFactory.error("Revendication Impossible", f"❌ Le propriétaire actuel ({owner_member.mention}) est toujours dans la room.", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        self.bot.temp_channels[channel.id] = ctx.author.id
        await self.bot.db.update_room_owner(channel.id, ctx.author.id)
        
        embed = EmbedFactory.success("Propriété Transférée", f"🔑 Vous êtes désormais le **propriétaire** de cette room.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='kick', description="Expulse un utilisateur de votre room")
    async def kick_user(self, ctx: commands.Context, member: discord.Member):
        channel = await self._check_room_owner(ctx)
        if not channel:
            return
            
        if member.id == ctx.author.id:
            embed = EmbedFactory.error("Erreur", "❌ Vous ne pouvez pas vous expulser vous-même.", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        if member not in channel.members:
            embed = EmbedFactory.error("Erreur", "❌ Cet utilisateur n'est pas dans votre salon vocal.", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        await member.move_to(None)
        embed = EmbedFactory.success("Expulsion", f"👢 {member.mention} a été expulsé de la room.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='ban', description="Bannit un utilisateur de votre room")
    async def ban_user(self, ctx: commands.Context, member: discord.Member):
        channel = await self._check_room_owner(ctx)
        if not channel:
            return
            
        if member.id == ctx.author.id:
            embed = EmbedFactory.error("Erreur", "❌ Vous ne pouvez pas vous bannir vous-même.", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        overwrite = channel.overwrites_for(member)
        overwrite.connect = False
        await channel.set_permissions(member, overwrite=overwrite)
        
        if member in channel.members:
            await member.move_to(None)
            
        embed = EmbedFactory.success("Bannissement Room", f"🚫 {member.mention} a été banni de votre room.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='transfer', description="Transfère la propriété de la room à un membre")
    async def transfer_ownership(self, ctx: commands.Context, member: discord.Member):
        channel = await self._check_room_owner(ctx)
        if not channel:
            return
            
        if member.id == ctx.author.id:
            embed = EmbedFactory.error("Erreur", "❌ Vous possédez déjà la room.", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        if member not in channel.members:
            embed = EmbedFactory.error("Erreur", "❌ Le membre doit être présent dans le salon.", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        self.bot.temp_channels[channel.id] = member.id
        await self.bot.db.update_room_owner(channel.id, member.id)
        
        embed = EmbedFactory.success("Transfère de Propriété", f"🔑 Propriété transférée à {member.mention}.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='bitrate', description="Modifie la qualité audio (64, 96, 128 kbps)")
    async def set_bitrate(self, ctx: commands.Context, bitrate: int):
        channel = await self._check_room_owner(ctx)
        if not channel:
            return
            
        allowed = [64, 96, 128]
        if bitrate not in allowed:
            embed = EmbedFactory.error("Bitrate Invalide", f"❌ Choisissez une valeur parmi: {', '.join(map(str, allowed))} kbps.", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        await channel.edit(bitrate=bitrate * 1000)
        embed = EmbedFactory.success("Qualité Audio", f"📊 Bitrate défini à **{bitrate} kbps**.", guild=ctx.guild)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(VoiceCog(bot))