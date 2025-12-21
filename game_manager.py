"""
Module de gestion du jeu et du scoring
"""
import json
import os
import uuid
import time
import threading
from datetime import datetime
from geopy.distance import geodesic

# Phases de jeu pour le mode synchronisé
GAME_PHASES = {
    'lobby': 'lobby',           # Attente joueurs
    'countdown': 'countdown',   # Compte à rebours avant manche
    'guessing': 'guessing',     # Joueurs devinent
    'results': 'results',       # Affichage résultats
    'between': 'between',       # Pause entre manches
    'paused': 'paused',         # Pause (déconnexion)
    'finished': 'finished'      # Partie terminée
}


class GameManager:
    def __init__(self, data_folder='data', socketio=None):
        """
        Initialise le gestionnaire de jeu

        Args:
            data_folder: Dossier où stocker les fichiers JSON
            socketio: Instance SocketIO pour communications temps réel
        """
        self.data_folder = data_folder
        self.sessions_file = os.path.join(data_folder, 'sessions.json')
        self.games_file = os.path.join(data_folder, 'games.json')
        self.config_file = os.path.join(data_folder, 'config.json')
        self.socketio = socketio

        # Sessions actives en mémoire (mode solo)
        self.active_sessions = {}

        # Salles multijoueurs asynchrones (ancien système)
        self.multiplayer_rooms = {}

        # Salles multijoueurs synchronisées (nouveau système temps réel)
        self.synchronized_rooms = {}

        # Threads de timer actifs
        self.active_timers = {}

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

    # ===== MÉTHODES MULTIJOUEUR SYNCHRONISÉ (TEMPS RÉEL) =====

    def create_synchronized_room(self, room_name, host_name, photos, num_rounds=5):
        """
        Crée une salle multijoueur synchronisée (temps réel)

        Args:
            room_name: Nom de la salle
            host_name: Nom de l'hôte
            photos: Liste des photos pour cette partie
            num_rounds: Nombre de manches

        Returns:
            ID de la salle
        """
        room_id = str(uuid.uuid4())[:8]  # ID court

        # Limiter au nombre de rounds
        game_photos = photos[:num_rounds]

        room = {
            'id': room_id,
            'name': room_name,
            'host': host_name,
            'created_at': datetime.now().isoformat(),
            'num_rounds': num_rounds,
            'current_round': 0,  # Partagé entre tous les joueurs
            'phase': GAME_PHASES['lobby'],
            'photos': game_photos,
            'timer_duration': 60,  # 60 secondes par manche
            'round_start_time': None,
            'players': {},  # {player_name: {color, ready, connected, guess, submitted, scores, total_score}}
            'max_players': 6,
            'player_colors': ['#ff4444', '#4444ff', '#ffaa00', '#aa00ff', '#00ffaa', '#ff66cc'],
            'disconnect_pause_duration': 30,  # 30 secondes de pause
            'pause_end_time': None
        }

        # Ajouter l'hôte comme premier joueur avec première couleur
        room['players'][host_name] = {
            'color': room['player_colors'][0],
            'ready': False,
            'connected': True,
            'guess': None,
            'submitted': False,
            'scores': [],
            'total_score': 0,
            'is_host': True
        }

        self.synchronized_rooms[room_id] = room
        return room_id

    def join_synchronized_room(self, room_id, player_name):
        """
        Rejoindre une salle synchronisée

        Args:
            room_id: ID de la salle
            player_name: Nom du joueur

        Returns:
            Dict avec status et color, ou None si erreur
        """
        room = self.synchronized_rooms.get(room_id)
        if not room:
            return None

        # Vérifier limite de joueurs
        if len(room['players']) >= room['max_players']:
            return {'error': 'Salle pleine'}

        # Vérifier si déjà dans la salle (reconnexion)
        if player_name in room['players']:
            room['players'][player_name]['connected'] = True
            return {
                'success': True,
                'color': room['players'][player_name]['color'],
                'reconnected': True
            }

        # Assigner couleur
        used_colors = [p['color'] for p in room['players'].values()]
        available_colors = [c for c in room['player_colors'] if c not in used_colors]

        if not available_colors:
            return {'error': 'Pas de couleur disponible'}

        # Ajouter le joueur
        room['players'][player_name] = {
            'color': available_colors[0],
            'ready': False,
            'connected': True,
            'guess': None,
            'submitted': False,
            'scores': [],
            'total_score': 0,
            'is_host': False
        }

        return {
            'success': True,
            'color': available_colors[0],
            'reconnected': False
        }

    def set_player_ready(self, room_id, player_name, ready=True):
        """
        Marque un joueur comme prêt

        Args:
            room_id: ID de la salle
            player_name: Nom du joueur
            ready: Statut prêt

        Returns:
            True si succès
        """
        room = self.synchronized_rooms.get(room_id)
        if not room or player_name not in room['players']:
            return False

        room['players'][player_name]['ready'] = ready
        return True

    def can_start_game(self, room_id):
        """
        Vérifie si la partie peut démarrer

        Args:
            room_id: ID de la salle

        Returns:
            True si au moins 2 joueurs prêts
        """
        room = self.synchronized_rooms.get(room_id)
        if not room:
            return False

        ready_count = sum(1 for p in room['players'].values() if p['ready'] and p['connected'])
        return ready_count >= 2

    def start_synchronized_game(self, room_id):
        """
        Démarre le jeu synchronisé (première manche)

        Args:
            room_id: ID de la salle

        Returns:
            True si succès
        """
        room = self.synchronized_rooms.get(room_id)
        if not room or not self.can_start_game(room_id):
            return False

        room['phase'] = GAME_PHASES['countdown']
        room['current_round'] = 0

        # Démarrer la première manche après un court délai
        if self.socketio:
            self.socketio.start_background_task(self._start_round_after_countdown, room_id, 3)

        return True

    def _start_round_after_countdown(self, room_id, countdown_seconds):
        """
        Démarre une manche après un compte à rebours

        Args:
            room_id: ID de la salle
            countdown_seconds: Durée du compte à rebours
        """
        room = self.synchronized_rooms.get(room_id)
        if not room:
            return

        # Compte à rebours
        for i in range(countdown_seconds, 0, -1):
            if self.socketio:
                self.socketio.emit('countdown_tick', {'seconds': i}, room=room_id)
            time.sleep(1)

        # Démarrer la manche
        self.start_round(room_id)

    def start_round(self, room_id):
        """
        Lance une nouvelle manche avec timer

        Args:
            room_id: ID de la salle
        """
        room = self.synchronized_rooms.get(room_id)
        if not room:
            return

        room['phase'] = GAME_PHASES['guessing']
        room['round_start_time'] = time.time()

        # Réinitialiser les soumissions
        for player in room['players'].values():
            player['guess'] = None
            player['submitted'] = False

        # Broadcaster début de manche
        if self.socketio:
            current_photo = room['photos'][room['current_round']]
            self.socketio.emit('round_started', {
                'round': room['current_round'] + 1,
                'total_rounds': room['num_rounds'],
                'photo_path': current_photo['path'],
                'timer_duration': room['timer_duration']
            }, room=room_id)

            # Démarrer le timer en background
            self.socketio.start_background_task(self._countdown_task, room_id)

    def _countdown_task(self, room_id):
        """
        Tâche de countdown (60 secondes)

        Args:
            room_id: ID de la salle
        """
        room = self.synchronized_rooms.get(room_id)
        if not room:
            return

        duration = room['timer_duration']

        for remaining in range(duration, -1, -1):
            # Vérifier si la salle existe toujours
            room = self.synchronized_rooms.get(room_id)
            if not room or room['phase'] != GAME_PHASES['guessing']:
                return

            # Broadcaster le temps restant
            if self.socketio:
                self.socketio.emit('timer_update', {'seconds': remaining}, room=room_id)

            time.sleep(1)

            # Vérifier si tous ont soumis (fin anticipée)
            if self.check_all_submitted(room_id):
                self.advance_to_results(room_id)
                return

        # Timer expiré - forcer passage aux résultats
        self.advance_to_results(room_id)

    def check_all_submitted(self, room_id):
        """
        Vérifie si tous les joueurs connectés ont soumis

        Args:
            room_id: ID de la salle

        Returns:
            True si tous ont soumis
        """
        room = self.synchronized_rooms.get(room_id)
        if not room:
            return False

        connected_players = [p for p in room['players'].values() if p['connected']]
        if not connected_players:
            return False

        return all(p['submitted'] for p in connected_players)

    def submit_synchronized_guess(self, room_id, player_name, guess_lat, guess_lon):
        """
        Soumet une réponse dans le mode synchronisé

        Args:
            room_id: ID de la salle
            player_name: Nom du joueur
            guess_lat: Latitude devinée
            guess_lon: Longitude devinée

        Returns:
            Dict avec status ou None
        """
        room = self.synchronized_rooms.get(room_id)
        if not room or player_name not in room['players']:
            return None

        if room['phase'] != GAME_PHASES['guessing']:
            return {'error': 'Pas en phase de jeu'}

        player = room['players'][player_name]
        if player['submitted']:
            return {'error': 'Déjà soumis'}

        # Enregistrer la réponse
        player['guess'] = {
            'lat': guess_lat,
            'lon': guess_lon,
            'timestamp': time.time()
        }
        player['submitted'] = True

        # Broadcaster que ce joueur a soumis
        if self.socketio:
            self.socketio.emit('player_submitted', {
                'player_name': player_name
            }, room=room_id)

        return {'success': True}

    def advance_to_results(self, room_id):
        """
        Passe à la phase résultats et calcule les scores

        Args:
            room_id: ID de la salle
        """
        room = self.synchronized_rooms.get(room_id)
        if not room:
            return

        room['phase'] = GAME_PHASES['results']

        # Récupérer photo actuelle
        current_photo = room['photos'][room['current_round']]
        true_lat = current_photo['latitude']
        true_lon = current_photo['longitude']

        # Calculer scores pour tous les joueurs
        results = []
        for player_name, player in room['players'].items():
            if player['submitted'] and player['guess']:
                guess_lat = player['guess']['lat']
                guess_lon = player['guess']['lon']

                # Calculer distance
                distance_km = geodesic(
                    (true_lat, true_lon),
                    (guess_lat, guess_lon)
                ).kilometers

                # Calculer score
                score = self._calculate_score(distance_km)

                player['scores'].append(score)
                player['total_score'] += score

                results.append({
                    'player_name': player_name,
                    'color': player['color'],
                    'guess_lat': guess_lat,
                    'guess_lon': guess_lon,
                    'distance_km': round(distance_km, 2),
                    'score': score,
                    'total_score': player['total_score']
                })
            else:
                # Joueur n'a pas soumis - 0 points
                player['scores'].append(0)
                results.append({
                    'player_name': player_name,
                    'color': player['color'],
                    'guess_lat': None,
                    'guess_lon': None,
                    'distance_km': None,
                    'score': 0,
                    'total_score': player['total_score']
                })

        # Trier par score de cette manche (décroissant)
        results.sort(key=lambda x: x['score'] if x['score'] is not None else -1, reverse=True)

        # Broadcaster les résultats
        if self.socketio:
            self.socketio.emit('round_results', {
                'results': results,
                'true_lat': true_lat,
                'true_lon': true_lon,
                'current_round': room['current_round'] + 1,
                'total_rounds': room['num_rounds']
            }, room=room_id)

    def advance_to_next_round(self, room_id):
        """
        Passe à la manche suivante ou termine le jeu

        Args:
            room_id: ID de la salle
        """
        room = self.synchronized_rooms.get(room_id)
        if not room:
            return

        room['current_round'] += 1

        if room['current_round'] >= room['num_rounds']:
            # Partie terminée
            room['phase'] = GAME_PHASES['finished']
            self._finalize_synchronized_game(room_id)
        else:
            # Prochaine manche
            room['phase'] = GAME_PHASES['between']
            # Démarrer la prochaine manche après un court délai
            if self.socketio:
                self.socketio.start_background_task(self._start_round_after_countdown, room_id, 5)

    def _finalize_synchronized_game(self, room_id):
        """
        Finalise une partie synchronisée terminée

        Args:
            room_id: ID de la salle
        """
        room = self.synchronized_rooms.get(room_id)
        if not room:
            return

        # Créer classement final
        final_scores = []
        for player_name, player in room['players'].items():
            final_scores.append({
                'player_name': player_name,
                'total_score': player['total_score'],
                'scores': player['scores']
            })

        final_scores.sort(key=lambda x: x['total_score'], reverse=True)

        # Broadcaster fin de partie
        if self.socketio:
            self.socketio.emit('game_finished', {
                'final_scores': final_scores
            }, room=room_id)

        # Sauvegarder dans l'historique
        self._save_synchronized_game_history(room)

    def _save_synchronized_game_history(self, room):
        """
        Sauvegarde l'historique d'une partie synchronisée

        Args:
            room: Données de la salle
        """
        games = []
        if os.path.exists(self.games_file):
            try:
                with open(self.games_file, 'r', encoding='utf-8') as f:
                    games = json.load(f)
            except:
                games = []

        # Ajouter chaque joueur
        for player_name, player_data in room['players'].items():
            game_record = {
                'player_name': player_name,
                'date': room['created_at'],
                'total_score': player_data['total_score'],
                'num_rounds': room['num_rounds'],
                'average_score': round(player_data['total_score'] / room['num_rounds'], 2),
                'multiplayer': True,
                'synchronized': True,
                'room_name': room['name']
            }
            games.append(game_record)

        with open(self.games_file, 'w', encoding='utf-8') as f:
            json.dump(games, f, indent=2, ensure_ascii=False)

    def handle_player_disconnect(self, room_id, player_name):
        """
        Gère la déconnexion d'un joueur (pause de 30s)

        Args:
            room_id: ID de la salle
            player_name: Nom du joueur
        """
        room = self.synchronized_rooms.get(room_id)
        if not room or player_name not in room['players']:
            return

        player = room['players'][player_name]
        player['connected'] = False
        player['disconnect_time'] = time.time()

        # Mettre en pause si en phase de jeu
        if room['phase'] == GAME_PHASES['guessing']:
            room['phase'] = GAME_PHASES['paused']
            room['pause_end_time'] = time.time() + room['disconnect_pause_duration']

            # Broadcaster pause
            if self.socketio:
                self.socketio.emit('game_paused', {
                    'player_name': player_name,
                    'pause_duration': room['disconnect_pause_duration']
                }, room=room_id)

                # Démarrer timer de pause
                self.socketio.start_background_task(
                    self._pause_countdown,
                    room_id,
                    player_name
                )

    def _pause_countdown(self, room_id, disconnected_player):
        """
        Compte à rebours de pause (30 secondes)

        Args:
            room_id: ID de la salle
            disconnected_player: Nom du joueur déconnecté
        """
        room = self.synchronized_rooms.get(room_id)
        if not room:
            return

        duration = room['disconnect_pause_duration']

        for remaining in range(duration, -1, -1):
            room = self.synchronized_rooms.get(room_id)
            if not room or room['phase'] != GAME_PHASES['paused']:
                return

            # Vérifier si le joueur s'est reconnecté
            if room['players'][disconnected_player]['connected']:
                # Reprendre le jeu
                self._resume_game(room_id)
                return

            # Broadcaster temps restant de pause
            if self.socketio:
                self.socketio.emit('pause_countdown', {'seconds': remaining}, room=room_id)

            time.sleep(1)

        # Pause expirée - continuer sans le joueur
        self._resume_game(room_id)

    def _resume_game(self, room_id):
        """
        Reprend le jeu après une pause

        Args:
            room_id: ID de la salle
        """
        room = self.synchronized_rooms.get(room_id)
        if not room:
            return

        room['phase'] = GAME_PHASES['guessing']

        # Broadcaster reprise
        if self.socketio:
            self.socketio.emit('game_resumed', {}, room=room_id)

            # Relancer le timer (temps restant)
            elapsed = time.time() - room['round_start_time']
            remaining = max(0, int(room['timer_duration'] - elapsed))

            if remaining > 0:
                self.socketio.start_background_task(
                    self._countdown_task_with_offset,
                    room_id,
                    remaining
                )
            else:
                # Timer déjà expiré - passer aux résultats
                self.advance_to_results(room_id)

    def _countdown_task_with_offset(self, room_id, start_seconds):
        """
        Tâche de countdown avec offset (pour reprise après pause)

        Args:
            room_id: ID de la salle
            start_seconds: Secondes restantes
        """
        room = self.synchronized_rooms.get(room_id)
        if not room:
            return

        for remaining in range(start_seconds, -1, -1):
            room = self.synchronized_rooms.get(room_id)
            if not room or room['phase'] != GAME_PHASES['guessing']:
                return

            if self.socketio:
                self.socketio.emit('timer_update', {'seconds': remaining}, room=room_id)

            time.sleep(1)

            if self.check_all_submitted(room_id):
                self.advance_to_results(room_id)
                return

        self.advance_to_results(room_id)

    def get_synchronized_room_state(self, room_id):
        """
        Récupère l'état complet d'une salle synchronisée

        Args:
            room_id: ID de la salle

        Returns:
            Dict avec l'état de la salle
        """
        room = self.synchronized_rooms.get(room_id)
        if not room:
            return None

        # Préparer liste des joueurs
        players_list = []
        for name, data in room['players'].items():
            players_list.append({
                'name': name,
                'color': data['color'],
                'ready': data['ready'],
                'connected': data['connected'],
                'submitted': data['submitted'],
                'total_score': data['total_score'],
                'is_host': data.get('is_host', False)
            })

        return {
            'id': room['id'],
            'name': room['name'],
            'host': room['host'],
            'phase': room['phase'],
            'current_round': room['current_round'],
            'num_rounds': room['num_rounds'],
            'players': players_list,
            'max_players': room['max_players']
        }
