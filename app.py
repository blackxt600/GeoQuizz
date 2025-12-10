"""
Serveur Flask principal pour GeoQuizz
"""
from flask import Flask, render_template, request, jsonify, send_file
import os
from photo_manager import PhotoManager
from game_manager import GameManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'geoquizz-secret-key-2024'

# Gestionnaires globaux
photo_manager = None
game_manager = GameManager()


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
            'num_photos_found': num_photos
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


if __name__ == '__main__':
    # Créer le dossier data s'il n'existe pas
    os.makedirs('data', exist_ok=True)

    # Lancer le serveur
    print("=" * 50)
    print("GeoQuizz - Serveur démarré")
    print("=" * 50)
    print("Accédez à l'application : http://localhost:5000")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=5000)
