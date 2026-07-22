# cogs/welcome.py
import discord
from discord.ext import commands
from datetime import datetime, timezone
import logging

from utils.embeds import EmbedFactory

logger = logging.getLogger(__name__)

class WelcomeCog(commands.Cog, name="Bienvenue"):
    """Cog pour les systèmes de bienvenue, au revoir et attribution de rôle automatique"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Événement déclenché lorsqu'un nouveau membre rejoint le serveur"""
        guild = member.guild
        try:
            settings = await self.bot.db.get_guild_settings(guild.id)
            
            # 1. Attribution automatique de rôle (Auto-role)
            auto_role_id = settings.get("auto_role_id")
            if auto_role_id:
                role = guild.get_role(auto_role_id)
                if role:
                    try:
                        await member.add_roles(role, reason="Attribution automatique de rôle à l'arrivée")
                        logger.info(f"✅ Rôle {role.name} attribué à {member.display_name}")
                    except discord.Forbidden:
                        logger.warning(f"⚠️ Permissions insuffisantes pour donner le rôle {role.name} à {member.display_name}")

            # 2. Message de Bienvenue dans le salon configuré
            welcome_ch_id = settings.get("welcome_channel_id")
            if welcome_ch_id:
                channel = guild.get_channel(welcome_ch_id)
                if channel and isinstance(channel, discord.TextChannel):
                    member_count = guild.member_count
                    created_at_fmt = member.created_at.strftime("%d/%m/%Y à %H:%M")
                    
                    custom_msg = settings.get("welcome_message", "Bienvenue {member} sur **{guild}** ! 🎉")
                    formatted_msg = custom_msg.format(member=member.mention, guild=guild.name)
                    
                    fields = [
                        {'name': "👤 Pseudo", 'value': f"{member.name}", 'inline': True},
                        {'name': "🔢 Membre N°", 'value': f"`#{member_count}`", 'inline': True},
                        {'name': "👥 Total Membres", 'value': f"**{member_count}**", 'inline': True},
                        {'name': "📅 Compte Créé le", 'value': f"`{created_at_fmt}`", 'inline': False}
                    ]
                    
                    avatar_url = member.display_avatar.url if hasattr(member, 'display_avatar') else member.avatar.url
                    
                    embed = EmbedFactory.build(
                        title=f"🎉 Bienvenue sur {guild.name} !",
                        description=formatted_msg,
                        color='success',
                        thumbnail_url=avatar_url,
                        fields=fields,
                        guild=guild,
                        footer_text=f"RymBot • Bienvenue N°{member_count}"
                    )
                    await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"❌ Erreur on_member_join pour {member.display_name}: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Événement déclenché lorsqu'un membre quitte le serveur"""
        guild = member.guild
        try:
            settings = await self.bot.db.get_guild_settings(guild.id)
            goodbye_ch_id = settings.get("goodbye_channel_id")
            
            if goodbye_ch_id:
                channel = guild.get_channel(goodbye_ch_id)
                if channel and isinstance(channel, discord.TextChannel):
                    member_count = guild.member_count
                    custom_msg = settings.get("goodbye_message", "Au revoir {member}, merci d'avoir fait partie de **{guild}** ! 👋")
                    formatted_msg = custom_msg.format(member=f"**{member.display_name}**", guild=guild.name)
                    
                    fields = [
                        {'name': "👥 Membres Restants", 'value': f"**{member_count}** membres", 'inline': True}
                    ]
                    
                    avatar_url = member.display_avatar.url if hasattr(member, 'display_avatar') else member.avatar.url
                    
                    embed = EmbedFactory.build(
                        title=f"👋 Départ de {member.display_name}",
                        description=formatted_msg,
                        color='warning',
                        thumbnail_url=avatar_url,
                        fields=fields,
                        guild=guild,
                        footer_text="RymBot • Au revoir"
                    )
                    await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"❌ Erreur on_member_remove pour {member.display_name}: {e}")

async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))
