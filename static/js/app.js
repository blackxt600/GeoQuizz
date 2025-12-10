/**
 * Application GeoQuizz - JavaScript principal
 */

// Variables globales
let currentSessionId = null;
let playerName = '';
let gameMap = null;
let resultMap = null;
let guessMarker = null;
let currentGuessCoords = null;

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    initConfigScreen();
    loadStats();
});

/**
 * Initialisation de l'écran de configuration
 */
function initConfigScreen() {
    // Bouton scanner les photos
    document.getElementById('btn-scan-photos').addEventListener('click', scanPhotos);

    // Bouton démarrer la partie
    document.getElementById('btn-start-game').addEventListener('click', startGame);

    // Bouton valider la réponse
    document.getElementById('btn-submit-guess').addEventListener('click', submitGuess);

    // Bouton manche suivante
    document.getElementById('btn-next-round').addEventListener('click', nextRound);

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
