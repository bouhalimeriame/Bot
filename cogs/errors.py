# cogs/errors.py
import discord
from discord.ext import commands
import logging

from utils.embeds import EmbedFactory

logger = logging.getLogger(__name__)

class ErrorsCog(commands.Cog, name="Erreurs"):
    """Gestionnaire d'erreurs global élégant pour commandes préfixées et hybrides/slash"""
    
    def __init__(self, bot):
        self.bot = bot
        # Attache le handler d'erreur app_command (slash)
        bot.tree.error(self.on_app_command_error)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Gestionnaire pour les commandes textuelles et hybrides"""
        # Si l'erreur a déjà été traitée par un handler local
        if hasattr(ctx, 'handled_by_local') and ctx.handled_by_local:
            return

        # Ignorer CommandNotFound pour ne pas spammer les logs
        if isinstance(error, commands.CommandNotFound):
            return

        # Déballage des UnhandledCommandError / CommandInvokeError
        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        guild = ctx.guild

        if isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions)
            embed = EmbedFactory.error(
                "Permission Manquante",
                f"❌ Vous n'avez pas la ou les permission(s) requise(s) pour utiliser cette commande (`{perms}`).",
                guild=guild
            )
            return await ctx.send(embed=embed)

        elif isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_permissions)
            embed = EmbedFactory.error(
                "Permissions Bot Insuffisantes",
                f"❌ Le bot nécessite la ou les permission(s) suivante(s) : `{perms}`.",
                guild=guild
            )
            return await ctx.send(embed=embed)

        elif isinstance(error, commands.MissingRequiredArgument):
            param = error.param.name
            embed = EmbedFactory.error(
                "Argument Manquant",
                f"❌ Veuillez spécifier l'argument obligatoire : `{param}`.",
                guild=guild
            )
            return await ctx.send(embed=embed)

        elif isinstance(error, commands.BadArgument):
            embed = EmbedFactory.error(
                "Argument Invalide",
                "❌ Un ou plusieurs arguments fournis sont invalides.",
                guild=guild
            )
            return await ctx.send(embed=embed)

        elif isinstance(error, commands.NotOwner):
            embed = EmbedFactory.error(
                "Accès Refusé",
                "❌ Cette commande est strictement réservée au propriétaire du bot.",
                guild=guild
            )
            return await ctx.send(embed=embed)

        elif isinstance(error, commands.CommandOnCooldown):
            embed = EmbedFactory.warning(
                "Patientez",
                f"⏳ Veuillez patienter `{error.retry_after:.1f}s` avant de réutiliser cette commande.",
                guild=guild
            )
            return await ctx.send(embed=embed)

        else:
            logger.error(f"❌ Erreur non gérée ({ctx.command}): {error}", exc_info=error)
            embed = EmbedFactory.error(
                "Une Erreur est Survenue",
                "❌ Une erreur inattendue est survenue lors de l'exécution de la commande.",
                guild=guild
            )
            try:
                await ctx.send(embed=embed)
            except Exception:
                pass

    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """Gestionnaire d'erreurs dédié aux commandes Slash (Tree)"""
        if isinstance(error, discord.app_commands.CommandInvokeError):
            error = error.original

        guild = interaction.guild

        if isinstance(error, discord.app_commands.MissingPermissions):
            embed = EmbedFactory.error("Permission Manquante", "❌ Vous ne possédez pas les permissions nécessaires.", guild=guild)
        elif isinstance(error, discord.app_commands.BotMissingPermissions):
            embed = EmbedFactory.error("Permission Bot Insuffisante", "❌ Le bot n'a pas les permissions requises.", guild=guild)
        else:
            logger.error(f"❌ Erreur AppCommand ({interaction.command.name}): {error}", exc_info=error)
            embed = EmbedFactory.error("Erreur", "❌ Une erreur est survenue lors du traitement de la commande Slash.", guild=guild)

        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception:
            pass

async def setup(bot):
    await bot.add_cog(ErrorsCog(bot))
