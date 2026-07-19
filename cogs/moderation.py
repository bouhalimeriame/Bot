# cogs/moderation.py
import discord
from discord.ext import commands
import datetime

class ModerationCog(commands.Cog):
    """Cog pour les commandes de modération"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='clear')
    @commands.has_permissions(manage_messages=True)
    async def clear_messages(self, ctx, amount: int):
        """Supprime un nombre de messages (max 100)"""
        try:
            if amount <= 0:
                await ctx.send("❌ Le nombre doit être supérieur à 0.")
                return
            
            if amount > 100:
                amount = 100
                await ctx.send("⚠️ Limité à 100 messages.")
            
            deleted = await ctx.channel.purge(limit=amount + 1)
            
            embed = discord.Embed(
                title="🗑️ Messages supprimés",
                description=f"{len(deleted)-1} messages ont été supprimés.",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"Par {ctx.author.display_name}")
            
            await ctx.send(embed=embed, delete_after=5)
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='gkick')
    @commands.has_permissions(kick_members=True)
    async def kick_member(self, ctx, member: discord.Member, *, reason=None):
        """Expulse un membre du serveur"""
        try:
            if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
                await ctx.send("❌ Vous ne pouvez pas expulser ce membre.")
                return
            
            await member.kick(reason=reason)
            
            embed = discord.Embed(
                title="👢 Membre expulsé",
                description=f"{member.mention} a été expulsé.",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.utcnow()
            )
            if reason:
                embed.add_field(name="Raison", value=reason)
            embed.set_footer(text=f"Par {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='gban')
    @commands.has_permissions(ban_members=True)
    async def ban_member(self, ctx, member: discord.Member, *, reason=None):
        """Bannit un membre du serveur"""
        try:
            if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
                await ctx.send("❌ Vous ne pouvez pas bannir ce membre.")
                return
            
            await member.ban(reason=reason)
            
            embed = discord.Embed(
                title="🚫 Membre banni",
                description=f"{member.mention} a été banni.",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            if reason:
                embed.add_field(name="Raison", value=reason)
            embed.set_footer(text=f"Par {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='unban')
    @commands.has_permissions(ban_members=True)
    async def unban_member(self, ctx, *, member_name: str):
        """Débannit un membre du serveur"""
        try:
            banned_users = await ctx.guild.bans()
            
            for ban_entry in banned_users:
                user = ban_entry.user
                if user.name.lower() == member_name.lower() or str(user) == member_name:
                    await ctx.guild.unban(user)
                    
                    embed = discord.Embed(
                        title="✅ Membre débanni",
                        description=f"{user.mention} a été débanni.",
                        color=discord.Color.green(),
                        timestamp=datetime.datetime.utcnow()
                    )
                    embed.set_footer(text=f"Par {ctx.author.display_name}")
                    
                    await ctx.send(embed=embed)
                    return
            
            await ctx.send(f"❌ Membre '{member_name}' non trouvé dans les bannissements.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='mute')
    @commands.has_permissions(manage_roles=True)
    async def mute_member(self, ctx, member: discord.Member, *, reason=None):
        """Mute un membre"""
        try:
            mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
            
            if not mute_role:
                # Créer le rôle si inexistant
                mute_role = await ctx.guild.create_role(name="Muted")
                
                # Configurer les permissions
                for channel in ctx.guild.channels:
                    await channel.set_permissions(mute_role, send_messages=False, speak=False)
            
            if mute_role in member.roles:
                await ctx.send("❌ Ce membre est déjà mute.")
                return
            
            await member.add_roles(mute_role, reason=reason)
            
            embed = discord.Embed(
                title="🔇 Membre mute",
                description=f"{member.mention} a été mute.",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.utcnow()
            )
            if reason:
                embed.add_field(name="Raison", value=reason)
            embed.set_footer(text=f"Par {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='unmute')
    @commands.has_permissions(manage_roles=True)
    async def unmute_member(self, ctx, member: discord.Member):
        """Unmute un membre"""
        try:
            mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
            
            if not mute_role:
                await ctx.send("❌ Aucun rôle Muted trouvé.")
                return
            
            if mute_role not in member.roles:
                await ctx.send("❌ Ce membre n'est pas mute.")
                return
            
            await member.remove_roles(mute_role)
            
            embed = discord.Embed(
                title="🔊 Membre unmute",
                description=f"{member.mention} a été unmute.",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text=f"Par {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))