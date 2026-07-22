# cogs/moderation.py
import discord
from discord.ext import commands
from typing import Optional

from utils.embeds import EmbedFactory

class ModerationCog(commands.Cog, name="Modération"):
    """Cog complet pour la modération du serveur avec embeds modernes"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='clear', description="Supprime un nombre de messages dans le salon (max 100)")
    @commands.has_permissions(manage_messages=True)
    async def clear_messages(self, ctx: commands.Context, amount: int):
        if amount <= 0:
            embed = EmbedFactory.error("Erreur", "❌ Le nombre de messages doit être supérieur à 0.", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        if amount > 100:
            amount = 100

        # Purge des messages
        deleted = await ctx.channel.purge(limit=amount + 1)
        count = len(deleted) - 1
        
        embed = EmbedFactory.success(
            "Messages Supprimés",
            f"🗑️ **{count}** message(s) ont été supprimés avec succès.",
            guild=ctx.guild,
            author=ctx.author
        )
        await ctx.send(embed=embed, delete_after=5)

    @commands.hybrid_command(name='gkick', description="Expulse un membre du serveur")
    @commands.has_permissions(kick_members=True)
    async def kick_member(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = "Aucune raison spécifiée"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = EmbedFactory.error("Permission Refusée", "❌ Vous ne pouvez pas expulser ce membre (rôle supérieur ou égal).", guild=ctx.guild)
            return await ctx.send(embed=embed)

        await member.kick(reason=reason)
        
        fields = [
            {'name': "Membre Expulsé", 'value': f"{member.mention} (`{member.id}`)", 'inline': True},
            {'name': "Modérateur", 'value': ctx.author.mention, 'inline': True},
            {'name': "Raison", 'value': reason, 'inline': False}
        ]
        
        embed = EmbedFactory.build(
            title="👢 Membre Expulsé",
            color='warning',
            fields=fields,
            guild=ctx.guild,
            author=ctx.author
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='gban', description="Bannit un membre du serveur")
    @commands.has_permissions(ban_members=True)
    async def ban_member(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = "Aucune raison spécifiée"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = EmbedFactory.error("Permission Refusée", "❌ Vous ne pouvez pas bannir ce membre (rôle supérieur ou égal).", guild=ctx.guild)
            return await ctx.send(embed=embed)

        await member.ban(reason=reason)
        
        fields = [
            {'name': "Membre Banni", 'value': f"{member.mention} (`{member.id}`)", 'inline': True},
            {'name': "Modérateur", 'value': ctx.author.mention, 'inline': True},
            {'name': "Raison", 'value': reason, 'inline': False}
        ]
        
        embed = EmbedFactory.build(
            title="🚫 Membre Banni",
            color='error',
            fields=fields,
            guild=ctx.guild,
            author=ctx.author
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='unban', description="Débannit un utilisateur par pseudo ou ID")
    @commands.has_permissions(ban_members=True)
    async def unban_member(self, ctx: commands.Context, *, user_query: str):
        banned_users = [entry async for entry in ctx.guild.bans()]
        
        target_user = None
        for ban_entry in banned_users:
            user = ban_entry.user
            if str(user.id) == user_query or user.name.lower() == user_query.lower() or str(user).lower() == user_query.lower():
                target_user = user
                break

        if not target_user:
            embed = EmbedFactory.error("Introuvable", f"❌ Impossible de trouver l'utilisateur `{user_query}` dans la liste des bannissements.", guild=ctx.guild)
            return await ctx.send(embed=embed)

        await ctx.guild.unban(target_user)
        embed = EmbedFactory.success("Membre Débanni", f"✅ **{target_user.name}** (`{target_user.id}`) a été débanni.", guild=ctx.guild, author=ctx.author)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='mute', description="Mute un membre en lui appliquant le rôle Muted")
    @commands.has_permissions(manage_roles=True)
    async def mute_member(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = "Aucune raison"):
        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
        
        if not mute_role:
            try:
                mute_role = await ctx.guild.create_role(name="Muted", reason="Rôle de mute automatique RymBot")
                for channel in ctx.guild.channels:
                    await channel.set_permissions(mute_role, send_messages=False, speak=False)
            except Exception as e:
                embed = EmbedFactory.error("Erreur Rôle", f"❌ Impossible de créer le rôle Muted: {e}", guild=ctx.guild)
                return await ctx.send(embed=embed)

        if mute_role in member.roles:
            embed = EmbedFactory.warning("Déjà Mute", f"⚠️ {member.mention} est déjà réduit au silence.", guild=ctx.guild)
            return await ctx.send(embed=embed)

        await member.add_roles(mute_role, reason=reason)
        
        embed = EmbedFactory.build(
            title="🔇 Membre Mute",
            description=f"**{member.mention}** a été réduit au silence.",
            color='warning',
            fields=[{'name': "Raison", 'value': reason, 'inline': False}],
            guild=ctx.guild,
            author=ctx.author
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='unmute', description="Unmute un membre")
    @commands.has_permissions(manage_roles=True)
    async def unmute_member(self, ctx: commands.Context, member: discord.Member):
        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
        
        if not mute_role or mute_role not in member.roles:
            embed = EmbedFactory.warning("Non Mute", f"⚠️ {member.mention} n'est pas mute.", guild=ctx.guild)
            return await ctx.send(embed=embed)

        await member.remove_roles(mute_role)
        embed = EmbedFactory.success("Membre Unmute", f"🔊 {member.mention} a retrouvé la parole.", guild=ctx.guild, author=ctx.author)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))