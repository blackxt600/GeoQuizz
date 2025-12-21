# GeoQuizz

Application web de quiz géographique multijoueur inspirée de GeoGuessr.

## Description

GeoQuizz est un jeu où les joueurs doivent deviner l'emplacement géographique de photos. L'application compare leurs réponses avec les vraies coordonnées GPS et attribue des points en fonction de la précision.

## ✨ Version 2.0.0 - Mode Multijoueur avec QR Code

### Nouvelles fonctionnalités
- 🎮 **Mode Multijoueur en temps réel** avec synchronisation WebSocket
- 📱 **QR Code automatique** pour partager facilement les salles de jeu
- 🌐 **Détection d'IP locale** pour connexion sur réseau local
- 🔗 **URL de partage directe** (`/join/{room_id}`)
- ⏱️ **Timer synchronisé** de 60 secondes par manche
- 🎯 **Carte avec marqueurs multijoueur** en couleurs
- 👥 **Jusqu'à 6 joueurs** simultanés par salle
- 🏆 **Classement en temps réel** après chaque manche

## Fonctionnalités principales

### Mode Solo
- **Sélection de photos personnalisées** : Parcourt récursivement un dossier pour trouver des photos avec métadonnées GPS
- **Filtrage automatique** : Ignore les photos sans coordonnées GPS
- **Système de scoring** : Points attribués selon la précision (0-5000 points par manche)
- **Carte interactive** : Interface Leaflet pour placer les réponses
- **Centrage automatique sur la France** : Option activée par défaut pour faciliter la sélection de lieux en France
- **Résultats détaillés** : Affiche la distance, le score et la position réelle après chaque manche
- **Classement** : Historique des meilleures parties
- **Configuration flexible** : Nombre de manches personnalisable (3, 5, 10, 15)

### Mode Multijoueur
- **Lobby avec QR Code** : Créez une salle et partagez le QR code
- **3 façons de rejoindre** : QR code, lien direct ou code de salle
- **Synchronisation temps réel** : Tous les joueurs voient la même photo
- **Gestion des déconnexions** : Pause automatique de 30 secondes
- **Résultats comparatifs** : Carte interactive montrant toutes les réponses

## Prérequis

- Python 3.13 ou supérieur
- Photos avec métadonnées EXIF GPS

## Installation

1. Cloner ou télécharger ce dépôt

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Utilisation

1. Lancer le serveur :
```bash
python app.py
```

2. Ouvrir votre navigateur à l'adresse :
```
http://localhost:5000
```

3. Configurer l'application :
   - Entrer votre nom de joueur
   - Spécifier le chemin du dossier contenant vos photos (ex: `C:\Photos\Vacances`)
   - Choisir le nombre de manches
   - **Option** : Cocher/décocher "Centrer la carte sur la France à chaque manche" (activée par défaut)
   - Cliquer sur "Scanner les photos"

4. Démarrer une partie :
   - Cliquer sur "Démarrer la partie"
   - Pour chaque photo, cliquer sur la carte pour deviner l'emplacement
   - Valider votre réponse
   - Voir le résultat et passer à la manche suivante

## Structure du projet

```
GeoQuizz2/
├── app.py                 # Serveur Flask principal
├── photo_manager.py       # Gestion des photos et extraction EXIF
├── game_manager.py        # Logique du jeu et scoring
├── requirements.txt       # Dépendances Python
├── data/                  # Données JSON (sessions, historique, config)
├── static/
│   ├── css/
│   │   └── style.css     # Styles de l'application
│   └── js/
│       └── app.js        # Logique JavaScript
└── templates/
    └── index.html        # Interface HTML
```

## API REST

### Configuration

- `GET /api/config` - Récupérer la configuration
- `POST /api/config` - Définir la configuration et scanner les photos

### Jeu

- `POST /api/game/start` - Démarrer une nouvelle partie
- `GET /api/game/<session_id>/photo` - Récupérer la photo actuelle
- `POST /api/game/<session_id>/guess` - Soumettre une supposition
- `GET /api/game/<session_id>/summary` - Récupérer le résumé de la partie

### Statistiques

- `GET /api/leaderboard` - Récupérer le classement
- `GET /api/stats` - Récupérer les statistiques générales

## Système de scoring

Le score est calculé selon la distance entre la supposition et la vraie position :

- Distance < 1 km : 5000 points
- Distance > 2000 km : 0 point
- Entre les deux : décroissance exponentielle

**Formule** : `score = 5000 * (2^(-distance/250))`

## 📖 Documentation

- **[Guide Multijoueur](MULTIPLAYER_GUIDE.md)** - Guide complet du mode multijoueur
- **[CLAUDE.md](CLAUDE.md)** - Instructions pour Claude Code
- **[CHANGELOG.md](CHANGELOG.md)** - Historique des versions
- **[DEPLOY.md](DEPLOY.md)** - Guide de déploiement

## 🚀 Quick Start Multijoueur

1. Lancez le serveur : `python app.py`
2. Sur votre PC : Ouvrez http://localhost:5000
3. Cliquez sur "Créer partie multijoueur"
4. **Sur mobile** : Scannez le QR code affiché
5. Jouez ensemble en temps réel !

## Prochaines fonctionnalités (v3)

- Interface mobile optimisée
- Modes de jeu supplémentaires (pays spécifique, continent, etc.)
- Indices progressifs
- Profils utilisateurs persistants
- Mode tournoi
- Équipes multijoueur
- Statistiques avancées

## Technologies utilisées

- **Backend** : Flask (Python 3.13)
- **Frontend** : HTML5, CSS3, JavaScript
- **Temps réel** : Flask-SocketIO, Socket.IO (WebSocket)
- **Cartes** : Leaflet.js
- **QR Code** : qrcode library (PIL)
- **Stockage** : Fichiers JSON (sans base de données)
- **Images** : Pillow (extraction EXIF)
- **Géolocalisation** : geopy

## Licence

Projet éducatif - Libre d'utilisation

## Auteur

Développé avec Claude Code
