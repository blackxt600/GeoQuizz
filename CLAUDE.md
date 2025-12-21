# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GeoQuizz is a web-based geographic quiz game inspired by GeoGuessr. Players view photos and guess their geographic locations on an interactive map. The application extracts GPS coordinates from photo EXIF metadata, calculates distances, and awards points based on accuracy (0-5000 points per round).

**Tech Stack:**
- Backend: Flask (Python 3.13)
- Frontend: HTML5, CSS3, JavaScript with Leaflet.js for maps
- Storage: JSON files (no database)
- Image processing: Pillow (EXIF extraction)
- Geolocation: geopy

## Core Architecture

### Three-Module System

1. **app.py** - Flask server and API endpoints
   - REST API for game operations and multiplayer rooms
   - Photo serving endpoint with path security
   - Global instances: `photo_manager` and `game_manager`

2. **photo_manager.py** - Photo discovery and GPS extraction
   - Recursively scans folders for images (.jpg, .jpeg, .png, .tiff, .bmp)
   - Extracts GPS coordinates from EXIF metadata
   - Converts EXIF GPS format to decimal degrees
   - Maintains list of photos with valid GPS data

3. **game_manager.py** - Game logic and state management
   - Session management for solo games
   - Multiplayer room system with turn-by-turn gameplay
   - Scoring algorithm: `5000 * (2^(-distance/250))` for exponential decay
   - Persistence to JSON files in `data/` folder

### Data Flow

**Solo Game:**
1. User configures photo folder → PhotoManager scans for GPS photos
2. User starts game → GameManager creates session with random photos
3. Each round: Client requests photo → submits guess → receives score and actual location
4. Game completion → Session saved to history

**Multiplayer Game:**
1. Host creates room → PhotoManager provides photo set
2. Players join room → Each gets individual progress tracking
3. Each player progresses independently through same photos
4. Room finishes when all players complete all rounds
5. Leaderboard tracks comparative scores

### JSON Data Storage

All data stored in `data/` directory:
- `config.json` - Photo folder path, number of rounds, photo count
- `sessions.json` - Active game sessions (in-memory + persisted)
- `games.json` - Completed games history for leaderboard

### Frontend Architecture

- **Single-page application** in `templates/index.html`
- **State management** via global JavaScript variables in `static/js/app.js`
- **Dual map instances:** gameMap (for guessing) and resultMap (for showing results)
- **API communication:** Async fetch() calls to Flask endpoints

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

Use `git.bat` wrapper on Windows (bypasses config issues):
```bash
git.bat status
git.bat add .
git.bat commit -m "message"
git.bat push
```

## API Endpoints Reference

### Configuration
- `GET /api/config` - Load current configuration
- `POST /api/config` - Set photo folder and scan for GPS photos

### Solo Game
- `POST /api/game/start` - Create new game session (requires `player_name`, `num_rounds`)
- `GET /api/game/<session_id>/photo` - Get current photo (without GPS coords)
- `POST /api/game/<session_id>/guess` - Submit guess (`latitude`, `longitude`)
- `GET /api/game/<session_id>/summary` - Get game summary and results

### Multiplayer
- `POST /api/multiplayer/room/create` - Create room (`room_name`, `host_name`, `num_rounds`)
- `POST /api/multiplayer/room/<room_id>/join` - Join room (`player_name`)
- `POST /api/multiplayer/room/<room_id>/start` - Start game
- `GET /api/multiplayer/room/<room_id>/info` - Get room status and players
- `GET /api/multiplayer/room/<room_id>/photo?player_name=X` - Get current photo for player
- `POST /api/multiplayer/room/<room_id>/guess` - Submit guess (`player_name`, `latitude`, `longitude`)
- `GET /api/multiplayer/room/<room_id>/leaderboard` - Get room rankings

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
- Each player has independent progress within shared photo set
- Room marked finished when all players complete all rounds

## Common Development Tasks

### Adding a new game mode
1. Add endpoint in `app.py`
2. Add logic method in `game_manager.py`
3. Update frontend in `static/js/app.js` and `templates/index.html`

### Modifying scoring algorithm
Edit `game_manager.py:_calculate_score()` - adjust formula parameters or thresholds.

### Adding photo filters
Modify `photo_manager.py:scan_photos()` to add additional EXIF checks (e.g., date ranges, camera models).

### Changing data storage
Currently uses JSON files. To migrate to database:
1. Replace `_save_sessions()`, `_load_sessions()`, etc. in `game_manager.py`
2. Add database models
3. Update requirements.txt with DB library

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

### Testing Multiplayer via API

See `MULTIPLAYER.md` for complete examples using curl or Python requests library.

## Project Structure Notes

- `static/images/` - Static assets (logos, icons)
- `static/css/` - Styling
- `static/js/` - Client-side logic
- `templates/` - HTML templates (only index.html currently)
- `data/` - JSON data files (auto-created on first run)
- `venv/` - Python virtual environment (excluded from git)

## Known Limitations

1. **No real-time multiplayer UI** - Multiplayer only accessible via API, no web interface yet
2. **In-memory multiplayer rooms** - Rooms lost on server restart
3. **No authentication** - Players identified by name only
4. **File-based storage** - JSON files don't scale well beyond hundreds of games
5. **No photo caching** - Photos served directly from filesystem on each request
6. **Port 5000 conflict** - Change port in `app.py` line 289 if needed

## Deployment Notes

See `DEPLOY.md` for full deployment guide. Key points:

- **Production server:** Use Gunicorn instead of Flask dev server
- **Environment variables:** Consider externalizing config (photo paths, ports)
- **Docker:** Dockerfile and docker-compose.yml provided
- **Static files:** Consider CDN for production photo serving

## File Encoding

All Python files use UTF-8 encoding (specified in JSON dumps with `ensure_ascii=False`) to support international characters in player names and room names.
