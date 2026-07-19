# cogs/owner.py
import discord
from discord.ext import commands
import os
import sys
import datetime

class OwnerCog(commands.Cog):
    """Cog pour les commandes réservées au propriétaire"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def is_owner(self, ctx):
        """Vérifie si l'utilisateur est le propriétaire"""
        return await self.bot.is_owner(ctx.author)
    
    @commands.command(name='status')
    @commands.is_owner()
    async def set_status(self, ctx, status_type: str, *, status_text: str):
        """Définit le statut du bot"""
        try:
            status_type = status_type.lower()
            
            if status_type == 'online':
                activity_type = discord.ActivityType.playing
            elif status_type == 'streaming':
                activity_type = discord.ActivityType.streaming
            elif status_type == 'listening':
                activity_type = discord.ActivityType.listening
            elif status_type == 'watching':
                activity_type = discord.ActivityType.watching
            else:
                await ctx.send("❌ Types valides: online, streaming, listening, watching")
                return
            
            await self.bot.change_presence(activity=discord.Activity(
                type=activity_type,
                name=status_text
            ))
            
            await ctx.send(f"✅ Statut changé: {status_type} - {status_text}")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='reload')
    @commands.is_owner()
    async def reload_cogs(self, ctx, cog_name: str = None):
        """Recharge un ou tous les cogs"""
        try:
            if cog_name:
                # Recharger un cog spécifique
                cog_path = f"cogs.{cog_name}"
                await self.bot.reload_extension(cog_path)
                await ctx.send(f"✅ Cog '{cog_name}' rechargé.")
            else:
                # Recharger tous les cogs
                for cog_file in os.listdir("cogs"):
                    if cog_file.endswith(".py"):
                        cog_name = f"cogs.{cog_file[:-3]}"
                        await self.bot.reload_extension(cog_name)
                await ctx.send("✅ Tous les cogs ont été rechargés.")
                
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='load')
    @commands.is_owner()
    async def load_cog(self, ctx, cog_name: str):
        """Charge un cog"""
        try:
            cog_path = f"cogs.{cog_name}"
            await self.bot.load_extension(cog_path)
            await ctx.send(f"✅ Cog '{cog_name}' chargé.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='unload')
    @commands.is_owner()
    async def unload_cog(self, ctx, cog_name: str):
        """Décharge un cog"""
        try:
            cog_path = f"cogs.{cog_name}"
            await self.bot.unload_extension(cog_path)
            await ctx.send(f"✅ Cog '{cog_name}' déchargé.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='guilds')
    @commands.is_owner()
    async def list_guilds(self, ctx):
        """Liste les serveurs du bot"""
        try:
            embed = discord.Embed(
                title="📊 Serveurs",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.utcnow()
            )
            
            guilds_text = ""
            for guild in self.bot.guilds:
                guilds_text += f"• {guild.name} ({guild.id})\n"
            
            if guilds_text:
                embed.add_field(name=f"Total: {len(self.bot.guilds)}", value=guilds_text, inline=False)
            else:
                embed.add_field(name="Total: 0", value="Aucun serveur", inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='leave')
    @commands.is_owner()
    async def leave_guild(self, ctx, guild_id: int):
        """Fait quitter un serveur au bot"""
        try:
            guild = self.bot.get_guild(guild_id)
            
            if not guild:
                await ctx.send(f"❌ Serveur {guild_id} non trouvé.")
                return
            
            await guild.leave()
            await ctx.send(f"✅ Le bot a quitté le serveur {guild.name}.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='shutdown')
    @commands.is_owner()
    async def shutdown_bot(self, ctx):
        """Arrête le bot"""
        try:
            await ctx.send("🔄 Arrêt du bot...")
            await self.bot.close()
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='restart')
    @commands.is_owner()
    async def restart_bot(self, ctx):
        """Redémarre le bot"""
        try:
            await ctx.send("🔄 Redémarrage du bot...")
            await self.bot.close()
            
            # Redémarrer le script
            os.execv(sys.executable, ['python'] + sys.argv)
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
    
    @commands.command(name='sync')
    @commands.is_owner()
    async def sync_commands(self, ctx):
        """Synchronise les commandes slash"""
        try:
            await self.bot.tree.sync()
            await ctx.send("✅ Commandes slash synchronisées.")
            
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")

async def setup(bot):
    await bot.add_cog(OwnerCog(bot))