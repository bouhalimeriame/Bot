# views/help_view.py
import discord
from utils.embeds import EmbedFactory

class HelpCategorySelect(discord.ui.Select):
    """Menu déroulant de sélection de catégorie pour l'aide"""
    
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(
                label="Voice",
                description="Gestion des rooms vocales temporaires",
                emoji="🔊",
                value="voice"
            ),
            discord.SelectOption(
                label="Modération",
                description="Outils de modération (kick, ban, mute, clear)",
                emoji="🛡️",
                value="moderation"
            ),
            discord.SelectOption(
                label="Administration",
                description="Configuration du serveur (welcome, logs, roles)",
                emoji="⚙️",
                value="admin"
            ),
            discord.SelectOption(
                label="Utilitaires",
                description="Commandes générales et informations",
                emoji="🔮",
                value="utils"
            ),
            discord.SelectOption(
                label="Propriétaire",
                description="Commandes réservées au développeur du bot",
                emoji="👑",
                value="owner"
            )
        ]
        super().__init__(placeholder="Selectionnez une categorie...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        prefix = "."
        
        if category == "voice":
            embed = EmbedFactory.build(
                title="🔊 Catégorie: Salons Vocaux Temporaires",
                description="Gérez votre room temporaire personnelle :",
                color='voice',
                fields=[
                    {'name': f"`{prefix}aji <@user|ID|nom>` / `/aji`", 'value': "Déplace un membre dans votre salon vocal.", 'inline': False},
                    {'name': f"`{prefix}limit <nombre>`", 'value': "Définit la limite de membres dans la room (1-99).", 'inline': True},
                    {'name': f"`{prefix}lock` / `{prefix}unlock`", 'value': "Verrouille ou déverrouille l'accès au salon.", 'inline': True},
                    {'name': f"`{prefix}private` / `{prefix}public`", 'value': "Masque ou affiche le salon dans la liste des vocaux.", 'inline': True},
                    {'name': f"`{prefix}rename <nom>`", 'value': "Renomme le salon vocal.", 'inline': True},
                    {'name': f"`{prefix}claim`", 'value': "Revendique la propriété si le créateur a quitté le salon.", 'inline': True},
                    {'name': f"`{prefix}kick @user`", 'value': "Expulse un membre de votre salon vocal.", 'inline': True},
                    {'name': f"`{prefix}ban @user`", 'value': "Interdit à un membre de rejoindre votre salon.", 'inline': True},
                    {'name': f"`{prefix}transfer @user`", 'value': "Transfère la propriété de la room à un ami.", 'inline': True},
                    {'name': f"`{prefix}bitrate <64|96|128>`", 'value': "Modifie la qualité audio du salon.", 'inline': True}
                ],
                guild=interaction.guild,
                bot_user=self.bot.user
            )
        elif category == "moderation":
            embed = EmbedFactory.build(
                title="🛡️ Catégorie: Modération",
                description="Outils de maintien de l'ordre pour modérateurs et administrateurs :",
                color='error',
                fields=[
                    {'name': f"`{prefix}clear <nombre>` / `/clear`", 'value': "Supprime jusqu'à 100 messages dans le salon.", 'inline': False},
                    {'name': f"`{prefix}gkick @user [raison]`", 'value': "Expulse un membre du serveur Discord.", 'inline': True},
                    {'name': f"`{prefix}gban @user [raison]`", 'value': "Bannit définitivement un membre du serveur.", 'inline': True},
                    {'name': f"`{prefix}unban <pseudo/ID>`", 'value': "Lève le bannissement d'un utilisateur.", 'inline': True},
                    {'name': f"`{prefix}mute @user [raison]`", 'value': "Applique le rôle Muted pour réduire au silence.", 'inline': True},
                    {'name': f"`{prefix}unmute @user`", 'value': "Retire le rôle Muted d'un membre.", 'inline': True}
                ],
                guild=interaction.guild,
                bot_user=self.bot.user
            )
        elif category == "admin":
            embed = EmbedFactory.build(
                title="⚙️ Catégorie: Administration",
                description="Configuration générale du bot sur le serveur :",
                color='primary',
                fields=[
                    {'name': f"`{prefix}config` / `/config`", 'value': "Ouvre le panneau de configuration interactif du serveur.", 'inline': False},
                    {'name': f"`{prefix}config prefix <nouveau>`", 'value': "Change le préfixe textuel sur ce serveur.", 'inline': True},
                    {'name': f"`{prefix}config welcome #salon`", 'value': "Définit le salon d'envoi des messages de bienvenue.", 'inline': True},
                    {'name': f"`{prefix}config goodbye #salon`", 'value': "Définit le salon des messages de départ.", 'inline': True},
                    {'name': f"`{prefix}config logs #salon`", 'value': "Définit le salon de journalisation générale.", 'inline': True},
                    {'name': f"`{prefix}config autorole @role`", 'value': "Attribue automatiquement un rôle aux nouveaux arrivants.", 'inline': True}
                ],
                guild=interaction.guild,
                bot_user=self.bot.user
            )
        elif category == "utils":
            embed = EmbedFactory.build(
                title="🔮 Catégorie: Utilitaires",
                description="Commandes utilitaires et d'information :",
                color='info',
                fields=[
                    {'name': f"`{prefix}help` / `/help`", 'value': "Affiche ce menu d'aide interactif.", 'inline': False},
                    {'name': f"`{prefix}ping`", 'value': "Affiche la latence du bot Discord.", 'inline': True},
                    {'name': f"`{prefix}botinfo`", 'value': "Affiche des statistiques sur le bot.", 'inline': True}
                ],
                guild=interaction.guild,
                bot_user=self.bot.user
            )
        elif category == "owner":
            embed = EmbedFactory.build(
                title="👑 Catégorie: Propriétaire",
                description="Commandes système pour l'administrateur du bot :",
                color='dark',
                fields=[
                    {'name': f"`{prefix}status <type> <texte>`", 'value': "Met à jour l'activité du bot.", 'inline': True},
                    {'name': f"`{prefix}reload [cog]`", 'value': "Recharge à chaud un ou plusieurs cogs.", 'inline': True},
                    {'name': f"`{prefix}guilds`", 'value': "Liste les serveurs où le bot est présent.", 'inline': True},
                    {'name': f"`{prefix}sync`", 'value': "Force la synchronisation des commandes Slash.", 'inline': True},
                    {'name': f"`{prefix}restart`", 'value': "Redémarre le processus du bot.", 'inline': True}
                ],
                guild=interaction.guild,
                bot_user=self.bot.user
            )

        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpSelectView(discord.ui.View):
    """View d'aide contenant le Select Menu"""
    
    def __init__(self, bot):
        super().__init__(timeout=180)
        self.add_item(HelpCategorySelect(bot))
