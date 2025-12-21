# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GeoQuizz is a web-based geographic quiz game inspired by GeoGuessr. Players view photos and guess their geographic locations on an interactive map. The application extracts GPS coordinates from photo EXIF metadata, calculates distances, and awards points based on accuracy (0-5000 points per round).

**Tech Stack:**
- Backend: Flask (Python 3.13) with Flask-SocketIO for real-time communication
- Frontend: HTML5, CSS3, JavaScript with Leaflet.js for maps and Socket.IO client
- Storage: JSON files (no database)
- Image processing: Pillow (EXIF extraction)
- Geolocation: geopy
- Real-time sync: WebSocket (Socket.IO)
- QR Code generation: qrcode library

## Core Architecture

### Three-Module System

1. **app.py** - Flask server, API endpoints, and WebSocket handlers
   - REST API for game operations
   - WebSocket event handlers for real-time multiplayer sync
   - QR code generation endpoint
   - Photo serving endpoint with path security
   - Global instances: `photo_manager`, `game_manager`, and `socketio`

2. **photo_manager.py** - Photo discovery and GPS extraction
   - Recursively scans folders for images (.jpg, .jpeg, .png, .tiff, .bmp)
   - Extracts GPS coordinates from EXIF metadata
   - Converts EXIF GPS format to decimal degrees
   - Maintains list of photos with valid GPS data

3. **game_manager.py** - Game logic and state management
   - Session management for solo games
   - Real-time multiplayer room system with WebSocket synchronization
   - 60-second timer per round with automatic submission
   - Player disconnection handling with 30-second pause
   - Scoring algorithm: `5000 * (2^(-distance/250))` for exponential decay
   - Persistence to JSON files in `data/` folder

### Data Flow

**Solo Game:**
1. User configures photo folder → PhotoManager scans for GPS photos
2. User starts game → GameManager creates session with random photos
3. Each round: Client requests photo → submits guess → receives score and actual location
4. Game completion → Session saved to history

**Multiplayer Game (Real-time with WebSocket):**
1. Host creates room → PhotoManager provides photo set → QR code generated
2. Players join via QR code, direct link (`/join/{room_id}`), or room code
3. Lobby with ready status → Host starts when ≥2 players ready
4. Synchronized rounds: All players see same photo with 60-second timer
5. Real-time updates: Player status, guesses, timer via Socket.IO events
6. Results phase: Comparative map showing all player markers in different colors
7. Disconnection handling: 30-second pause for reconnection
8. Final leaderboard with complete scoring

### JSON Data Storage

All data stored in `data/` directory:
- `config.json` - Photo folder path, number of rounds, photo count, map center preference
- `sessions.json` - Active game sessions (in-memory + persisted)
- `games.json` - Completed games history for leaderboard

### User Preferences and Configuration

**Map Center Preference:**
- Checkbox option: "Centrer la carte sur la France à chaque manche"
- Enabled by default (`center_france: true` in config.json)
- When enabled: Map centers on France [46.603354, 1.888334] with zoom 6
- When disabled: Map shows world view (Paris reference) [48.8566, 2.3522] with zoom 2
- Applies to: Solo and multiplayer game modes at the start of each round
- Useful for: French users to quickly select locations in France
- Preference persists across sessions via config.json

### Frontend Architecture

- **Single-page application** in `templates/index.html`
- **State management** via global JavaScript variables in `static/js/app.js`
- **Dual map instances:** gameMap (for guessing) and resultMap (for showing results)
- **API communication:** Async fetch() calls to Flask endpoints
- **Real-time sync:** Socket.IO client connecting to Flask-SocketIO server
- **WebSocket events:** Player join/leave, timer sync, guess submission, round transitions
- **QR code display:** Auto-generated in lobby for easy mobile joining
- **Map centering:** `getMapView()` function returns appropriate center/zoom based on user preference

### WebSocket Architecture (Multiplayer v2.0)

**Server-side (Flask-SocketIO):**
- `socketio = SocketIO(app)` initialized in `app.py`
- Event handlers decorated with `@socketio.on('event_name')`
- Room-based broadcasting: `emit('event', data, room=room_id)`
- Automatic session management with `request.sid`

**Client-side (Socket.IO JavaScript):**
- Connection: `const socket = io()` in `app.js`
- Event listeners: `socket.on('event_name', callback)`
- Emit events: `socket.emit('event_name', data)`
- Automatic reconnection handling

**Key WebSocket Events:**
1. **join_room** - Player joins a multiplayer room
2. **player_ready** - Player marks themselves ready in lobby
3. **start_game** - Host initiates game start
4. **submit_guess** - Player submits location guess
5. **timer_update** - Server broadcasts countdown (every second)
6. **round_results** - Server sends results after round completion
7. **player_disconnected** - Notifies room of player disconnection

**Synchronization Strategy:**
- Server is source of truth for game state
- All state changes broadcast to room members
- Client UI updates reactively based on server events
- Timer runs on server, clients display synchronized countdown

## Development Commands

### Running the Application

**Quick start (Windows):**
```bash
start.bat
```
This activates venv, installs dependencies, and runs the server.

**Manual start:**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python app.py
```
Access at http://localhost:5000

**Docker:**
```bash
docker build -t geoquizz .
docker run -p 5000:5000 geoquizz
```

### Git Operations

**IMPORTANT for Windows:** Always use `git.bat` wrapper instead of `git` directly (bypasses HOME directory config issues):
```bash
git.bat status
git.bat add .
git.bat commit -m "message"
git.bat push
```

The wrapper sets `HOME=C:\temp` to avoid git configuration errors. Never use `git` commands directly - always use `git.bat`.

## API Endpoints Reference

### Configuration
- `GET /api/config` - Load current configuration (photo_folder, num_rounds, center_france, num_photos_found)
- `POST /api/config` - Set photo folder, scan for GPS photos, and save preferences (photo_folder, num_rounds, center_france)

### Solo Game
- `POST /api/game/start` - Create new game session (requires `player_name`, `num_rounds`)
- `GET /api/game/<session_id>/photo` - Get current photo (without GPS coords)
- `POST /api/game/<session_id>/guess` - Submit guess (`latitude`, `longitude`)
- `GET /api/game/<session_id>/summary` - Get game summary and results

### Multiplayer (WebSocket-based)
- `POST /api/sync/room/create` - Create synchronized room (`room_name`, `host_name`, `num_rounds`)
- `GET /api/multiplayer/room/<room_id>/qrcode` - Get QR code PNG for room sharing
- `GET /api/multiplayer/room/<room_id>/exists` - Check if room exists and get basic info
- `GET /join/<room_id>` - Direct join URL (auto-redirects to join flow)

**Socket.IO Events (Real-time):**
- Client → Server: `join_room`, `player_ready`, `submit_guess`, `start_game`, `disconnect`
- Server → Client: `player_joined`, `player_left`, `room_update`, `game_started`, `timer_update`, `round_results`, `game_ended`, `player_disconnected`

### Statistics
- `GET /api/leaderboard?limit=N` - Top N games by score
- `GET /api/stats` - General stats (photo count, best score)

## Key Implementation Details

### Security Considerations

**Photo path validation:** The `/api/photo/<path:photo_path>` endpoint serves arbitrary file paths. While it checks file existence, consider adding whitelist validation to ensure paths are within the configured photo folder.

**Session IDs:** Generated using `uuid.uuid4()` for solo games, shortened to 8 chars for multiplayer rooms (for easier sharing).

### Scoring Algorithm

Located in `game_manager.py:_calculate_score()`:
- Distance < 1 km: 5000 points (maximum)
- Distance > 2000 km: 0 points (minimum)
- Exponential decay between: `5000 * (2^(-distance_km/250))`

### GPS Coordinate Extraction

In `photo_manager.py:_extract_gps_coordinates()`:
1. Read EXIF data using Pillow
2. Find GPSInfo tag
3. Extract latitude/longitude tuples (degrees, minutes, seconds)
4. Convert to decimal: `degrees + minutes/60 + seconds/3600`
5. Apply hemisphere references (S = negative lat, W = negative lon)

### Session Management

Sessions stored in both memory (`active_sessions` dict) and disk (`sessions.json`):
- Allows recovery after server restart
- Tracks current round, guesses, scores
- `finished` flag marks completion

Multiplayer rooms stored only in memory (`multiplayer_rooms`):
- Real-time synchronization via Socket.IO
- All players see same photo simultaneously
- 60-second timer per round (synchronized across all clients)
- Player colors assigned for visual distinction on result maps
- Automatic disconnection handling with 30-second grace period
- Room automatically cleans up when all players leave

## Common Development Tasks

### Adding a new Socket.IO event
1. Define event handler in `app.py` using `@socketio.on('event_name')`
2. Add corresponding client-side listener in `static/js/app.js`
3. Update room state in `game_manager.py` if needed
4. Emit updates to all room members using `socketio.emit('event_name', data, room=room_id)`

### Adding a new game mode
1. Add endpoint in `app.py`
2. Add logic method in `game_manager.py`
3. Update frontend in `static/js/app.js` and `templates/index.html`
4. Add Socket.IO events if real-time sync required

### Modifying scoring algorithm
Edit `game_manager.py:_calculate_score()` - adjust formula parameters or thresholds.

### Modifying timer duration
Change the timer value in both:
1. Server-side: `game_manager.py` - timer logic
2. Client-side: `static/js/app.js` - UI countdown display

### Changing map center behavior
To modify the default map center/zoom:
1. Edit `getMapView()` function in `static/js/app.js`
2. Adjust coordinates and zoom levels for France or world view
3. Default center for France: `[46.603354, 1.888334]` with zoom 6
4. Default center for world: `[48.8566, 2.3522]` with zoom 2
5. Map resets to configured view at start of each round in both `loadCurrentPhoto()` (solo) and `handleRoundStarted()` (multiplayer)

### Adding photo filters
Modify `photo_manager.py:scan_photos()` to add additional EXIF checks (e.g., date ranges, camera models).

### Changing data storage
Currently uses JSON files. To migrate to database:
1. Replace `_save_sessions()`, `_load_sessions()`, etc. in `game_manager.py`
2. Add database models
3. Update requirements.txt with DB library
4. Consider Redis for in-memory room state (better for WebSocket apps)

## Testing the Application

### Preparing Test Photos

Photos must have GPS EXIF metadata. Sources:
- Smartphone photos with location services enabled
- Download geotagged photos from Flickr
- Use sample GPS photo datasets

**Verify GPS metadata (Windows):**
Right-click photo → Properties → Details → Check for Latitude/Longitude under GPS section

**Verify with Python:**
```python
from PIL import Image
from PIL.ExifTags import TAGS

img = Image.open("photo.jpg")
exif = img._getexif()
for tag, value in exif.items():
    if TAGS.get(tag) == 'GPSInfo':
        print("GPS data found!")
```

### Testing Multiplayer

**Web Interface (v2.0+):**
1. Create room from main interface
2. Share QR code or link with other players
3. Join from any device on same network
4. See `MULTIPLAYER_GUIDE.md` for complete feature documentation

**Key Features:**
- QR code automatic generation for easy mobile access
- Three join methods: QR scan, direct link, or room code
- Real-time synchronization with WebSocket
- Up to 6 players per room
- Visual player status indicators
- Colored markers for each player on result maps

## Project Structure Notes

- `static/images/` - Static assets (logos, icons)
- `static/css/` - Styling
- `static/js/` - Client-side logic
- `templates/` - HTML templates (only index.html currently)
- `data/` - JSON data files (auto-created on first run)
- `venv/` - Python virtual environment (excluded from git)

## Known Limitations

1. **In-memory multiplayer rooms** - Rooms lost on server restart
2. **No authentication** - Players identified by name only
3. **File-based storage** - JSON files don't scale well beyond hundreds of games
4. **No photo caching** - Photos served directly from filesystem on each request
5. **Port 5000 conflict** - Change port in `app.py` if needed
6. **Max 6 players** - Room size limited to prevent performance issues
7. **Network dependency** - WebSocket requires stable connection for smooth gameplay

## Deployment Notes

See `DEPLOY.md` for full deployment guide. Key points:

- **Production server:** Use Gunicorn with `eventlet` or `gevent` worker class for WebSocket support
  - Example: `gunicorn --worker-class eventlet -w 1 app:app`
  - Note: Only 1 worker allowed with WebSocket (due to in-memory room state)
- **Environment variables:** Consider externalizing config (photo paths, ports)
- **Docker:** Dockerfile and docker-compose.yml provided
- **Static files:** Consider CDN for production photo serving
- **WebSocket considerations:** Ensure reverse proxy (nginx/Apache) supports WebSocket upgrade headers

## Debugging and Troubleshooting

### WebSocket Connection Issues

**Symptom:** Players can't join or disconnections occur frequently
- Check browser console for Socket.IO connection errors
- Verify Flask-SocketIO is running: Look for `Socket.IO server started` in console
- Test WebSocket endpoint: Browser network tab should show WebSocket upgrade (ws://)
- Firewall: Ensure port 5000 allows both HTTP and WebSocket connections

**Common error:** "WebSocket connection failed"
- Solution: Restart Flask server, clear browser cache, check network

### Room Not Found Errors

**Symptom:** "Room does not exist" when trying to join
- Rooms are in-memory only - lost on server restart
- Room ID is case-sensitive (8 characters)
- Check server logs for room creation confirmation

### Timer Desync

**Symptom:** Timer shows different values for different players
- Server-side timer is authoritative
- Client only displays countdown
- Network lag can cause visual desync (≤1-2 seconds normal)
- Check `timer_update` events in browser console

### Photo Not Loading

**Symptom:** Blank photo or 404 error
- Verify photo path in `data/config.json`
- Check photo has GPS metadata: Use Testing section's Python script
- Ensure file permissions allow Flask to read photos
- Check Flask console for `/api/photo/<path>` request errors

### Git Commit Issues on Windows

**Symptom:** Git commands fail with config errors
- Always use `git.bat` wrapper, never direct `git` commands
- The wrapper sets `HOME=C:\temp` to bypass config location issues
- If errors persist, check git.bat:6 sets correct HOME path

### Performance Issues with Many Photos

**Symptom:** Slow scanning or game start
- PhotoManager scans entire folder tree recursively
- Large photo collections (>1000 images) may take time
- EXIF reading is I/O intensive
- Solution: Use smaller subfolder or implement caching in `photo_manager.py`

### Port 5000 Already in Use

**Symptom:** `OSError: [Errno 98] Address already in use`
- Another Flask/Python process is running
- On Mac: AirPlay Receiver uses port 5000 by default
- Solution: Change port in `app.py` where `socketio.run()` is called
- Or: Kill existing process using port 5000

## File Encoding

All Python files use UTF-8 encoding (specified in JSON dumps with `ensure_ascii=False`) to support international characters in player names and room names.
