# cogs/help.py
import discord
from discord.ext import commands

from utils.embeds import EmbedFactory
from views.help_view import HelpSelectView

class HelpCog(commands.Cog, name="Aide"):
    """Cog pour l'affichage moderne de la commande help"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='help', description="Affiche le menu d'aide interactif par catégories")
    async def help_cmd(self, ctx: commands.Context):
        """Commande help principale"""
        guild = ctx.guild
        
        fields = [
            {'name': "🎵 Musique", 'value': "Commandes de lecture audio YouTube/Spotify, file d'attente et contrôle.", 'inline': True},
            {'name': "🔊 Voice", 'value': "Gestion des salons vocaux temporaires personnels.", 'inline': True},
            {'name': "🛡️ Modération", 'value': "Outils de modération (kick, ban, mute, purge).", 'inline': True},
            {'name': "⚙️ Administration", 'value': "Configuration du serveur (welcome, logs, roles).", 'inline': True},
            {'name': "🔮 Utilitaires", 'value': "Informations générales et commandes utilitaires.", 'inline': True},
            {'name': "👑 Propriétaire", 'value': "Gestion du bot (développeur).", 'inline': True}
        ]
        
        embed = EmbedFactory.build(
            title="📚 RymBot • Centre d'Aide & Documentation",
            description=(
                "Bienvenue dans le menu d'aide de **RymBot** !\n\n"
                "👉 **Sélectionnez une catégorie** dans le menu déroulant ci-dessous pour explorer l'ensemble des commandes disponibles.\n\n"
                "*RymBot prend en charge les commandes Slash (`/`) et préfixées (`.`).*"
            ),
            color='primary',
            fields=fields,
            guild=guild,
            bot_user=self.bot.user
        )
        
        view = HelpSelectView(self.bot)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
