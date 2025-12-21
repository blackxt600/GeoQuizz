/**
 * Application GeoQuizz - JavaScript principal
 */

// Variables globales
let currentSessionId = null;
let playerName = '';
let gameMap = null;
let resultMap = null;
let multiplayerResultMap = null;
let guessMarker = null;
let currentGuessCoords = null;

// Variables multijoueur
let socket = null;
let isMultiplayerMode = false;
let currentRoomId = null;
let playerColor = null;
let isHost = false;
let isReady = false;

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    initConfigScreen();
    initWebSocket();
    loadStats();
    checkAutoJoinRoom();
});

/**
 * Initialisation de l'écran de configuration
 */
function initConfigScreen() {
    // Bouton scanner les photos
    document.getElementById('btn-scan-photos').addEventListener('click', scanPhotos);

    // Bouton démarrer la partie solo
    document.getElementById('btn-start-game').addEventListener('click', startGame);

    // Boutons multijoueur
    document.getElementById('btn-create-multiplayer').addEventListener('click', createMultiplayerRoom);
    document.getElementById('btn-join-multiplayer').addEventListener('click', promptJoinRoom);

    // Boutons lobby
    document.getElementById('btn-ready').addEventListener('click', toggleReady);
    document.getElementById('btn-start-multiplayer').addEventListener('click', startMultiplayerGame);
    document.getElementById('btn-leave-lobby').addEventListener('click', leaveLobby);
    document.getElementById('btn-copy-code').addEventListener('click', copyRoomCode);
    document.getElementById('btn-copy-url').addEventListener('click', copyRoomURL);

    // Bouton valider la réponse
    document.getElementById('btn-submit-guess').addEventListener('click', submitGuess);

    // Bouton manche suivante
    document.getElementById('btn-next-round').addEventListener('click', nextRound);
    document.getElementById('btn-next-multiplayer-round').addEventListener('click', nextMultiplayerRound);

    // Bouton nouvelle partie
    document.getElementById('btn-new-game').addEventListener('click', newGame);

    // Bouton changer de configuration
    document.getElementById('btn-change-config').addEventListener('click', changeConfig);
}

/**
 * Scanner les photos du dossier sélectionné
 */
async function scanPhotos() {
    const photoFolder = document.getElementById('photo-folder').value.trim();
    const numRounds = parseInt(document.getElementById('num-rounds').value);

    if (!photoFolder) {
        showError('Veuillez entrer un chemin de dossier');
        return;
    }

    // Afficher un message de chargement
    const btn = document.getElementById('btn-scan-photos');
    btn.textContent = 'Scan en cours...';
    btn.disabled = true;

    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                photo_folder: photoFolder,
                num_rounds: numRounds
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Afficher le résultat
            const resultDiv = document.getElementById('scan-result');
            const successP = resultDiv.querySelector('.success');
            successP.textContent = `${data.num_photos} photo(s) avec coordonnées GPS trouvée(s) !`;
            resultDiv.classList.remove('hidden');

            document.getElementById('scan-error').classList.add('hidden');
        } else {
            showError(data.error || 'Erreur lors du scan');
        }
    } catch (error) {
        showError('Erreur de connexion au serveur');
    } finally {
        btn.textContent = 'Scanner les photos';
        btn.disabled = false;
    }
}

/**
 * Démarrer une nouvelle partie
 */
async function startGame() {
    playerName = document.getElementById('player-name').value.trim() || 'Joueur 1';
    const numRounds = parseInt(document.getElementById('num-rounds').value);

    const btn = document.getElementById('btn-start-game');
    btn.textContent = 'Démarrage...';
    btn.disabled = true;

    try {
        const response = await fetch('/api/game/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                player_name: playerName,
                num_rounds: numRounds
            })
        });

        const data = await response.json();

        if (response.ok) {
            currentSessionId = data.session_id;
            showGameScreen();
            loadCurrentPhoto();
        } else {
            showError(data.error || 'Erreur lors du démarrage');
        }
    } catch (error) {
        showError('Erreur de connexion au serveur');
    } finally {
        btn.textContent = 'Démarrer la partie';
        btn.disabled = false;
    }
}

/**
 * Afficher l'écran de jeu
 */
function showGameScreen() {
    hideAllScreens();
    document.getElementById('game-screen').classList.add('active');
    document.getElementById('player-display').textContent = playerName;

    // Initialiser la carte si pas déjà fait
    if (!gameMap) {
        initGameMap();
    }
}

/**
 * Initialiser la carte de jeu
 */
function initGameMap() {
    gameMap = L.map('map').setView([48.8566, 2.3522], 2);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(gameMap);

    // Clic sur la carte pour placer le marqueur
    gameMap.on('click', function(e) {
        placeGuessMarker(e.latlng);
    });
}

/**
 * Placer le marqueur de supposition
 */
function placeGuessMarker(latlng) {
    // Supprimer le marqueur existant
    if (guessMarker) {
        gameMap.removeLayer(guessMarker);
    }

    // Créer un nouveau marqueur
    guessMarker = L.marker(latlng, {
        icon: L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        })
    }).addTo(gameMap);

    currentGuessCoords = latlng;

    // Activer le bouton de validation
    document.getElementById('btn-submit-guess').disabled = false;
}

/**
 * Charger la photo actuelle
 */
async function loadCurrentPhoto() {
    try {
        const response = await fetch(`/api/game/${currentSessionId}/photo`);
        const data = await response.json();

        if (response.ok) {
            // Afficher la photo
            const photoPath = data.path.replace(/\\/g, '/');
            document.getElementById('current-photo').src = `/api/photo/${encodeURIComponent(photoPath)}`;

            // Mettre à jour l'affichage de la manche
            document.getElementById('round-display').textContent = `Manche ${data.round}/${data.total_rounds}`;

            // Réinitialiser la carte
            if (guessMarker) {
                gameMap.removeLayer(guessMarker);
                guessMarker = null;
            }
            currentGuessCoords = null;
            document.getElementById('btn-submit-guess').disabled = true;
            gameMap.setView([48.8566, 2.3522], 2);
        } else {
            showError(data.error || 'Erreur lors du chargement de la photo');
        }
    } catch (error) {
        showError('Erreur de connexion au serveur');
    }
}

/**
 * Soumettre la supposition
 */
async function submitGuess() {
    if (!currentGuessCoords) {
        alert('Veuillez placer un marqueur sur la carte');
        return;
    }

    const btn = document.getElementById('btn-submit-guess');
    btn.textContent = 'Validation...';
    btn.disabled = true;

    try {
        const response = await fetch(`/api/game/${currentSessionId}/guess`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                latitude: currentGuessCoords.lat,
                longitude: currentGuessCoords.lng
            })
        });

        const data = await response.json();

        if (response.ok) {
            showResultScreen(data);
        } else {
            showError(data.error || 'Erreur lors de la soumission');
        }
    } catch (error) {
        showError('Erreur de connexion au serveur');
    } finally {
        btn.textContent = 'Valider ma réponse';
    }
}

/**
 * Afficher l'écran de résultat
 */
function showResultScreen(result) {
    hideAllScreens();
    document.getElementById('result-screen').classList.add('active');

    // Afficher les détails
    document.getElementById('result-distance').textContent = `${result.distance_km.toFixed(2)} km`;
    document.getElementById('result-score').textContent = `${result.score} points`;

    // Récupérer le score total actuel
    fetch(`/api/game/${currentSessionId}/summary`)
        .then(res => res.json())
        .then(summary => {
            document.getElementById('result-total-score').textContent = `${summary.total_score} points`;
            document.getElementById('score-display').textContent = `Score: ${summary.total_score}`;
        });

    // Initialiser la carte de résultat
    initResultMap(result);
}

/**
 * Initialiser la carte de résultat
 */
function initResultMap(result) {
    // Supprimer la carte existante
    if (resultMap) {
        resultMap.remove();
    }

    resultMap = L.map('result-map').setView([result.true_lat, result.true_lon], 5);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(resultMap);

    // Marqueur rouge pour la supposition
    L.marker([result.guess_lat, result.guess_lon], {
        icon: L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        })
    }).addTo(resultMap).bindPopup('Votre réponse');

    // Marqueur vert pour la vraie position
    L.marker([result.true_lat, result.true_lon], {
        icon: L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        })
    }).addTo(resultMap).bindPopup('Position réelle');

    // Ligne entre les deux
    L.polyline([
        [result.guess_lat, result.guess_lon],
        [result.true_lat, result.true_lon]
    ], {
        color: 'blue',
        weight: 3,
        dashArray: '5, 10'
    }).addTo(resultMap);

    // Ajuster la vue pour voir les deux marqueurs
    const bounds = L.latLngBounds(
        [result.guess_lat, result.guess_lon],
        [result.true_lat, result.true_lon]
    );
    resultMap.fitBounds(bounds, { padding: [50, 50] });
}

/**
 * Passer à la manche suivante
 */
async function nextRound() {
    try {
        const response = await fetch(`/api/game/${currentSessionId}/summary`);
        const summary = await response.json();

        if (summary.finished) {
            showEndScreen();
        } else {
            showGameScreen();
            loadCurrentPhoto();
        }
    } catch (error) {
        showError('Erreur de connexion au serveur');
    }
}

/**
 * Afficher l'écran de fin
 */
async function showEndScreen() {
    hideAllScreens();
    document.getElementById('end-screen').classList.add('active');

    try {
        const response = await fetch(`/api/game/${currentSessionId}/summary`);
        const summary = await response.json();

        // Afficher le score final
        document.getElementById('final-score').textContent = summary.total_score;
        document.getElementById('final-player-name').textContent = summary.player_name;

        // Afficher le récapitulatif
        const summaryContent = document.getElementById('summary-content');
        summaryContent.innerHTML = summary.guesses.map(guess => `
            <div class="summary-round">
                <strong>Manche ${guess.round}:</strong> ${guess.score} points (${guess.distance_km} km)
            </div>
        `).join('');

        // Charger et afficher le classement
        loadLeaderboard();
    } catch (error) {
        showError('Erreur lors du chargement du résumé');
    }
}

/**
 * Charger le classement
 */
async function loadLeaderboard() {
    try {
        const response = await fetch('/api/leaderboard?limit=10');
        const leaderboard = await response.json();

        const leaderboardContent = document.getElementById('leaderboard-content');

        if (leaderboard.length === 0) {
            leaderboardContent.innerHTML = '<p>Aucune partie enregistrée</p>';
            return;
        }

        leaderboardContent.innerHTML = leaderboard.map((game, index) => `
            <div class="leaderboard-item">
                <span>${index + 1}. ${game.player_name}</span>
                <span><strong>${game.total_score}</strong> points (${game.num_rounds} manches)</span>
            </div>
        `).join('');
    } catch (error) {
        console.error('Erreur lors du chargement du classement:', error);
    }
}

/**
 * Charger les statistiques
 */
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        const statsContent = document.getElementById('stats-content');
        statsContent.innerHTML = `
            <p><strong>Dossier:</strong> ${stats.photo_folder}</p>
            <p><strong>Photos disponibles:</strong> ${stats.total_photos}</p>
            <p><strong>Meilleur score:</strong> ${stats.best_score} (${stats.best_player})</p>
        `;
    } catch (error) {
        console.error('Erreur lors du chargement des stats:', error);
    }
}

/**
 * Nouvelle partie
 */
function newGame() {
    currentSessionId = null;
    startGame();
}

/**
 * Changer de configuration
 */
function changeConfig() {
    currentSessionId = null;
    hideAllScreens();
    document.getElementById('config-screen').classList.add('active');
    loadStats();
}

/**
 * Masquer tous les écrans
 */
function hideAllScreens() {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
}

/**
 * Afficher une erreur
 */
function showError(message) {
    const errorDiv = document.getElementById('scan-error');
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
    document.getElementById('scan-result').classList.add('hidden');
}

// ===== FONCTIONS MULTIJOUEUR =====

/**
 * Initialiser WebSocket
 */
function initWebSocket() {
    socket = io();

    socket.on('connected', (data) => {
        console.log('WebSocket connecté:', data.message);
    });

    socket.on('error', (data) => {
        console.error('Erreur WebSocket:', data.message);
        showError(data.message);
    });

    socket.on('joined_room', handleJoinedRoom);
    socket.on('room_updated', handleRoomUpdated);
    socket.on('countdown_tick', handleCountdownTick);
    socket.on('round_started', handleRoundStarted);
    socket.on('timer_update', handleTimerUpdate);
    socket.on('player_submitted', handlePlayerSubmitted);
    socket.on('round_results', handleRoundResults);
    socket.on('game_finished', handleGameFinished);
    socket.on('game_paused', handleGamePaused);
    socket.on('pause_countdown', handlePauseCountdown);
    socket.on('game_resumed', handleGameResumed);
}

/**
 * Créer une salle multijoueur
 */
async function createMultiplayerRoom() {
    playerName = document.getElementById('player-name').value.trim() || 'Joueur 1';
    const numRounds = parseInt(document.getElementById('num-rounds').value);

    try {
        const response = await fetch('/api/sync/room/create', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                room_name: `Partie de ${playerName}`,
                host_name: playerName,
                num_rounds: numRounds
            })
        });

        const data = await response.json();

        if (response.ok) {
            currentRoomId = data.room_id;
            isMultiplayerMode = true;
            isHost = true;

            // Rejoindre via WebSocket
            socket.emit('join_sync_room', {
                room_id: currentRoomId,
                player_name: playerName
            });
        } else {
            showError(data.error || 'Erreur lors de la création');
        }
    } catch (error) {
        showError('Erreur de connexion');
    }
}

/**
 * Demander le code de salle et rejoindre
 */
function promptJoinRoom() {
    const roomCode = prompt('Entrez le code de la salle :');
    if (roomCode) {
        joinRoom(roomCode.trim());
    }
}

/**
 * Rejoindre une salle
 */
function joinRoom(roomId) {
    playerName = document.getElementById('player-name').value.trim() || 'Joueur 1';
    currentRoomId = roomId;
    isMultiplayerMode = true;
    isHost = false;

    socket.emit('join_sync_room', {
        room_id: roomId,
        player_name: playerName
    });
}

/**
 * Gérer l'événement de salle rejointe
 */
function handleJoinedRoom(data) {
    playerColor = data.color;

    // Afficher le lobby
    hideAllScreens();
    document.getElementById('lobby-screen').classList.add('active');

    // Afficher le code de salle
    document.getElementById('lobby-room-code').textContent = data.room_id;
    document.getElementById('lobby-num-rounds').textContent = document.getElementById('num-rounds').value;

    // Charger le QR code
    loadQRCode(data.room_id);
}

/**
 * Gérer la mise à jour de la salle
 */
function handleRoomUpdated(roomState) {
    // Mettre à jour la liste des joueurs
    const container = document.getElementById('lobby-players-container');
    container.innerHTML = '';

    roomState.players.forEach(player => {
        const playerDiv = document.createElement('div');
        playerDiv.className = 'lobby-player-item';
        playerDiv.style.borderLeft = `4px solid ${player.color}`;

        const statusIcon = player.ready ? '✓' : '⏳';
        const hostBadge = player.is_host ? ' (Hôte)' : '';

        playerDiv.innerHTML = `
            <span class="player-name">${player.name}${hostBadge}</span>
            <span class="player-status">${statusIcon}</span>
        `;

        container.appendChild(playerDiv);
    });

    // Mettre à jour le compteur
    document.getElementById('lobby-player-count').textContent = roomState.players.length;

    // Activer le bouton démarrer si hôte et conditions remplies
    if (isHost) {
        const readyCount = roomState.players.filter(p => p.ready).length;
        const canStart = readyCount >= 2;
        document.getElementById('btn-start-multiplayer').disabled = !canStart;
    }
}

/**
 * Basculer l'état prêt
 */
function toggleReady() {
    isReady = !isReady;
    socket.emit('player_ready', {ready: isReady});

    const btn = document.getElementById('btn-ready');
    btn.textContent = isReady ? 'Pas prêt' : 'Prêt';
    btn.classList.toggle('btn-success', isReady);
}

/**
 * Démarrer le jeu multijoueur
 */
function startMultiplayerGame() {
    socket.emit('start_game');
}

/**
 * Quitter le lobby
 */
function leaveLobby() {
    socket.emit('leave_sync_room', {});
    isMultiplayerMode = false;
    currentRoomId = null;
    isHost = false;
    isReady = false;

    hideAllScreens();
    document.getElementById('config-screen').classList.add('active');
}

/**
 * Copier le code de salle
 */
function copyRoomCode() {
    const code = document.getElementById('lobby-room-code').textContent;
    navigator.clipboard.writeText(code).then(() => {
        const btn = document.getElementById('btn-copy-code');
        const originalText = btn.textContent;
        btn.textContent = 'Copié !';
        setTimeout(() => btn.textContent = originalText, 2000);
    });
}

/**
 * Gérer le compte à rebours avant manche
 */
function handleCountdownTick(data) {
    hideAllScreens();
    const screen = document.createElement('div');
    screen.id = 'countdown-screen';
    screen.className = 'screen active';
    screen.innerHTML = `
        <div class="container">
            <h1>La manche commence dans</h1>
            <div class="countdown-number">${data.seconds}</div>
        </div>
    `;
    document.body.appendChild(screen);

    setTimeout(() => {
        if (document.getElementById('countdown-screen')) {
            document.getElementById('countdown-screen').remove();
        }
    }, 1000);
}

/**
 * Gérer le démarrage d'une manche
 */
function handleRoundStarted(data) {
    hideAllScreens();
    document.getElementById('game-screen').classList.add('active');

    // Afficher timer et statuts pour multijoueur
    document.getElementById('timer-container').classList.remove('hidden');
    document.getElementById('players-status-container').classList.remove('hidden');

    // Masquer info solo
    document.querySelector('.game-info').style.display = 'none';

    // Initialiser la carte si pas déjà fait (IMPORTANT: avant d'utiliser gameMap)
    if (!gameMap) {
        initGameMap();
    }

    // Charger la photo
    document.getElementById('current-photo').src = `/api/photo/${data.photo_path}`;
    document.getElementById('round-display').textContent = `Manche ${data.round}/${data.total_rounds}`;

    // Réinitialiser la carte
    if (guessMarker) {
        gameMap.removeLayer(guessMarker);
        guessMarker = null;
    }
    currentGuessCoords = null;
    gameMap.setView([48.8566, 2.3522], 2);

    // Forcer le redimensionnement de la carte (important pour Leaflet)
    setTimeout(() => {
        if (gameMap) {
            gameMap.invalidateSize();
        }
    }, 100);

    // Réinitialiser le bouton
    document.getElementById('btn-submit-guess').disabled = true;
    document.getElementById('btn-submit-guess').textContent = 'Valider ma réponse';
    document.getElementById('waiting-message').classList.add('hidden');
}

/**
 * Gérer la mise à jour du timer
 */
function handleTimerUpdate(data) {
    const minutes = Math.floor(data.seconds / 60);
    const secs = data.seconds % 60;
    const timerDisplay = document.getElementById('timer-display');
    timerDisplay.textContent = `${minutes}:${String(secs).padStart(2, '0')}`;

    // Alerte visuelle si < 10s
    if (data.seconds <= 10) {
        timerDisplay.classList.add('danger');
    } else {
        timerDisplay.classList.remove('danger');
    }

    // Désactiver soumission si timer à 0
    if (data.seconds <= 0) {
        document.getElementById('btn-submit-guess').disabled = true;
        document.getElementById('btn-submit-guess').textContent = 'Temps écoulé';
    }
}

/**
 * Gérer la soumission d'un joueur
 */
function handlePlayerSubmitted(data) {
    console.log(`${data.player_name} a soumis sa réponse`);
    // Mettre à jour l'UI si nécessaire
}

/**
 * Soumettre une réponse (modifiée pour multijoueur)
 */
async function submitGuess() {
    if (!currentGuessCoords) return;

    const btn = document.getElementById('btn-submit-guess');
    btn.disabled = true;

    if (isMultiplayerMode) {
        // Mode multijoueur
        socket.emit('submit_sync_guess', {
            latitude: currentGuessCoords.lat,
            longitude: currentGuessCoords.lng
        });

        btn.textContent = 'Réponse envoyée';
        document.getElementById('waiting-message').classList.remove('hidden');
    } else {
        // Mode solo (code existant)
        try {
            const response = await fetch(`/api/game/${currentSessionId}/guess`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    latitude: currentGuessCoords.lat,
                    longitude: currentGuessCoords.lng
                })
            });

            const data = await response.json();

            if (response.ok) {
                showResultScreen(data);
            } else {
                showError(data.error || 'Erreur');
                btn.disabled = false;
            }
        } catch (error) {
            showError('Erreur de connexion');
            btn.disabled = false;
        }
    }
}

/**
 * Gérer les résultats de manche (multijoueur)
 */
function handleRoundResults(data) {
    hideAllScreens();
    document.getElementById('multiplayer-result-screen').classList.add('active');

    // Remplir le tableau
    const tbody = document.getElementById('multiplayer-results-tbody');
    tbody.innerHTML = '';

    data.results.forEach((result, index) => {
        const row = document.createElement('tr');
        if (index === 0) row.classList.add('first-place');

        const distanceText = result.distance_km !== null ? `${result.distance_km} km` : 'Pas de réponse';
        const scoreText = result.score !== null ? result.score : 0;

        row.innerHTML = `
            <td>${index + 1}</td>
            <td><span class="color-dot" style="background: ${result.color}"></span> ${result.player_name}</td>
            <td>${distanceText}</td>
            <td>${scoreText}</td>
            <td>${result.total_score}</td>
        `;

        tbody.appendChild(row);
    });

    // Afficher la carte avec tous les marqueurs
    displayMultiplayerResultMap(data.results, data.true_lat, data.true_lon);
}

/**
 * Afficher la carte de résultats multijoueur
 */
function displayMultiplayerResultMap(results, trueLat, trueLon) {
    // Supprimer l'ancienne carte
    if (multiplayerResultMap) {
        multiplayerResultMap.remove();
    }

    // Créer nouvelle carte
    multiplayerResultMap = L.map('multiplayer-result-map').setView([trueLat, trueLon], 4);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(multiplayerResultMap);

    const bounds = L.latLngBounds();

    // Ajouter marqueur de chaque joueur
    results.forEach(result => {
        if (result.guess_lat && result.guess_lon) {
            const marker = L.marker([result.guess_lat, result.guess_lon], {
                icon: L.divIcon({
                    className: 'custom-marker',
                    html: `<div style="background: ${result.color}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>`
                })
            }).addTo(multiplayerResultMap);

            marker.bindPopup(`
                <b>${result.player_name}</b><br>
                Distance: ${result.distance_km} km<br>
                Score: ${result.score}
            `);

            bounds.extend([result.guess_lat, result.guess_lon]);

            // Ligne vers position réelle
            L.polyline(
                [[result.guess_lat, result.guess_lon], [trueLat, trueLon]],
                {color: result.color, dashArray: '5, 10', weight: 2}
            ).addTo(multiplayerResultMap);
        }
    });

    // Marqueur position réelle
    L.marker([trueLat, trueLon], {
        icon: L.divIcon({
            className: 'custom-marker',
            html: '<div style="background: #00ff00; width: 25px; height: 25px; border-radius: 50%; border: 3px solid white;"></div>'
        })
    }).addTo(multiplayerResultMap).bindPopup('<b>Position réelle</b>');

    bounds.extend([trueLat, trueLon]);
    multiplayerResultMap.fitBounds(bounds, {padding: [50, 50]});
}

/**
 * Passer à la manche suivante (multijoueur)
 */
function nextMultiplayerRound() {
    socket.emit('next_round');
}

/**
 * Gérer la fin de partie
 */
function handleGameFinished(data) {
    hideAllScreens();
    document.getElementById('end-screen').classList.add('active');

    // Afficher les scores finaux
    const summaryDiv = document.getElementById('summary-content');
    summaryDiv.innerHTML = '<h3>Classement final</h3>';

    const table = document.createElement('table');
    table.className = 'leaderboard-table';
    table.innerHTML = `
        <thead>
            <tr>
                <th>Rang</th>
                <th>Joueur</th>
                <th>Score Total</th>
            </tr>
        </thead>
        <tbody>
            ${data.final_scores.map((player, index) => `
                <tr ${index === 0 ? 'class="first-place"' : ''}>
                    <td>${index + 1}</td>
                    <td>${player.player_name}</td>
                    <td>${player.total_score}</td>
                </tr>
            `).join('')}
        </tbody>
    `;

    summaryDiv.appendChild(table);

    document.getElementById('final-score').textContent = data.final_scores[0]?.total_score || 0;
    document.getElementById('final-player-name').textContent = `Gagnant: ${data.final_scores[0]?.player_name || ''}`;
}

/**
 * Gérer la pause du jeu
 */
function handleGamePaused(data) {
    const statusDiv = document.createElement('div');
    statusDiv.id = 'pause-overlay';
    statusDiv.className = 'pause-overlay';
    statusDiv.innerHTML = `
        <div class="pause-message">
            <h2>Partie en pause</h2>
            <p>${data.player_name} s'est déconnecté</p>
            <p>Reprise dans <span id="pause-timer">${data.pause_duration}</span> secondes...</p>
        </div>
    `;
    document.body.appendChild(statusDiv);
}

/**
 * Gérer le compte à rebours de pause
 */
function handlePauseCountdown(data) {
    const timer = document.getElementById('pause-timer');
    if (timer) {
        timer.textContent = data.seconds;
    }
}

/**
 * Gérer la reprise du jeu
 */
function handleGameResumed() {
    const overlay = document.getElementById('pause-overlay');
    if (overlay) {
        overlay.remove();
    }
}

/**
 * Vérifier si on doit auto-rejoindre une salle (via URL /join/<room_id>)
 */
function checkAutoJoinRoom() {
    // Récupérer le room_id depuis l'URL
    const path = window.location.pathname;
    const match = path.match(/^\/join\/([a-zA-Z0-9]+)$/);

    if (match) {
        const roomId = match[1];
        console.log('Auto-join room:', roomId);

        // Demander le nom du joueur
        const name = prompt('Entrez votre nom pour rejoindre la partie :');
        if (name && name.trim()) {
            playerName = name.trim();
            document.getElementById('player-name').value = playerName;
            joinRoom(roomId);
        } else {
            // Rediriger vers la page d'accueil si annulé
            window.history.pushState({}, '', '/');
        }
    }
}

/**
 * Charger le QR code de la salle et l'URL de partage
 */
async function loadQRCode(roomId) {
    const qrImage = document.getElementById('qr-code-image');
    qrImage.src = `/api/multiplayer/room/${roomId}/qrcode`;
    qrImage.style.display = 'block';

    // Charger et afficher l'URL de partage
    try {
        const response = await fetch(`/api/multiplayer/room/${roomId}/share-url`);
        const data = await response.json();

        if (response.ok) {
            const urlText = document.getElementById('share-url-text');
            urlText.textContent = data.url;
        }
    } catch (error) {
        console.error('Erreur lors du chargement de l\'URL de partage:', error);
    }
}

/**
 * Copier l'URL de la salle
 */
async function copyRoomURL() {
    const roomId = currentRoomId;

    try {
        // Récupérer l'URL de partage avec l'IP locale depuis le serveur
        const response = await fetch(`/api/multiplayer/room/${roomId}/share-url`);
        const data = await response.json();

        if (response.ok) {
            const url = data.url;

            navigator.clipboard.writeText(url).then(() => {
                const btn = document.getElementById('btn-copy-url');
                const originalText = btn.textContent;
                btn.textContent = 'Lien copié !';
                setTimeout(() => btn.textContent = originalText, 2000);
            }).catch(err => {
                console.error('Erreur lors de la copie:', err);
                // Fallback pour les navigateurs qui ne supportent pas clipboard API
                alert('Copiez ce lien : ' + url);
            });
        } else {
            // Fallback si l'API échoue
            const url = `${window.location.origin}/join/${roomId}`;
            alert('Copiez ce lien : ' + url);
        }
    } catch (error) {
        console.error('Erreur lors de la récupération de l\'URL:', error);
        // Fallback
        const url = `${window.location.origin}/join/${roomId}`;
        alert('Copiez ce lien : ' + url);
    }
}
