# cogs/owner.py
import discord
from discord.ext import commands
import os
import sys
from typing import Optional

from utils.embeds import EmbedFactory

class OwnerCog(commands.Cog, name="Propriétaire"):
    """Cog réservé exclusivement au développeur et propriétaire du bot"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='status', description="Définit l'activité du bot (online, streaming, listening, watching)")
    @commands.is_owner()
    async def set_status(self, ctx: commands.Context, status_type: str, *, status_text: str):
        status_type = status_type.lower()
        
        types_map = {
            'online': discord.ActivityType.playing,
            'playing': discord.ActivityType.playing,
            'streaming': discord.ActivityType.streaming,
            'listening': discord.ActivityType.listening,
            'watching': discord.ActivityType.watching
        }
        
        if status_type not in types_map:
            embed = EmbedFactory.error("Type Invalide", "❌ Types valides: `online`, `playing`, `streaming`, `listening`, `watching`.", guild=ctx.guild)
            return await ctx.send(embed=embed)

        activity = discord.Activity(type=types_map[status_type], name=status_text)
        await self.bot.change_presence(activity=activity)
        
        embed = EmbedFactory.success("Statut Mis à Jour", f"👑 Statut changé en **{status_type.capitalize()}**: `{status_text}`", guild=ctx.guild)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='reload', description="Recharge un ou tous les cogs du bot")
    @commands.is_owner()
    async def reload_cogs(self, ctx: commands.Context, cog_name: Optional[str] = None):
        if cog_name:
            target = f"cogs.{cog_name}" if not cog_name.startswith("cogs.") else cog_name
            try:
                await self.bot.reload_extension(target)
                embed = EmbedFactory.success("Cog Rechargé", f"✅ Le cog `{cog_name}` a été rechargé avec succès.", guild=ctx.guild)
            except Exception as e:
                embed = EmbedFactory.error("Erreur Rechargement", f"❌ Échec du rechargement de `{cog_name}`: {e}", guild=ctx.guild)
            return await ctx.send(embed=embed)
        else:
            reloaded = []
            for file in os.listdir("cogs"):
                if file.endswith(".py") and not file.startswith("__"):
                    name = f"cogs.{file[:-3]}"
                    try:
                        await self.bot.reload_extension(name)
                        reloaded.append(file[:-3])
                    except Exception as e:
                        print(f"Erreur rechargement {name}: {e}")
                        
            embed = EmbedFactory.success("Cogs Rechargés", f"✅ **{len(reloaded)}** cogs rechargés : `{', '.join(reloaded)}`.", guild=ctx.guild)
            await ctx.send(embed=embed)

    @commands.hybrid_command(name='guilds', description="Affiche la liste des serveurs où le bot est présent")
    @commands.is_owner()
    async def list_guilds(self, ctx: commands.Context):
        guilds_text = "\n".join([f"• **{g.name}** (`{g.id}`) - {g.member_count} membres" for g in self.bot.guilds])
        
        embed = EmbedFactory.build(
            title="📊 Serveurs RymBot",
            description=guilds_text[:2000] if guilds_text else "Aucun serveur",
            color='dark',
            footer_text=f"Total: {len(self.bot.guilds)} serveur(s)",
            guild=ctx.guild
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='sync', description="Force la synchronisation des commandes Slash Tree")
    @commands.is_owner()
    async def sync_commands(self, ctx: commands.Context):
        synced = await self.bot.tree.sync()
        embed = EmbedFactory.success("Tree Synchronisé", f"🔮 **{len(synced)}** commandes Slash synchronisées avec succès.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='shutdown', description="Éteint proprement le bot")
    @commands.is_owner()
    async def shutdown_bot(self, ctx: commands.Context):
        embed = EmbedFactory.warning("Arrêt du Bot", "🔄 Arrêt du processus RymBot...", guild=ctx.guild)
        await ctx.send(embed=embed)
        await self.bot.close()

    @commands.hybrid_command(name='restart', description="Redémarre le processus RymBot")
    @commands.is_owner()
    async def restart_bot(self, ctx: commands.Context):
        embed = EmbedFactory.warning("Redémarrage", "🔄 Redémarrage du processus RymBot...", guild=ctx.guild)
        await ctx.send(embed=embed)
        await self.bot.close()
        os.execv(sys.executable, ['python'] + sys.argv)

async def setup(bot):
    await bot.add_cog(OwnerCog(bot))