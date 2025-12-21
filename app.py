"""
Serveur Flask principal pour GeoQuizz
"""
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import socket
import qrcode
from io import BytesIO
from photo_manager import PhotoManager
from game_manager import GameManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'geoquizz-secret-key-2024'

# Initialiser SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Gestionnaires globaux
photo_manager = None
game_manager = GameManager(socketio=socketio)


def get_local_ip():
    """
    Obtenir l'adresse IP locale du serveur (non-localhost)

    Returns:
        str: Adresse IP locale (ex: 192.168.1.66) ou localhost si non trouvée
    """
    try:
        # Méthode 1: Connexion UDP pour trouver l'IP locale
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # On se connecte à un serveur externe (pas besoin que la connexion aboutisse)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        try:
            # Méthode 2: Via le hostname
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            # Ne pas retourner 127.0.0.1
            if local_ip != '127.0.0.1':
                return local_ip
        except Exception:
            pass

    # Fallback à localhost si aucune méthode ne fonctionne
    return 'localhost'


@app.route('/')
def index():
    """Page principale de l'application"""
    return render_template('index.html')


@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """Gestion de la configuration"""
    if request.method == 'GET':
        # Récupérer la configuration actuelle
        config = game_manager.load_config()
        return jsonify(config if config else {})

    elif request.method == 'POST':
        # Sauvegarder une nouvelle configuration
        data = request.json
        photo_folder = data.get('photo_folder')
        num_rounds = data.get('num_rounds', 5)
        center_france = data.get('center_france', True)  # Par défaut activé

        if not photo_folder or not os.path.exists(photo_folder):
            return jsonify({'error': 'Dossier de photos invalide'}), 400

        # Scanner les photos
        global photo_manager
        photo_manager = PhotoManager(photo_folder)
        num_photos = photo_manager.scan_photos()

        if num_photos == 0:
            return jsonify({'error': 'Aucune photo avec coordonnées GPS trouvée'}), 400

        # Sauvegarder la config
        config = {
            'photo_folder': photo_folder,
            'num_rounds': num_rounds,
            'num_photos_found': num_photos,
            'center_france': center_france
        }
        game_manager.save_config(config)

        return jsonify({
            'success': True,
            'num_photos': num_photos,
            'config': config
        })


@app.route('/api/game/start', methods=['POST'])
def start_game():
    """Démarrer une nouvelle partie"""
    if photo_manager is None:
        return jsonify({'error': 'Configuration non initialisée'}), 400

    data = request.json
    player_name = data.get('player_name', 'Joueur')
    num_rounds = data.get('num_rounds', 5)

    # Récupérer des photos aléatoires
    photos = photo_manager.get_random_photos(num_rounds)

    if not photos:
        return jsonify({'error': 'Aucune photo disponible'}), 400

    # Créer la session de jeu
    session_id = game_manager.create_game(player_name, photos, num_rounds)

    return jsonify({
        'success': True,
        'session_id': session_id,
        'num_rounds': num_rounds
    })


@app.route('/api/game/<session_id>/photo', methods=['GET'])
def get_current_photo(session_id):
    """Récupérer la photo actuelle pour une session"""
    photo = game_manager.get_current_photo(session_id)

    if photo is None:
        return jsonify({'error': 'Session invalide ou terminée'}), 404

    return jsonify(photo)


@app.route('/api/game/<session_id>/guess', methods=['POST'])
def submit_guess(session_id):
    """Soumettre une supposition"""
    data = request.json
    guess_lat = data.get('latitude')
    guess_lon = data.get('longitude')

    if guess_lat is None or guess_lon is None:
        return jsonify({'error': 'Coordonnées manquantes'}), 400

    result = game_manager.submit_guess(session_id, guess_lat, guess_lon)

    if result is None:
        return jsonify({'error': 'Session invalide'}), 404

    return jsonify(result)


@app.route('/api/game/<session_id>/summary', methods=['GET'])
def get_game_summary(session_id):
    """Récupérer le résumé d'une partie"""
    summary = game_manager.get_session_summary(session_id)

    if summary is None:
        return jsonify({'error': 'Session introuvable'}), 404

    return jsonify(summary)


@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Récupérer le classement"""
    limit = request.args.get('limit', 10, type=int)
    leaderboard = game_manager.get_leaderboard(limit)
    return jsonify(leaderboard)


@app.route('/api/photo/<path:photo_path>')
def serve_photo(photo_path):
    """Servir une photo depuis le système de fichiers"""
    # Sécurité : vérifier que le fichier existe et est dans le dossier autorisé
    if not os.path.exists(photo_path):
        return jsonify({'error': 'Photo introuvable'}), 404

    return send_file(photo_path, mimetype='image/jpeg')


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Récupérer les statistiques générales"""
    config = game_manager.load_config()
    leaderboard = game_manager.get_leaderboard(1)

    stats = {
        'total_photos': config.get('num_photos_found', 0) if config else 0,
        'photo_folder': config.get('photo_folder', 'Non configuré') if config else 'Non configuré',
        'best_score': leaderboard[0]['total_score'] if leaderboard else 0,
        'best_player': leaderboard[0]['player_name'] if leaderboard else 'Aucun'
    }

    return jsonify(stats)


# ===== ENDPOINTS MULTIJOUEUR =====

@app.route('/api/multiplayer/room/create', methods=['POST'])
def create_multiplayer_room():
    """Créer une salle multijoueur"""
    if photo_manager is None:
        return jsonify({'error': 'Configuration non initialisée'}), 400

    data = request.json
    room_name = data.get('room_name', 'Salle')
    host_name = data.get('host_name', 'Hôte')
    num_rounds = data.get('num_rounds', 5)

    # Récupérer des photos aléatoires
    photos = photo_manager.get_random_photos(num_rounds)

    if not photos:
        return jsonify({'error': 'Aucune photo disponible'}), 400

    # Créer la salle
    room_id = game_manager.create_multiplayer_room(room_name, host_name, photos, num_rounds)

    return jsonify({
        'success': True,
        'room_id': room_id,
        'room_name': room_name
    })


@app.route('/api/multiplayer/room/<room_id>/join', methods=['POST'])
def join_multiplayer_room(room_id):
    """Rejoindre une salle multijoueur"""
    data = request.json
    player_name = data.get('player_name')

    if not player_name:
        return jsonify({'error': 'Nom du joueur requis'}), 400

    success = game_manager.join_multiplayer_room(room_id, player_name)

    if not success:
        return jsonify({'error': 'Impossible de rejoindre la salle'}), 404

    return jsonify({
        'success': True,
        'room_id': room_id,
        'player_name': player_name
    })


@app.route('/api/multiplayer/room/<room_id>/start', methods=['POST'])
def start_multiplayer_room(room_id):
    """Démarrer une partie multijoueur"""
    success = game_manager.start_multiplayer_game(room_id)

    if not success:
        return jsonify({'error': 'Impossible de démarrer la partie'}), 400

    return jsonify({'success': True})


@app.route('/api/multiplayer/room/<room_id>/info', methods=['GET'])
def get_multiplayer_room_info(room_id):
    """Récupérer les informations d'une salle"""
    info = game_manager.get_multiplayer_room_info(room_id)

    if info is None:
        return jsonify({'error': 'Salle introuvable'}), 404

    return jsonify(info)


@app.route('/api/multiplayer/room/<room_id>/photo', methods=['GET'])
def get_multiplayer_photo(room_id):
    """Récupérer la photo actuelle pour un joueur"""
    player_name = request.args.get('player_name')

    if not player_name:
        return jsonify({'error': 'Nom du joueur requis'}), 400

    photo = game_manager.get_multiplayer_photo(room_id, player_name)

    if photo is None:
        return jsonify({'error': 'Photo non disponible'}), 404

    return jsonify(photo)


@app.route('/api/multiplayer/room/<room_id>/guess', methods=['POST'])
def submit_multiplayer_guess(room_id):
    """Soumettre une supposition dans une partie multijoueur"""
    data = request.json
    player_name = data.get('player_name')
    guess_lat = data.get('latitude')
    guess_lon = data.get('longitude')

    if not player_name or guess_lat is None or guess_lon is None:
        return jsonify({'error': 'Données manquantes'}), 400

    result = game_manager.submit_multiplayer_guess(room_id, player_name, guess_lat, guess_lon)

    if result is None:
        return jsonify({'error': 'Erreur lors de la soumission'}), 404

    return jsonify(result)


@app.route('/api/multiplayer/room/<room_id>/leaderboard', methods=['GET'])
def get_multiplayer_leaderboard(room_id):
    """Récupérer le classement d'une salle"""
    leaderboard = game_manager.get_multiplayer_leaderboard(room_id)

    return jsonify(leaderboard)


@app.route('/api/multiplayer/room/<room_id>/qrcode', methods=['GET'])
def get_room_qrcode(room_id):
    """Générer un QR code pour rejoindre une salle multijoueur"""
    # Vérifier que la salle existe
    room_info = game_manager.get_synchronized_room_state(room_id)

    if room_info is None:
        return jsonify({'error': 'Salle introuvable'}), 404

    # Obtenir l'adresse IP locale du serveur
    local_ip = get_local_ip()
    port = request.host.split(':')[1] if ':' in request.host else '5000'

    # Générer l'URL de la salle avec l'IP locale
    join_url = f"http://{local_ip}:{port}/join/{room_id}"

    # Créer le QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(join_url)
    qr.make(fit=True)

    # Générer l'image
    img = qr.make_image(fill_color="black", back_color="white")

    # Convertir en bytes pour la réponse HTTP
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')


@app.route('/join/<room_id>')
def join_room_page(room_id):
    """Page pour rejoindre une salle directement via URL"""
    # Vérifier que la salle existe
    room_info = game_manager.get_synchronized_room_state(room_id)

    if room_info is None:
        # Rediriger vers la page d'accueil avec message d'erreur
        return render_template('index.html'), 404

    # Rendre la page principale avec le room_id en paramètre
    return render_template('index.html', room_id=room_id, room_name=room_info['name'])


@app.route('/api/multiplayer/room/<room_id>/exists', methods=['GET'])
def check_room_exists(room_id):
    """Vérifier si une salle existe"""
    room_info = game_manager.get_synchronized_room_state(room_id)

    if room_info is None:
        return jsonify({'exists': False}), 404

    return jsonify({
        'exists': True,
        'room_name': room_info['name'],
        'num_rounds': room_info['num_rounds'],
        'player_count': len(room_info['players']),
        'max_players': room_info['max_players'],
        'phase': room_info['phase']
    })


@app.route('/api/multiplayer/room/<room_id>/share-url', methods=['GET'])
def get_room_share_url(room_id):
    """Obtenir l'URL de partage pour rejoindre une salle (avec IP locale)"""
    # Vérifier que la salle existe
    room_info = game_manager.get_synchronized_room_state(room_id)

    if room_info is None:
        return jsonify({'error': 'Salle introuvable'}), 404

    # Obtenir l'adresse IP locale du serveur
    local_ip = get_local_ip()
    port = request.host.split(':')[1] if ':' in request.host else '5000'

    # Générer l'URL de partage
    join_url = f"http://{local_ip}:{port}/join/{room_id}"

    return jsonify({
        'url': join_url,
        'ip': local_ip,
        'port': port,
        'room_id': room_id
    })


# ===== ENDPOINTS MULTIJOUEUR SYNCHRONISÉ =====

@app.route('/api/sync/room/create', methods=['POST'])
def create_synchronized_room():
    """Créer une salle multijoueur synchronisée"""
    if photo_manager is None:
        return jsonify({'error': 'Configuration non initialisée'}), 400

    data = request.json
    room_name = data.get('room_name', 'Salle')
    host_name = data.get('host_name', 'Hôte')
    num_rounds = data.get('num_rounds', 5)

    # Récupérer des photos aléatoires
    photos = photo_manager.get_random_photos(num_rounds)

    if not photos:
        return jsonify({'error': 'Aucune photo disponible'}), 400

    # Créer la salle
    room_id = game_manager.create_synchronized_room(room_name, host_name, photos, num_rounds)

    return jsonify({
        'success': True,
        'room_id': room_id,
        'room_name': room_name
    })


@app.route('/api/sync/room/<room_id>/state', methods=['GET'])
def get_sync_room_state(room_id):
    """Récupérer l'état d'une salle synchronisée"""
    state = game_manager.get_synchronized_room_state(room_id)

    if state is None:
        return jsonify({'error': 'Salle introuvable'}), 404

    return jsonify(state)


# ===== ÉVÉNEMENTS WEBSOCKET =====

# Dictionnaire pour associer session IDs WebSocket aux room IDs et player names
socket_sessions = {}


@socketio.on('connect')
def handle_connect():
    """Gestion de la connexion WebSocket"""
    print(f'Client connecté: {request.sid}')
    emit('connected', {'message': 'Connexion établie'})


@socketio.on('disconnect')
def handle_disconnect():
    """Gestion de la déconnexion WebSocket"""
    sid = request.sid
    print(f'Client déconnecté: {sid}')

    # Récupérer les infos de session
    if sid in socket_sessions:
        room_id = socket_sessions[sid]['room_id']
        player_name = socket_sessions[sid]['player_name']

        # Gérer la déconnexion dans le game manager
        game_manager.handle_player_disconnect(room_id, player_name)

        # Supprimer la session
        del socket_sessions[sid]


@socketio.on('join_sync_room')
def handle_join_sync_room(data):
    """Rejoindre une salle synchronisée"""
    room_id = data.get('room_id')
    player_name = data.get('player_name')

    if not room_id or not player_name:
        emit('error', {'message': 'room_id et player_name requis'})
        return

    # Rejoindre la salle dans le game manager
    result = game_manager.join_synchronized_room(room_id, player_name)

    if result is None:
        emit('error', {'message': 'Salle introuvable'})
        return

    if 'error' in result:
        emit('error', {'message': result['error']})
        return

    # Rejoindre la room SocketIO
    join_room(room_id)

    # Enregistrer la session
    socket_sessions[request.sid] = {
        'room_id': room_id,
        'player_name': player_name
    }

    # Confirmer au joueur
    emit('joined_room', {
        'room_id': room_id,
        'player_name': player_name,
        'color': result['color'],
        'reconnected': result.get('reconnected', False)
    })

    # Broadcaster à tous les joueurs de la salle
    room_state = game_manager.get_synchronized_room_state(room_id)
    emit('room_updated', room_state, room=room_id)


@socketio.on('leave_sync_room')
def handle_leave_sync_room(data):
    """Quitter une salle synchronisée"""
    sid = request.sid

    if sid not in socket_sessions:
        emit('error', {'message': 'Session introuvable'})
        return

    room_id = socket_sessions[sid]['room_id']
    player_name = socket_sessions[sid]['player_name']

    # Quitter la room SocketIO
    leave_room(room_id)

    # Gérer la déconnexion
    game_manager.handle_player_disconnect(room_id, player_name)

    # Supprimer la session
    del socket_sessions[sid]

    # Broadcaster à tous
    room_state = game_manager.get_synchronized_room_state(room_id)
    emit('room_updated', room_state, room=room_id)

    # Confirmer au joueur
    emit('left_room', {'room_id': room_id})


@socketio.on('player_ready')
def handle_player_ready(data):
    """Marquer un joueur comme prêt"""
    sid = request.sid

    if sid not in socket_sessions:
        emit('error', {'message': 'Session introuvable'})
        return

    room_id = socket_sessions[sid]['room_id']
    player_name = socket_sessions[sid]['player_name']
    ready = data.get('ready', True)

    # Mettre à jour le statut
    game_manager.set_player_ready(room_id, player_name, ready)

    # Broadcaster l'état de la salle
    room_state = game_manager.get_synchronized_room_state(room_id)
    emit('room_updated', room_state, room=room_id)


@socketio.on('start_game')
def handle_start_game():
    """Démarrer le jeu (hôte seulement)"""
    sid = request.sid

    if sid not in socket_sessions:
        emit('error', {'message': 'Session introuvable'})
        return

    room_id = socket_sessions[sid]['room_id']

    # Démarrer le jeu
    success = game_manager.start_synchronized_game(room_id)

    if not success:
        emit('error', {'message': 'Impossible de démarrer - vérifier les conditions'})
        return

    # Broadcaster début du jeu
    emit('game_starting', {'message': 'La partie commence!'}, room=room_id)


@socketio.on('submit_sync_guess')
def handle_submit_sync_guess(data):
    """Soumettre une réponse synchronisée"""
    sid = request.sid

    if sid not in socket_sessions:
        emit('error', {'message': 'Session introuvable'})
        return

    room_id = socket_sessions[sid]['room_id']
    player_name = socket_sessions[sid]['player_name']
    guess_lat = data.get('latitude')
    guess_lon = data.get('longitude')

    if guess_lat is None or guess_lon is None:
        emit('error', {'message': 'Coordonnées manquantes'})
        return

    # Soumettre la réponse
    result = game_manager.submit_synchronized_guess(room_id, player_name, guess_lat, guess_lon)

    if result is None:
        emit('error', {'message': 'Erreur lors de la soumission'})
        return

    if 'error' in result:
        emit('error', {'message': result['error']})
        return

    # Confirmer au joueur
    emit('guess_submitted', {'success': True})

    # Note: player_submitted sera broadcaster automatiquement par game_manager


@socketio.on('next_round')
def handle_next_round():
    """Passer à la manche suivante"""
    sid = request.sid

    if sid not in socket_sessions:
        emit('error', {'message': 'Session introuvable'})
        return

    room_id = socket_sessions[sid]['room_id']

    # Avancer à la manche suivante
    game_manager.advance_to_next_round(room_id)


if __name__ == '__main__':
    # Créer le dossier data s'il n'existe pas
    os.makedirs('data', exist_ok=True)

    # Lancer le serveur
    print("=" * 50)
    print("GeoQuizz - Serveur démarré")
    print("=" * 50)
    print("Accédez à l'application : http://localhost:5000")
    print("Mode multijoueur temps réel activé")
    print("=" * 50)

    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
