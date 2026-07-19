# cogs/voice.py
import discord
from discord.ext import commands
from typing import Optional

class VoiceCog(commands.Cog):
    """Cog pour la gestion des commandes vocales"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='help')
    async def show_help(self, ctx):
        """Affiche la liste des commandes disponibles"""
        embed = discord.Embed(
            title="📚 Commandes RymBot",
            description="Voici toutes les commandes disponibles pour gérer votre room vocale :",
            color=discord.Color.blue()
        )
        
        # Commandes de gestion
        embed.add_field(
            name="🔧 Gestion de la room",
            value=(
                "`der <nombre>` - Définir la limite (1-99)\n"
                "`lock` - Verrouiller la room\n"
                "`unlock` - Déverrouiller la room\n"
                "`private` - Rendre privée\n"
                "`public` - Rendre publique\n"
                "`rename <nom>` - Renommer la room\n"
                "`claim` - Revendiquer la propriété\n"
                "`kick @user` - Expulser un utilisateur\n"
                "`ban @user` - Bannir un utilisateur\n"
                "`transfer @user` - Transférer la propriété\n"
                "`hide` - Cacher la room\n"
                "`show` - Montrer la room\n"
                "`bitrate <64|96|128>` - Définir le débit"
            ),
            inline=False
        )
        
        # Modération
        embed.add_field(
            name="🛡️ Modération",
            value=(
                "`clear <nombre>` - Supprimer des messages\n"
                "`gkick @user` - Expulser un membre du serveur\n"
                "`gban @user` - Bannir un membre du serveur\n"
                "`unban <nom>` - Débannir un membre\n"
                "`mute @user` - Mute un membre\n"
                "`unmute @user` - Unmute un membre"
            ),
            inline=False
        )
        
        # Propriétaire
        embed.add_field(
            name="👑 Propriétaire",
            value=(
                "`status <type> <texte>` - Changer le statut\n"
                "`reload` - Recharger les cogs\n"
                "`guilds` - Lister les serveurs\n"
                "`shutdown` - Arrêter le bot\n"
                "`restart` - Redémarrer le bot"
            ),
            inline=False
        )
        
        embed.set_footer(text="Utilisez ces commandes dans le chat de votre room vocale")
        await ctx.send(embed=embed)
    
    @commands.command(name='der')
    async def set_user_limit(self, ctx, limit: int):
        """Définit le nombre maximum d'utilisateurs dans la room"""
        try:
            # Vérifier si l'utilisateur est dans un salon vocal
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send("❌ Vous devez être dans un salon vocal.")
                return
            
            channel = ctx.author.voice.channel
            
            # Vérifier si c'est une room temporaire
            if channel.id not in self.bot.temp_channels:
                await ctx.send("❌ Ce salon n'est pas une room temporaire.")
                return
            
            # Vérifier si l'utilisateur est le propriétaire
            if self.bot.temp_channels[channel.id] != ctx.author.id:
                await ctx.send("❌ Vous n'êtes pas propriétaire de cette room.")
                return
            
            # Vérifier la limite
            if limit < 1 or limit > 99:
                await ctx.send("❌ La limite doit être comprise entre 1 et 99.")
                return
            
            # Appliquer la limite
            await channel.edit(user_limit=limit)
            await ctx.send(f"✅ Limite définie à {limit} utilisateurs.")
            
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas la permission de modifier ce salon.")
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='lock')
    async def lock_room(self, ctx):
        """Verrouille la room (empêche les nouveaux membres de rejoindre)"""
        await self.toggle_lock(ctx, True)
    
    @commands.command(name='unlock')
    async def unlock_room(self, ctx):
        """Déverrouille la room"""
        await self.toggle_lock(ctx, False)
    
    async def toggle_lock(self, ctx, lock: bool):
        """Fonction interne pour verrouiller/déverrouiller"""
        try:
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send("❌ Vous devez être dans un salon vocal.")
                return
            
            channel = ctx.author.voice.channel
            
            if channel.id not in self.bot.temp_channels:
                await ctx.send("❌ Ce salon n'est pas une room temporaire.")
                return
            
            if self.bot.temp_channels[channel.id] != ctx.author.id:
                await ctx.send("❌ Vous n'êtes pas propriétaire de cette room.")
                return
            
            # Modification des permissions
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.connect = not lock if lock is not None else None
            
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            
            status = "verrouillé" if lock else "déverrouillé"
            await ctx.send(f"🔒 Room {status}.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='private')
    async def set_private(self, ctx):
        """Rend la room privée (visible uniquement par les membres)"""
        try:
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send("❌ Vous devez être dans un salon vocal.")
                return
            
            channel = ctx.author.voice.channel
            
            if channel.id not in self.bot.temp_channels:
                await ctx.send("❌ Ce salon n'est pas une room temporaire.")
                return
            
            if self.bot.temp_channels[channel.id] != ctx.author.id:
                await ctx.send("❌ Vous n'êtes pas propriétaire de cette room.")
                return
            
            # Rendre privé
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.view_channel = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            
            await ctx.send("🔒 Room rendue privée.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='public')
    async def set_public(self, ctx):
        """Rend la room publique"""
        try:
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send("❌ Vous devez être dans un salon vocal.")
                return
            
            channel = ctx.author.voice.channel
            
            if channel.id not in self.bot.temp_channels:
                await ctx.send("❌ Ce salon n'est pas une room temporaire.")
                return
            
            if self.bot.temp_channels[channel.id] != ctx.author.id:
                await ctx.send("❌ Vous n'êtes pas propriétaire de cette room.")
                return
            
            # Rendre public
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.view_channel = True
            overwrite.connect = True
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            
            await ctx.send("🌍 Room rendue publique.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='rename')
    async def rename_room(self, ctx, *, new_name: str):
        """Renomme la room"""
        try:
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send("❌ Vous devez être dans un salon vocal.")
                return
            
            channel = ctx.author.voice.channel
            
            if channel.id not in self.bot.temp_channels:
                await ctx.send("❌ Ce salon n'est pas une room temporaire.")
                return
            
            if self.bot.temp_channels[channel.id] != ctx.author.id:
                await ctx.send("❌ Vous n'êtes pas propriétaire de cette room.")
                return
            
            # Vérifier la longueur du nom
            if len(new_name) > 100:
                await ctx.send("❌ Le nom est trop long (max 100 caractères).")
                return
            
            await channel.edit(name=new_name)
            await ctx.send(f"✅ Room renommée en: {new_name}")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='claim')
    async def claim_room(self, ctx):
        """Revendique la propriété de la room (si elle n'a pas de propriétaire)"""
        try:
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send("❌ Vous devez être dans un salon vocal.")
                return
            
            channel = ctx.author.voice.channel
            
            if channel.id not in self.bot.temp_channels:
                await ctx.send("❌ Ce salon n'est pas une room temporaire.")
                return
            
            # Vérifier si le propriétaire est absent
            owner_id = self.bot.temp_channels[channel.id]
            owner = ctx.guild.get_member(owner_id)
            
            if owner and owner.voice and owner.voice.channel == channel:
                await ctx.send("❌ Le propriétaire est toujours dans la room.")
                return
            
            # Revendiquer la propriété
            self.bot.temp_channels[channel.id] = ctx.author.id
            await self.bot.db.update_room_owner(channel.id, ctx.author.id)
            
            await ctx.send(f"🔑 Vous êtes maintenant propriétaire de cette room.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='kick')
    async def kick_user(self, ctx, member: discord.Member):
        """Expulse un utilisateur de la room"""
        try:
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send("❌ Vous devez être dans un salon vocal.")
                return
            
            channel = ctx.author.voice.channel
            
            if channel.id not in self.bot.temp_channels:
                await ctx.send("❌ Ce salon n'est pas une room temporaire.")
                return
            
            if self.bot.temp_channels[channel.id] != ctx.author.id:
                await ctx.send("❌ Vous n'êtes pas propriétaire de cette room.")
                return
            
            if member.id == ctx.author.id:
                await ctx.send("❌ Vous ne pouvez pas vous expulser vous-même.")
                return
            
            if member not in channel.members:
                await ctx.send("❌ Cet utilisateur n'est pas dans cette room.")
                return
            
            await member.move_to(None)
            await ctx.send(f"👢 {member.mention} a été expulsé de la room.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='ban')
    async def ban_user(self, ctx, member: discord.Member):
        """Bannit un utilisateur de la room"""
        try:
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send("❌ Vous devez être dans un salon vocal.")
                return
            
            channel = ctx.author.voice.channel
            
            if channel.id not in self.bot.temp_channels:
                await ctx.send("❌ Ce salon n'est pas une room temporaire.")
                return
            
            if self.bot.temp_channels[channel.id] != ctx.author.id:
                await ctx.send("❌ Vous n'êtes pas propriétaire de cette room.")
                return
            
            if member.id == ctx.author.id:
                await ctx.send("❌ Vous ne pouvez pas vous bannir vous-même.")
                return
            
            # Bannir l'utilisateur
            overwrite = channel.overwrites_for(member)
            overwrite.connect = False
            await channel.set_permissions(member, overwrite=overwrite)
            
            # Expulser si présent
            if member in channel.members:
                await member.move_to(None)
            
            await ctx.send(f"🚫 {member.mention} a été banni de la room.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='transfer')
    async def transfer_ownership(self, ctx, member: discord.Member):
        """Transfère la propriété de la room à un autre utilisateur"""
        try:
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send("❌ Vous devez être dans un salon vocal.")
                return
            
            channel = ctx.author.voice.channel
            
            if channel.id not in self.bot.temp_channels:
                await ctx.send("❌ Ce salon n'est pas une room temporaire.")
                return
            
            if self.bot.temp_channels[channel.id] != ctx.author.id:
                await ctx.send("❌ Vous n'êtes pas propriétaire de cette room.")
                return
            
            if member.id == ctx.author.id:
                await ctx.send("❌ Vous ne pouvez pas vous transférer la propriété à vous-même.")
                return
            
            if member not in channel.members:
                await ctx.send("❌ Cet utilisateur n'est pas dans cette room.")
                return
            
            # Transférer la propriété
            self.bot.temp_channels[channel.id] = member.id
            await self.bot.db.update_room_owner(channel.id, member.id)
            
            await ctx.send(f"🔑 La propriété a été transférée à {member.mention}.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='hide')
    async def hide_room(self, ctx):
        """Cache la room de la liste des salons"""
        try:
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send("❌ Vous devez être dans un salon vocal.")
                return
            
            channel = ctx.author.voice.channel
            
            if channel.id not in self.bot.temp_channels:
                await ctx.send("❌ Ce salon n'est pas une room temporaire.")
                return
            
            if self.bot.temp_channels[channel.id] != ctx.author.id:
                await ctx.send("❌ Vous n'êtes pas propriétaire de cette room.")
                return
            
            # Cacher la room
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.view_channel = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            
            await ctx.send("👻 Room cachée.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='show')
    async def show_room(self, ctx):
        """Montre la room dans la liste des salons"""
        try:
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send("❌ Vous devez être dans un salon vocal.")
                return
            
            channel = ctx.author.voice.channel
            
            if channel.id not in self.bot.temp_channels:
                await ctx.send("❌ Ce salon n'est pas une room temporaire.")
                return
            
            if self.bot.temp_channels[channel.id] != ctx.author.id:
                await ctx.send("❌ Vous n'êtes pas propriétaire de cette room.")
                return
            
            # Montrer la room
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.view_channel = True
            overwrite.connect = True
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            
            await ctx.send("👀 Room visible.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='bitrate')
    async def set_bitrate(self, ctx, bitrate: int):
        """Définit le débit binaire de la room"""
        try:
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send("❌ Vous devez être dans un salon vocal.")
                return
            
            channel = ctx.author.voice.channel
            
            if channel.id not in self.bot.temp_channels:
                await ctx.send("❌ Ce salon n'est pas une room temporaire.")
                return
            
            if self.bot.temp_channels[channel.id] != ctx.author.id:
                await ctx.send("❌ Vous n'êtes pas propriétaire de cette room.")
                return
            
            # Valeurs autorisées: 64, 96, 128
            allowed_values = [64, 96, 128]
            if bitrate not in allowed_values:
                await ctx.send(f"❌ Valeur invalide. Choisissez parmi: {', '.join(map(str, allowed_values))}")
                return
            
            # Le bitrate est en kbps, Discord attend en bps
            await channel.edit(bitrate=bitrate * 1000)
            await ctx.send(f"✅ Débit binaire défini à {bitrate} kbps.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")

async def setup(bot):
    await bot.add_cog(VoiceCog(bot))