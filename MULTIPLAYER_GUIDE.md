# Guide du Mode Multijoueur avec QR Code - GeoQuizz

## Vue d'ensemble

Le mode multijoueur de GeoQuizz permet à plusieurs joueurs de jouer ensemble en temps réel, avec synchronisation des rounds et affichage des résultats comparatifs. Le système utilise WebSocket (Socket.IO) pour la communication temps réel.

## Fonctionnalités

### 1. Création d'une salle multijoueur

**Depuis l'écran d'accueil :**
1. Configurez votre dossier de photos et scannez-les
2. Cliquez sur "Créer partie multijoueur"
3. Vous serez automatiquement désigné comme hôte de la salle
4. Un code de salle unique (8 caractères) sera généré

### 2. Partage de la salle - 3 méthodes

#### Méthode 1 : Code de salle
- Partagez le code de 8 caractères affiché en gros
- Les autres joueurs peuvent le saisir en cliquant sur "Rejoindre une partie"

#### Méthode 2 : QR Code (NOUVEAU !)
- Un QR code est automatiquement généré pour votre salle
- Les joueurs peuvent le scanner avec leur téléphone
- Ils seront automatiquement redirigés vers la salle avec l'URL : `http://[votre-serveur]/join/[room-id]`
- Parfait pour jouer sur mobile ou tablette !

#### Méthode 3 : Lien direct
- Cliquez sur "Copier le lien" sous le QR code
- Partagez le lien par message, email, etc.
- Format du lien : `http://localhost:5000/join/[room-id]`

### 3. Rejoindre une salle

**Plusieurs options :**

1. **Scanner le QR code** (recommandé)
   - Utilisez l'appareil photo de votre téléphone
   - Scannez le QR code affiché sur l'écran de l'hôte
   - Entrez votre nom quand demandé
   - Vous rejoignez automatiquement la salle

2. **Saisir le code manuellement**
   - Cliquez sur "Rejoindre une partie"
   - Entrez le code de 8 caractères
   - Entrez votre nom

3. **Cliquer sur le lien partagé**
   - Cliquez sur le lien reçu de l'hôte
   - Entrez votre nom
   - Rejoignez la salle automatiquement

### 4. Lobby et préparation

**Dans le lobby :**
- Vous voyez tous les joueurs connectés (max 6 joueurs)
- Chaque joueur a une couleur unique
- Cliquez sur "Prêt" quand vous êtes prêt à jouer
- L'hôte peut démarrer la partie quand au moins 2 joueurs sont prêts

**Indicateurs visuels :**
- ✓ = Joueur prêt
- ⏳ = En attente
- (Hôte) = Hôte de la salle

### 5. Déroulement du jeu

**Phase de jeu :**
1. Compte à rebours de 3 secondes avant chaque round
2. Une photo s'affiche - vous avez 60 secondes pour deviner
3. Cliquez sur la carte pour placer votre marqueur
4. Validez votre réponse
5. Attendez que tous les joueurs répondent (ou fin du timer)

**Affichage pendant le jeu :**
- Timer central en gros (devient rouge < 10s)
- Statut de chaque joueur (qui a répondu)
- Photo à deviner à gauche
- Carte interactive à droite

### 6. Résultats

**Après chaque round :**
- Tableau de classement de la manche
- Carte montrant tous les marqueurs des joueurs avec leurs couleurs
- Lignes reliant chaque supposition à la position réelle
- Score de la manche + score total

**Système de points :**
- 5000 points maximum (distance < 1 km)
- 0 point minimum (distance > 2000 km)
- Formule : `5000 * (2^(-distance/250))` - décroissance exponentielle

### 7. Fin de partie

**Écran final :**
- Classement complet avec scores totaux
- Le gagnant est affiché en premier
- Possibilité de rejouer ou retourner à l'accueil

## Fonctionnalités avancées

### Gestion des déconnexions

Si un joueur se déconnecte pendant une partie :
- Le jeu se met en pause automatiquement
- Pause de 30 secondes pour reconnecter
- Si reconnexion : le jeu reprend
- Si non reconnecté : le jeu continue sans lui

### Reconnexion

Un joueur déconnecté peut rejoindre avec le même nom pour reprendre sa partie.

## Configuration réseau

### Accès local
- URL : `http://localhost:5000`
- Fonctionne sur le même ordinateur

### Accès réseau local (LAN)
1. Trouvez votre adresse IP locale (ex: 192.168.1.66)
2. Les joueurs sur le même réseau peuvent accéder via :
   - `http://[votre-ip]:5000`
   - Exemple : `http://192.168.1.66:5000`

### Accès depuis Internet (avancé)
Pour jouer avec des amis à distance :
1. Configurez le port forwarding sur votre routeur (port 5000)
2. Partagez votre IP publique
3. ⚠️ **Attention sécurité** : Le serveur Flask dev n'est pas sécurisé pour production

## Exemples d'utilisation

### Scénario 1 : Jeu en famille
1. Hôte sur PC/laptop crée la salle
2. Affiche le QR code sur l'écran
3. Chaque joueur scanne avec son smartphone/tablette
4. Tout le monde joue en même temps

### Scénario 2 : Soirée entre amis
1. L'hôte partage le lien dans le groupe WhatsApp/Discord
2. Chacun rejoint depuis son appareil
3. Jeu en temps réel avec classement compétitif

### Scénario 3 : Événement/Animation
1. Projetez l'écran avec le QR code
2. Les participants scannent pour rejoindre
3. Jeu collaboratif ou compétitif

## Dépannage

### Le QR code ne s'affiche pas
- Vérifiez que la bibliothèque `qrcode` est installée : `pip install qrcode[pil]`
- Rechargez la page du lobby

### Impossible de rejoindre une salle
- Vérifiez le code de salle (8 caractères)
- Assurez-vous d'être sur le même réseau (pour LAN)
- Vérifiez que le serveur est démarré

### Le timer ne se synchronise pas
- Problème de connexion WebSocket
- Vérifiez votre connexion réseau
- Essayez de vous reconnecter

### Déconnexion fréquente
- Vérifiez votre connexion WiFi
- Rapprochez-vous du routeur
- Fermez les autres applications utilisant beaucoup de bande passante

## API Endpoints

Pour les développeurs qui veulent intégrer ou tester :

```bash
# Créer une salle
POST /api/sync/room/create
Body: {"room_name": "Ma partie", "host_name": "Joueur1", "num_rounds": 5}

# Obtenir le QR code d'une salle
GET /api/multiplayer/room/{room_id}/qrcode
Retourne: Image PNG du QR code

# Rejoindre via URL
GET /join/{room_id}
Ouvre la page avec auto-join

# Vérifier si une salle existe
GET /api/multiplayer/room/{room_id}/exists
Retourne: {"exists": true/false, "room_name": "...", ...}
```

## Conseils pour une meilleure expérience

1. **Utilisez des photos variées** avec GPS de différents endroits du monde
2. **Nombre optimal de joueurs** : 2-4 joueurs pour une meilleure expérience
3. **Connexion stable** : WiFi plutôt que 4G pour éviter les déconnexions
4. **Grand écran** : Projetez l'écran principal pour voir les résultats ensemble
5. **Timer** : 60 secondes par défaut - suffisant pour la plupart des joueurs

## Support

Pour signaler un bug ou demander une fonctionnalité :
- GitHub Issues : https://github.com/anthropics/claude-code/issues
- Vérifiez d'abord les logs du serveur Flask

## Changelog

### Version actuelle
- ✅ QR Code automatique pour partage facile
- ✅ URL directe `/join/{room_id}` pour rejoindre
- ✅ Bouton "Copier le lien"
- ✅ Synchronisation temps réel avec WebSocket
- ✅ Gestion des déconnexions avec pause
- ✅ Jusqu'à 6 joueurs simultanés
- ✅ Timer de 60 secondes par round
- ✅ Carte interactive avec marqueurs colorés
- ✅ Classement en temps réel
