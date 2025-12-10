# Mode Multijoueur - GeoQuizz

## Vue d'ensemble

Le mode multijoueur tour par tour permet à plusieurs joueurs de jouer simultanément à la même série de photos. Chaque joueur progresse à son propre rythme et les scores sont comparés en temps réel.

## Comment jouer en multijoueur

### 1. Créer une salle

L'hôte crée une salle multijoueur :

```bash
POST /api/multiplayer/room/create
{
    "room_name": "Partie entre amis",
    "host_name": "Alice",
    "num_rounds": 5
}
```

Réponse :
```json
{
    "success": true,
    "room_id": "a1b2c3d4",
    "room_name": "Partie entre amis"
}
```

**Important :** Noter le `room_id` pour le partager avec les autres joueurs.

### 2. Rejoindre une salle

Les autres joueurs rejoignent avec le `room_id` :

```bash
POST /api/multiplayer/room/a1b2c3d4/join
{
    "player_name": "Bob"
}
```

### 3. Démarrer la partie

L'hôte démarre la partie quand tous les joueurs sont prêts :

```bash
POST /api/multiplayer/room/a1b2c3d4/start
```

### 4. Jouer

Chaque joueur :
- Récupère sa photo actuelle : `GET /api/multiplayer/room/{room_id}/photo?player_name=Bob`
- Place son marqueur sur la carte
- Soumet sa réponse : `POST /api/multiplayer/room/{room_id}/guess`

### 5. Voir le classement

Consulter le classement en temps réel :

```bash
GET /api/multiplayer/room/a1b2c3d4/leaderboard
```

## Endpoints API Multijoueur

### Créer une salle
```
POST /api/multiplayer/room/create
Body: {
    "room_name": string,
    "host_name": string,
    "num_rounds": int (optionnel, défaut: 5)
}
```

### Rejoindre une salle
```
POST /api/multiplayer/room/<room_id>/join
Body: {
    "player_name": string
}
```

### Démarrer une partie
```
POST /api/multiplayer/room/<room_id>/start
```

### Informations de la salle
```
GET /api/multiplayer/room/<room_id>/info
```

Retourne :
```json
{
    "id": "a1b2c3d4",
    "name": "Partie entre amis",
    "host": "Alice",
    "num_rounds": 5,
    "started": true,
    "finished": false,
    "players": [
        {
            "name": "Alice",
            "total_score": 12500,
            "current_round": 3,
            "finished": false
        },
        {
            "name": "Bob",
            "total_score": 10200,
            "current_round": 2,
            "finished": false
        }
    ]
}
```

### Récupérer la photo actuelle
```
GET /api/multiplayer/room/<room_id>/photo?player_name=<player_name>
```

### Soumettre une réponse
```
POST /api/multiplayer/room/<room_id>/guess
Body: {
    "player_name": string,
    "latitude": float,
    "longitude": float
}
```

### Classement de la salle
```
GET /api/multiplayer/room/<room_id>/leaderboard
```

Retourne :
```json
[
    {
        "player_name": "Alice",
        "total_score": 12500,
        "current_round": 3,
        "finished": false
    },
    {
        "player_name": "Bob",
        "total_score": 10200,
        "current_round": 2,
        "finished": false
    }
]
```

## Fonctionnement du mode tour par tour

- **Progression indépendante** : Chaque joueur progresse à son propre rythme
- **Mêmes photos** : Tous les joueurs voient les mêmes photos dans le même ordre
- **Pas de chronomètre** : Prenez le temps qu'il faut pour chaque manche
- **Classement en temps réel** : Le classement se met à jour après chaque supposition
- **Fin de partie** : La partie se termine quand tous les joueurs ont fini toutes leurs manches

## Exemple de flux complet

```python
import requests

BASE_URL = "http://localhost:5000"

# 1. L'hôte crée une salle
response = requests.post(f"{BASE_URL}/api/multiplayer/room/create", json={
    "room_name": "Ma partie",
    "host_name": "Alice",
    "num_rounds": 3
})
room_id = response.json()['room_id']
print(f"Salle créée : {room_id}")

# 2. Bob rejoint
requests.post(f"{BASE_URL}/api/multiplayer/room/{room_id}/join", json={
    "player_name": "Bob"
})

# 3. L'hôte démarre
requests.post(f"{BASE_URL}/api/multiplayer/room/{room_id}/start")

# 4. Alice joue sa première manche
photo = requests.get(f"{BASE_URL}/api/multiplayer/room/{room_id}/photo?player_name=Alice")
print(f"Photo pour Alice : {photo.json()}")

# Alice place son marqueur à Paris
result = requests.post(f"{BASE_URL}/api/multiplayer/room/{room_id}/guess", json={
    "player_name": "Alice",
    "latitude": 48.8566,
    "longitude": 2.3522
})
print(f"Score d'Alice : {result.json()['score']}")

# 5. Voir le classement
leaderboard = requests.get(f"{BASE_URL}/api/multiplayer/room/{room_id}/leaderboard")
print(f"Classement : {leaderboard.json()}")
```

## Limitations actuelles

- Les salles sont stockées en mémoire (perdues au redémarrage du serveur)
- Pas de système de reconnexion automatique
- Pas de chat entre joueurs
- Pas de limite de temps par manche
- Pas de spectateurs

## Améliorations futures

- [ ] Persistance des salles dans des fichiers JSON
- [ ] Salles privées avec mot de passe
- [ ] Chronomètre optionnel par manche
- [ ] Chat en temps réel
- [ ] Mode spectateur
- [ ] Replay des parties
- [ ] Statistiques détaillées par joueur
- [ ] Tournois et ligues

## Notes techniques

Le mode multijoueur utilise une architecture RESTful classique. Pour une expérience temps réel plus fluide, vous pourriez envisager :

- **WebSocket** pour les mises à jour en temps réel
- **Server-Sent Events (SSE)** pour les notifications push
- **Polling** simple pour une solution sans connexion persistante

L'implémentation actuelle fonctionne avec des appels API classiques, chaque client interrogeant le serveur pour obtenir les mises à jour.
