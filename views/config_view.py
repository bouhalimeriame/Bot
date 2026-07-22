# views/config_view.py
import discord
from utils.embeds import EmbedFactory

class ConfigView(discord.ui.View):
    """Panneau de configuration interactif pour administrateurs"""
    
    def __init__(self, bot, guild_id: int, settings: dict):
        super().__init__(timeout=180)
        self.bot = bot
        self.guild_id = guild_id
        self.settings = settings

    @discord.ui.button(label="Afficher la Config", style=discord.ButtonStyle.primary, emoji="📋", custom_id="cfg_show")
    async def show_cfg_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        settings = await self.bot.db.get_guild_settings(self.guild_id)
        
        welcome_ch = interaction.guild.get_channel(settings['welcome_channel_id']).mention if settings['welcome_channel_id'] else "Non configuré"
        goodbye_ch = interaction.guild.get_channel(settings['goodbye_channel_id']).mention if settings['goodbye_channel_id'] else "Non configuré"
        log_ch = interaction.guild.get_channel(settings['log_channel_id']).mention if settings['log_channel_id'] else "Non configuré"
        auto_role = interaction.guild.get_role(settings['auto_role_id']).mention if settings['auto_role_id'] else "Aucun"
        
        fields = [
            {'name': "Préfixe", 'value': f"`{settings['prefix']}`", 'inline': True},
            {'name': "Rôle Auto", 'value': auto_role, 'inline': True},
            {'name': "Couleur Principale", 'value': f"`{settings['main_color']}`", 'inline': True},
            {'name': "Salon Bienvenue", 'value': welcome_ch, 'inline': True},
            {'name': "Salon Au Revoir", 'value': goodbye_ch, 'inline': True},
            {'name': "Salon de Logs", 'value': log_ch, 'inline': True},
            {'name': "Message de Bienvenue", 'value': f"```{settings['welcome_message']}```", 'inline': False},
            {'name': "Message de Départ", 'value': f"```{settings['goodbye_message']}```", 'inline': False}
        ]
        
        embed = EmbedFactory.build(
            title="⚙️ Configuration du Serveur",
            description=f"Voici la configuration actuelle pour **{interaction.guild.name}** :",
            color='primary',
            fields=fields,
            guild=interaction.guild,
            bot_user=self.bot.user
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
