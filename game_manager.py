"""
Module de gestion du jeu et du scoring
"""
import json
import os
import uuid
from datetime import datetime
from geopy.distance import geodesic


class GameManager:
    def __init__(self, data_folder='data'):
        """
        Initialise le gestionnaire de jeu

        Args:
            data_folder: Dossier où stocker les fichiers JSON
        """
        self.data_folder = data_folder
        self.sessions_file = os.path.join(data_folder, 'sessions.json')
        self.games_file = os.path.join(data_folder, 'games.json')
        self.config_file = os.path.join(data_folder, 'config.json')

        # Sessions actives en mémoire
        self.active_sessions = {}

        # Salles multijoueurs actives
        self.multiplayer_rooms = {}

        # Charger les données existantes
        self._load_sessions()

    def _load_sessions(self):
        """Charge les sessions depuis le fichier JSON"""
        if os.path.exists(self.sessions_file):
            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    self.active_sessions = json.load(f)
            except:
                self.active_sessions = {}

    def _save_sessions(self):
        """Sauvegarde les sessions dans le fichier JSON"""
        os.makedirs(self.data_folder, exist_ok=True)
        with open(self.sessions_file, 'w', encoding='utf-8') as f:
            json.dump(self.active_sessions, f, indent=2, ensure_ascii=False)

    def create_game(self, player_name, photos, num_rounds=5):
        """
        Crée une nouvelle partie

        Args:
            player_name: Nom du joueur
            photos: Liste des photos pour cette partie
            num_rounds: Nombre de manches

        Returns:
            ID de la session de jeu
        """
        session_id = str(uuid.uuid4())

        # Limiter le nombre de photos au nombre de rounds
        game_photos = photos[:num_rounds]

        session = {
            'id': session_id,
            'player_name': player_name,
            'created_at': datetime.now().isoformat(),
            'num_rounds': num_rounds,
            'current_round': 0,
            'photos': game_photos,
            'guesses': [],
            'scores': [],
            'total_score': 0,
            'finished': False
        }

        self.active_sessions[session_id] = session
        self._save_sessions()

        return session_id

    def get_current_photo(self, session_id):
        """
        Récupère la photo actuelle pour une session

        Args:
            session_id: ID de la session

        Returns:
            Dict avec les infos de la photo (sans les coordonnées GPS)
        """
        session = self.active_sessions.get(session_id)
        if not session or session['finished']:
            return None

        current_round = session['current_round']
        if current_round >= len(session['photos']):
            return None

        photo = session['photos'][current_round]

        # Retourner les infos sans les coordonnées GPS (pour ne pas tricher)
        return {
            'path': photo['path'],
            'round': current_round + 1,
            'total_rounds': session['num_rounds']
        }

    def submit_guess(self, session_id, guess_lat, guess_lon):
        """
        Enregistre une supposition et calcule le score

        Args:
            session_id: ID de la session
            guess_lat: Latitude devinée
            guess_lon: Longitude devinée

        Returns:
            Dict avec les résultats (score, distance, vraies coordonnées)
        """
        session = self.active_sessions.get(session_id)
        if not session or session['finished']:
            return None

        current_round = session['current_round']
        if current_round >= len(session['photos']):
            return None

        # Récupérer les vraies coordonnées
        photo = session['photos'][current_round]
        true_lat = photo['latitude']
        true_lon = photo['longitude']

        # Calculer la distance
        true_coords = (true_lat, true_lon)
        guess_coords = (guess_lat, guess_lon)
        distance_km = geodesic(true_coords, guess_coords).kilometers

        # Calculer le score (système inspiré de GeoGuessr)
        # Score maximum de 5000 points si distance = 0
        # Score décroissant avec la distance
        score = self._calculate_score(distance_km)

        # Enregistrer la supposition
        guess_data = {
            'round': current_round + 1,
            'guess_lat': guess_lat,
            'guess_lon': guess_lon,
            'true_lat': true_lat,
            'true_lon': true_lon,
            'distance_km': round(distance_km, 2),
            'score': score
        }

        session['guesses'].append(guess_data)
        session['scores'].append(score)
        session['total_score'] += score

        # Passer à la manche suivante
        session['current_round'] += 1

        # Vérifier si la partie est terminée
        if session['current_round'] >= session['num_rounds']:
            session['finished'] = True
            self._save_game_history(session)

        self._save_sessions()

        return guess_data

    def _calculate_score(self, distance_km):
        """
        Calcule le score basé sur la distance

        Args:
            distance_km: Distance en kilomètres

        Returns:
            Score (0-5000)
        """
        # Formule inspirée de GeoGuessr
        # Score max (5000) si distance < 1km
        # Score min (0) si distance > 2000km
        if distance_km < 1:
            return 5000
        elif distance_km > 2000:
            return 0
        else:
            # Décroissance exponentielle
            score = 5000 * (2 ** (-distance_km / 250))
            return round(score)

    def get_session_summary(self, session_id):
        """
        Récupère le résumé d'une session

        Args:
            session_id: ID de la session

        Returns:
            Dict avec le résumé de la session
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return None

        return {
            'player_name': session['player_name'],
            'total_score': session['total_score'],
            'num_rounds': session['num_rounds'],
            'current_round': session['current_round'],
            'finished': session['finished'],
            'guesses': session['guesses']
        }

    def _save_game_history(self, session):
        """
        Sauvegarde l'historique d'une partie terminée

        Args:
            session: Données de la session
        """
        # Charger l'historique existant
        games = []
        if os.path.exists(self.games_file):
            try:
                with open(self.games_file, 'r', encoding='utf-8') as f:
                    games = json.load(f)
            except:
                games = []

        # Ajouter la nouvelle partie
        game_record = {
            'player_name': session['player_name'],
            'date': session['created_at'],
            'total_score': session['total_score'],
            'num_rounds': session['num_rounds'],
            'average_score': round(session['total_score'] / session['num_rounds'], 2)
        }

        games.append(game_record)

        # Sauvegarder
        with open(self.games_file, 'w', encoding='utf-8') as f:
            json.dump(games, f, indent=2, ensure_ascii=False)

    def get_leaderboard(self, limit=10):
        """
        Récupère le classement des meilleures parties

        Args:
            limit: Nombre de résultats à retourner

        Returns:
            Liste des meilleures parties
        """
        if not os.path.exists(self.games_file):
            return []

        try:
            with open(self.games_file, 'r', encoding='utf-8') as f:
                games = json.load(f)

            # Trier par score total décroissant
            games.sort(key=lambda x: x['total_score'], reverse=True)

            return games[:limit]
        except:
            return []

    def save_config(self, config):
        """
        Sauvegarde la configuration

        Args:
            config: Dict de configuration
        """
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def load_config(self):
        """
        Charge la configuration

        Returns:
            Dict de configuration ou None
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return None
        return None

    # ===== MÉTHODES MULTIJOUEUR =====

    def create_multiplayer_room(self, room_name, host_name, photos, num_rounds=5):
        """
        Crée une salle multijoueur

        Args:
            room_name: Nom de la salle
            host_name: Nom de l'hôte
            photos: Liste des photos pour cette partie
            num_rounds: Nombre de manches

        Returns:
            ID de la salle
        """
        room_id = str(uuid.uuid4())[:8]  # ID court pour faciliter le partage

        # Limiter le nombre de photos au nombre de rounds
        game_photos = photos[:num_rounds]

        room = {
            'id': room_id,
            'name': room_name,
            'host': host_name,
            'created_at': datetime.now().isoformat(),
            'num_rounds': num_rounds,
            'photos': game_photos,
            'players': {},  # {player_name: {current_round, guesses, scores, total_score}}
            'started': False,
            'finished': False
        }

        # Ajouter l'hôte comme premier joueur
        room['players'][host_name] = {
            'current_round': 0,
            'guesses': [],
            'scores': [],
            'total_score': 0,
            'finished': False
        }

        self.multiplayer_rooms[room_id] = room
        return room_id

    def join_multiplayer_room(self, room_id, player_name):
        """
        Rejoindre une salle multijoueur

        Args:
            room_id: ID de la salle
            player_name: Nom du joueur

        Returns:
            True si succès, False sinon
        """
        room = self.multiplayer_rooms.get(room_id)
        if not room:
            return False

        # Ne pas permettre de rejoindre une partie déjà terminée
        if room['finished']:
            return False

        # Vérifier si le joueur existe déjà
        if player_name in room['players']:
            return True  # Déjà dans la salle

        # Ajouter le joueur
        room['players'][player_name] = {
            'current_round': 0,
            'guesses': [],
            'scores': [],
            'total_score': 0,
            'finished': False
        }

        return True

    def start_multiplayer_game(self, room_id):
        """
        Démarrer une partie multijoueur

        Args:
            room_id: ID de la salle

        Returns:
            True si succès, False sinon
        """
        room = self.multiplayer_rooms.get(room_id)
        if not room or room['started']:
            return False

        room['started'] = True
        return True

    def get_multiplayer_room_info(self, room_id):
        """
        Récupérer les informations d'une salle

        Args:
            room_id: ID de la salle

        Returns:
            Dict avec les infos de la salle
        """
        room = self.multiplayer_rooms.get(room_id)
        if not room:
            return None

        # Retourner les infos sans les coordonnées GPS
        return {
            'id': room['id'],
            'name': room['name'],
            'host': room['host'],
            'num_rounds': room['num_rounds'],
            'started': room['started'],
            'finished': room['finished'],
            'players': [
                {
                    'name': name,
                    'total_score': player['total_score'],
                    'current_round': player['current_round'],
                    'finished': player['finished']
                }
                for name, player in room['players'].items()
            ]
        }

    def get_multiplayer_photo(self, room_id, player_name):
        """
        Récupère la photo actuelle pour un joueur dans une salle

        Args:
            room_id: ID de la salle
            player_name: Nom du joueur

        Returns:
            Dict avec les infos de la photo
        """
        room = self.multiplayer_rooms.get(room_id)
        if not room or not room['started']:
            return None

        player = room['players'].get(player_name)
        if not player or player['finished']:
            return None

        current_round = player['current_round']
        if current_round >= len(room['photos']):
            return None

        photo = room['photos'][current_round]

        return {
            'path': photo['path'],
            'round': current_round + 1,
            'total_rounds': room['num_rounds']
        }

    def submit_multiplayer_guess(self, room_id, player_name, guess_lat, guess_lon):
        """
        Soumettre une supposition dans une partie multijoueur

        Args:
            room_id: ID de la salle
            player_name: Nom du joueur
            guess_lat: Latitude devinée
            guess_lon: Longitude devinée

        Returns:
            Dict avec les résultats
        """
        room = self.multiplayer_rooms.get(room_id)
        if not room or not room['started']:
            return None

        player = room['players'].get(player_name)
        if not player or player['finished']:
            return None

        current_round = player['current_round']
        if current_round >= len(room['photos']):
            return None

        # Récupérer les vraies coordonnées
        photo = room['photos'][current_round]
        true_lat = photo['latitude']
        true_lon = photo['longitude']

        # Calculer la distance et le score
        true_coords = (true_lat, true_lon)
        guess_coords = (guess_lat, guess_lon)
        distance_km = geodesic(true_coords, guess_coords).kilometers
        score = self._calculate_score(distance_km)

        # Enregistrer la supposition
        guess_data = {
            'round': current_round + 1,
            'guess_lat': guess_lat,
            'guess_lon': guess_lon,
            'true_lat': true_lat,
            'true_lon': true_lon,
            'distance_km': round(distance_km, 2),
            'score': score
        }

        player['guesses'].append(guess_data)
        player['scores'].append(score)
        player['total_score'] += score
        player['current_round'] += 1

        # Vérifier si ce joueur a terminé
        if player['current_round'] >= room['num_rounds']:
            player['finished'] = True

        # Vérifier si tous les joueurs ont terminé
        all_finished = all(p['finished'] for p in room['players'].values())
        if all_finished:
            room['finished'] = True
            self._save_multiplayer_game_history(room)

        return guess_data

    def get_multiplayer_leaderboard(self, room_id):
        """
        Récupère le classement d'une salle multijoueur

        Args:
            room_id: ID de la salle

        Returns:
            Liste des joueurs triés par score
        """
        room = self.multiplayer_rooms.get(room_id)
        if not room:
            return []

        # Créer le classement
        leaderboard = []
        for name, player in room['players'].items():
            leaderboard.append({
                'player_name': name,
                'total_score': player['total_score'],
                'current_round': player['current_round'],
                'finished': player['finished']
            })

        # Trier par score décroissant
        leaderboard.sort(key=lambda x: x['total_score'], reverse=True)

        return leaderboard

    def _save_multiplayer_game_history(self, room):
        """
        Sauvegarde l'historique d'une partie multijoueur terminée

        Args:
            room: Données de la salle
        """
        # Charger l'historique existant
        games = []
        if os.path.exists(self.games_file):
            try:
                with open(self.games_file, 'r', encoding='utf-8') as f:
                    games = json.load(f)
            except:
                games = []

        # Ajouter chaque joueur à l'historique
        for player_name, player_data in room['players'].items():
            game_record = {
                'player_name': player_name,
                'date': room['created_at'],
                'total_score': player_data['total_score'],
                'num_rounds': room['num_rounds'],
                'average_score': round(player_data['total_score'] / room['num_rounds'], 2),
                'multiplayer': True,
                'room_name': room['name']
            }
            games.append(game_record)

        # Sauvegarder
        with open(self.games_file, 'w', encoding='utf-8') as f:
            json.dump(games, f, indent=2, ensure_ascii=False)
