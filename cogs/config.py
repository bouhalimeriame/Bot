# cogs/config.py
import discord
from discord.ext import commands
from typing import Optional

from utils.embeds import EmbedFactory
from views.config_view import ConfigView

class ConfigCog(commands.Cog, name="Administration"):
    """Cog de configuration dynamique du bot par serveur"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name='config', description="Affiche ou modifie la configuration du serveur")
    @commands.has_permissions(administrator=True)
    async def config_group(self, ctx: commands.Context):
        """Groupe principal de configuration"""
        if ctx.invoked_subcommand is None:
            settings = await self.bot.db.get_guild_settings(ctx.guild.id)
            view = ConfigView(self.bot, ctx.guild.id, settings)
            
            welcome_ch = ctx.guild.get_channel(settings['welcome_channel_id']).mention if settings['welcome_channel_id'] else "Non configuré"
            goodbye_ch = ctx.guild.get_channel(settings['goodbye_channel_id']).mention if settings['goodbye_channel_id'] else "Non configuré"
            log_ch = ctx.guild.get_channel(settings['log_channel_id']).mention if settings['log_channel_id'] else "Non configuré"
            auto_role = ctx.guild.get_role(settings['auto_role_id']).mention if settings['auto_role_id'] else "Aucun"
            
            fields = [
                {'name': "Préfixe Textuel", 'value': f"`{settings['prefix']}`", 'inline': True},
                {'name': "Rôle Automatique", 'value': auto_role, 'inline': True},
                {'name': "Couleur Principale", 'value': f"`{settings['main_color']}`", 'inline': True},
                {'name': "Salon Bienvenue", 'value': welcome_ch, 'inline': True},
                {'name': "Salon Au Revoir", 'value': goodbye_ch, 'inline': True},
                {'name': "Salon de Logs", 'value': log_ch, 'inline': True}
            ]
            
            embed = EmbedFactory.build(
                title="⚙️ Panneau de Configuration RymBot",
                description=f"Configuration actuelle pour **{ctx.guild.name}** :\n*Utilisez `/config <sous-commande>` ou `.config <sous-commande>` pour modifier un paramètre.*",
                color='primary',
                fields=fields,
                guild=ctx.guild,
                bot_user=self.bot.user
            )
            await ctx.send(embed=embed, view=view)

    @config_group.command(name='prefix', description="Définit le préfixe textuel pour le serveur")
    @commands.has_permissions(administrator=True)
    async def set_prefix(self, ctx: commands.Context, new_prefix: str):
        if len(new_prefix) > 5:
            embed = EmbedFactory.error("Préfixe Invalide", "❌ Le préfixe ne doit pas dépasser 5 caractères.", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        success = await self.bot.db.update_guild_setting(ctx.guild.id, "prefix", new_prefix)
        if success:
            embed = EmbedFactory.success("Préfixe Modifié", f"✅ Le préfixe du bot sur ce serveur est désormais `{new_prefix}`.", guild=ctx.guild)
        else:
            embed = EmbedFactory.error("Erreur BDD", "❌ Échec de la mise à jour du préfixe.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @config_group.command(name='welcome', description="Définit le salon d'envoi des messages de bienvenue")
    @commands.has_permissions(administrator=True)
    async def set_welcome_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        success = await self.bot.db.update_guild_setting(ctx.guild.id, "welcome_channel_id", channel.id)
        if success:
            embed = EmbedFactory.success("Salon Bienvenue", f"✅ Salon de bienvenue configuré sur {channel.mention}.", guild=ctx.guild)
        else:
            embed = EmbedFactory.error("Erreur", "❌ Impossible d'enregistrer le salon.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @config_group.command(name='goodbye', description="Définit le salon d'envoi des messages d'au revoir")
    @commands.has_permissions(administrator=True)
    async def set_goodbye_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        success = await self.bot.db.update_guild_setting(ctx.guild.id, "goodbye_channel_id", channel.id)
        if success:
            embed = EmbedFactory.success("Salon Au Revoir", f"✅ Salon d'au revoir configuré sur {channel.mention}.", guild=ctx.guild)
        else:
            embed = EmbedFactory.error("Erreur", "❌ Impossible d'enregistrer le salon.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @config_group.command(name='logs', description="Définit le salon de journalisation général")
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        success = await self.bot.db.update_guild_setting(ctx.guild.id, "log_channel_id", channel.id)
        if success:
            embed = EmbedFactory.success("Salon de Logs", f"✅ Salon de journalisation configuré sur {channel.mention}.", guild=ctx.guild)
        else:
            embed = EmbedFactory.error("Erreur", "❌ Impossible d'enregistrer le salon.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @config_group.command(name='autorole', description="Définit le rôle attribué automatiquement à l'arrivée")
    @commands.has_permissions(administrator=True)
    async def set_auto_role(self, ctx: commands.Context, role: discord.Role):
        success = await self.bot.db.update_guild_setting(ctx.guild.id, "auto_role_id", role.id)
        if success:
            embed = EmbedFactory.success("Rôle Automatique", f"✅ Rôle automatique configuré sur {role.mention}.", guild=ctx.guild)
        else:
            embed = EmbedFactory.error("Erreur", "❌ Impossible d'enregistrer le rôle.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @config_group.command(name='welcomemsg', description="Personnalise le message d'accueil ({member}, {guild})")
    @commands.has_permissions(administrator=True)
    async def set_welcome_msg(self, ctx: commands.Context, *, message: str):
        success = await self.bot.db.update_guild_setting(ctx.guild.id, "welcome_message", message)
        if success:
            embed = EmbedFactory.success("Message de Bienvenue", f"✅ Message mis à jour :\n```{message}```", guild=ctx.guild)
        else:
            embed = EmbedFactory.error("Erreur", "❌ Échec de la mise à jour.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @config_group.command(name='goodbyemsg', description="Personnalise le message de départ ({member}, {guild})")
    @commands.has_permissions(administrator=True)
    async def set_goodbye_msg(self, ctx: commands.Context, *, message: str):
        success = await self.bot.db.update_guild_setting(ctx.guild.id, "goodbye_message", message)
        if success:
            embed = EmbedFactory.success("Message d'Au Revoir", f"✅ Message mis à jour :\n```{message}```", guild=ctx.guild)
        else:
            embed = EmbedFactory.error("Erreur", "❌ Échec de la mise à jour.", guild=ctx.guild)
        await ctx.send(embed=embed)

    @config_group.command(name='color', description="Définit la couleur HEX principale des embeds")
    @commands.has_permissions(administrator=True)
    async def set_main_color(self, ctx: commands.Context, hex_code: str):
        if not hex_code.startswith('#'):
            hex_code = f"#{hex_code}"
            
        try:
            int(hex_code.lstrip('#'), 16)
        except ValueError:
            embed = EmbedFactory.error("Couleur Invalide", "❌ Veuillez fournir un code hexadécimal valide (ex: `#5865F2`).", guild=ctx.guild)
            return await ctx.send(embed=embed)
            
        success = await self.bot.db.update_guild_setting(ctx.guild.id, "main_color", hex_code)
        if success:
            embed = EmbedFactory.success("Couleur Principale", f"✅ Couleur principale définie à `{hex_code}`.", guild=ctx.guild)
        else:
            embed = EmbedFactory.error("Erreur", "❌ Échec de la mise à jour.", guild=ctx.guild)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ConfigCog(bot))
