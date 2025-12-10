# Quick Start - GeoQuizz

Guide de démarrage rapide pour utiliser GeoQuizz avec Git et le déploiement.

## État actuel du projet

✅ **Dépôt Git initialisé**
- Branch: `master`
- 2 commits créés
- Tous les fichiers sont versionnés

## Étapes suivantes

### 1. Connecter à GitHub (recommandé)

#### Option A : Interface GitHub

1. **Créer un nouveau dépôt sur GitHub**
   - Allez sur https://github.com/new
   - Nom: `GeoQuizz`
   - Description: "Application de quiz géographique multijoueur inspirée de GeoGuessr"
   - Visibilité: Public ou Private
   - **NE PAS** cocher "Initialize with README"
   - Cliquez "Create repository"

2. **Connecter votre projet local**
   ```bash
   # Remplacez VOTRE_USERNAME par votre nom d'utilisateur GitHub
   git.bat remote add origin https://github.com/VOTRE_USERNAME/GeoQuizz.git
   git.bat branch -M main
   git.bat push -u origin main
   ```

3. **Authentification**
   - GitHub va demander vos identifiants
   - Utilisez un **Personal Access Token** au lieu du mot de passe
   - Pour créer un token: Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token

#### Option B : GitHub Desktop (plus simple)

1. Téléchargez [GitHub Desktop](https://desktop.github.com/)
2. Installez et connectez-vous
3. File → Add Local Repository → Choisissez le dossier GeoQuizz2
4. Cliquez "Publish repository"

### 2. Tester localement

#### Méthode 1 : Script automatique (Windows)
```bash
start.bat
```
Puis ouvrez http://localhost:5000

#### Méthode 2 : Manuel
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

#### Méthode 3 : Docker
```bash
docker build -t geoquizz .
docker run -p 5000:5000 geoquizz
```

### 3. Préparer des photos de test

Pour tester l'application, vous avez besoin de photos avec métadonnées GPS.

#### Où trouver des photos avec GPS ?

1. **Vos propres photos** de smartphone (si GPS activé)
2. **Photos de vacances** prises avec GPS
3. **Télécharger des exemples** :
   - Flickr avec tag "geotagged"
   - Unsplash (certaines photos ont des GPS)

#### Vérifier les métadonnées GPS

**Windows :**
- Clic droit sur la photo → Propriétés → Détails
- Cherchez "Latitude" et "Longitude" dans les données GPS

**Python (script de vérification):**
```python
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def check_gps(image_path):
    img = Image.open(image_path)
    exif = img._getexif()
    if exif:
        for tag, value in exif.items():
            tag_name = TAGS.get(tag, tag)
            if tag_name == 'GPSInfo':
                print(f"✓ GPS trouvé dans {image_path}")
                return True
    print(f"✗ Pas de GPS dans {image_path}")
    return False

# Utilisation
check_gps("C:\\Photos\\IMG_001.jpg")
```

### 4. Utiliser l'application

1. **Scanner les photos**
   - Entrez votre nom
   - Spécifiez le chemin du dossier (ex: `C:\Photos\Vacances`)
   - Cliquez "Scanner les photos"

2. **Démarrer une partie**
   - Choisissez le nombre de manches
   - Cliquez "Démarrer la partie"

3. **Jouer**
   - Regardez la photo
   - Cliquez sur la carte pour deviner l'emplacement
   - Validez votre réponse
   - Voyez votre score et la vraie localisation

### 5. Mode Multijoueur (API)

Pour tester le mode multijoueur, utilisez l'API REST :

**Python example:**
```python
import requests

BASE = "http://localhost:5000"

# Créer une salle
response = requests.post(f"{BASE}/api/multiplayer/room/create", json={
    "room_name": "Ma partie",
    "host_name": "Alice",
    "num_rounds": 3
})
room_id = response.json()['room_id']
print(f"Salle créée: {room_id}")

# Bob rejoint
requests.post(f"{BASE}/api/multiplayer/room/{room_id}/join", json={
    "player_name": "Bob"
})

# Démarrer
requests.post(f"{BASE}/api/multiplayer/room/{room_id}/start")

# Voir le classement
leaderboard = requests.get(f"{BASE}/api/multiplayer/room/{room_id}/leaderboard")
print(leaderboard.json())
```

Voir `MULTIPLAYER.md` pour le guide complet.

### 6. Déployer en production

Consultez `DEPLOY.md` pour les options de déploiement :

- **Serveur local** : Accessible sur votre réseau local
- **Docker** : Containerisation pour déploiement facile
- **Cloud** : Heroku, Railway, Render, DigitalOcean
- **VPS** : Serveur Linux avec Nginx + Gunicorn

## Commandes Git utiles

Toutes ces commandes utilisent `git.bat` pour contourner le problème de configuration :

```bash
# Voir l'état
git.bat status

# Voir l'historique
git.bat log --oneline --graph

# Créer une branche
git.bat checkout -b feature/nouvelle-fonction

# Ajouter des changements
git.bat add .
git.bat commit -m "Description du changement"

# Pousser vers GitHub
git.bat push

# Récupérer les changements
git.bat pull

# Voir les différences
git.bat diff
```

## Structure du projet

```
GeoQuizz2/
├── app.py                      # Serveur Flask principal
├── photo_manager.py            # Gestion des photos + EXIF
├── game_manager.py             # Logique du jeu + multijoueur
├── requirements.txt            # Dépendances Python
├── start.bat                   # Lancement rapide Windows
├── git.bat                     # Wrapper Git pour Windows
│
├── templates/
│   └── index.html             # Interface web
├── static/
│   ├── css/style.css          # Styles
│   └── js/app.js              # Logique client
│
├── data/                       # Données JSON (auto-créé)
│   ├── sessions.json          # Sessions actives
│   ├── games.json             # Historique
│   └── config.json            # Configuration
│
├── .github/
│   └── workflows/
│       └── test.yml           # CI/CD GitHub Actions
│
├── Dockerfile                  # Configuration Docker
├── docker-compose.yml          # Orchestration Docker
├── .dockerignore              # Exclusions Docker
│
├── README.md                   # Documentation principale
├── MULTIPLAYER.md              # Guide multijoueur
├── GIT_REMOTE_SETUP.md        # Configuration Git distant
├── DEPLOY.md                   # Guide de déploiement
├── QUICK_START.md             # Ce fichier
└── LICENSE                     # Licence MIT
```

## Fonctionnalités principales

### ✅ Implémenté
- [x] Scan récursif des photos avec GPS
- [x] Extraction automatique des métadonnées EXIF
- [x] Mode solo avec scoring (0-5000 points)
- [x] Carte interactive (Leaflet.js)
- [x] Calcul de distance géographique
- [x] Affichage des résultats détaillés
- [x] Classement et historique
- [x] Mode multijoueur tour par tour
- [x] API REST complète
- [x] Interface responsive
- [x] Configuration du nombre de manches
- [x] Persistance JSON (sans BDD)

### 🔜 Améliorations possibles (v2)
- [ ] Interface pour le mode multijoueur
- [ ] WebSocket pour temps réel
- [ ] Chronomètre par manche
- [ ] Chat entre joueurs
- [ ] Modes de jeu supplémentaires (pays spécifique, continents)
- [ ] Indices progressifs
- [ ] Système de niveaux et achievements
- [ ] PWA pour installation mobile
- [ ] Migration vers PostgreSQL pour grandes échelles

## Troubleshooting

### L'application ne trouve pas les photos
- Vérifiez le chemin (utilisez `\` sous Windows)
- Assurez-vous que les photos ont des métadonnées GPS
- Essayez avec le chemin complet : `C:\Users\VOTRE_NOM\Photos\Dossier`

### Git ne fonctionne pas
- Utilisez `git.bat` au lieu de `git`
- Ou utilisez GitHub Desktop

### L'application ne démarre pas
- Vérifiez Python 3.13 : `python --version`
- Réinstallez les dépendances : `pip install -r requirements.txt`
- Vérifiez les logs dans la console

### Port 5000 déjà utilisé
Modifiez le port dans `app.py` (dernière ligne) :
```python
app.run(debug=True, host='0.0.0.0', port=8000)  # Changez 5000 en 8000
```

## Ressources

- **Documentation Flask** : https://flask.palletsprojects.com/
- **Leaflet.js** : https://leafletjs.com/
- **Documentation Git** : https://git-scm.com/doc
- **GitHub Docs** : https://docs.github.com/
- **Docker Docs** : https://docs.docker.com/

## Support

Pour toute question :
1. Consultez la documentation dans les fichiers `.md`
2. Vérifiez les issues sur GitHub
3. Ouvrez une nouvelle issue si nécessaire

## Licence

MIT License - Voir le fichier `LICENSE`

---

**Bon développement avec GeoQuizz ! 🌍🎮**
