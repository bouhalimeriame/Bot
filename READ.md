# README.md
# RymBot - Bot Discord Professionnel

RymBot est un bot Discord complet avec gestion de salons vocaux temporaires, modération et commandes avancées.

## 📋 Fonctionnalités

### 🎵 Salons Vocaux Temporaires
- Création automatique de rooms vocales
- Gestion de propriétaire
- Limite de participants
- Commandes de gestion complètes

### 🛠️ Commandes Disponibles

#### Gestion de Room (propriétaire uniquement)
- `der <nombre>` - Définir la limite de participants (1-99)
- `lock` - Verrouiller la room
- `unlock` - Déverrouiller la room
- `private` - Rendre la room privée
- `public` - Rendre la room publique
- `rename <nom>` - Renommer la room
- `claim` - Revendiquer la propriété
- `kick @user` - Expulser un utilisateur
- `ban @user` - Bannir un utilisateur
- `transfer @user` - Transférer la propriété
- `hide` - Cacher la room
- `show` - Montrer la room
- `bitrate <64|96|128>` - Définir le débit binaire

#### Modération
- `clear <nombre>` - Supprimer des messages (max 100)
- `kick @user [raison]` - Expulser un membre
- `ban @user [raison]` - Bannir un membre
- `unban <nom>` - Débannir un membre
- `mute @user [raison]` - Mute un membre
- `unmute @user` - Unmute un membre

#### Propriétaire
- `status <type> <texte>` - Changer le statut du bot
- `reload [cog]` - Recharger les cogs
- `load <cog>` - Charger un cog
- `unload <cog>` - Décharger un cog
- `guilds` - Lister les serveurs
- `leave <id>` - Quitter un serveur
- `shutdown` - Arrêter le bot
- `restart` - Redémarrer le bot
- `sync` - Synchroniser les commandes slash

## 🚀 Installation

### 1. Prérequis
- Python 3.12 ou supérieur
- pip (gestionnaire de paquets Python)
- Un serveur Discord avec les permissions nécessaires

### 2. Création du Bot Discord

1. Rendez-vous sur le [Discord Developer Portal](https://discord.com/developers/applications)
2. Cliquez sur "New Application" et donnez un nom à votre bot
3. Allez dans l'onglet "Bot"
4. Cliquez sur "Add Bot" puis confirmez
5. Sous le nom du bot, cliquez sur "Copy" pour récupérer le TOKEN
6. Activez les "Privileged Gateway Intents":
   - Presence Intent
   - Server Members Intent
   - Message Content Intent

### 3. Installation du Bot

```bash
# Cloner le repository
git clone <votre-repository>
cd RymBot

# Créer un environnement virtuel (recommandé)
python -m venv venv

# Activer l'environnement virtuel
# Sur Windows:
venv\Scripts\activate
# Sur Linux/Mac:
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt