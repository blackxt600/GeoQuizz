# Changelog

All notable changes to GeoQuizz will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-12-21

### Added - User Experience
- **France Map Centering**: New checkbox option to automatically center map on France at each round start
  - Enabled by default for easy location selection in France
  - Map centers on [46.603354, 1.888334] with zoom level 6 when enabled
  - Falls back to world view (Paris reference) with zoom level 2 when disabled
  - Preference persists across sessions in `config.json`
  - Works in both solo and multiplayer modes

### Added - Technical
- New field `center_france` in configuration storage (`data/config.json`)
- New global JavaScript variable `centerOnFrance` for runtime preference
- New function `getMapView()` in `app.js` to return appropriate map center/zoom
- New function `loadConfig()` in `app.js` to restore saved configuration on page load
- Configuration checkbox in HTML configuration screen with help text

### Changed
- `POST /api/config` endpoint now accepts and saves `center_france` parameter
- `GET /api/config` endpoint now returns `center_france` preference
- Map initialization and reset logic updated to use dynamic centering:
  - `initGameMap()` - Initial map creation
  - `loadCurrentPhoto()` - Solo mode round start
  - `handleRoundStarted()` - Multiplayer mode round start

### Documentation
- Updated `CLAUDE.md` with map centering feature details
- Updated `README.md` with user-facing feature description
- Added development task section for modifying map center behavior

## [2.0.0] - 2025-12-21

### Added - Multiplayer Mode
- **QR Code Generation**: Automatic QR code generation for easy room sharing
- **Local IP Detection**: Automatic detection of server's local network IP address
- **Direct URL Join**: Join rooms directly via URL (`/join/{room_id}`)
- **Share URL Display**: Display and copy room share URL in lobby
- **Multiplayer Guide**: Comprehensive guide for multiplayer features (`MULTIPLAYER_GUIDE.md`)

### Added - Technical Improvements
- New endpoint `/api/multiplayer/room/{room_id}/qrcode` for QR code generation
- New endpoint `/api/multiplayer/room/{room_id}/share-url` for share URL with local IP
- New endpoint `/api/multiplayer/room/{room_id}/exists` to check room status
- Auto-join functionality when accessing `/join/{room_id}`
- `get_local_ip()` function for network IP detection
- CSS `.hidden` utility class for better element visibility control
- QR code section in lobby interface with styling

### Fixed
- **Map Display in Multiplayer**: Fixed Leaflet map not showing in multiplayer mode
  - Corrected initialization order (initialize before use)
  - Added `invalidateSize()` call for proper rendering
  - Fixed map resize handling after screen transitions
- **Button State Management**: Improved button text and state in multiplayer flow
- **WebSocket Connection**: Better handling of room joining and state updates

### Changed
- QR codes now use local network IP instead of localhost
- Share URLs automatically use the correct network IP for cross-device access
- Improved lobby interface with QR code and URL display sections
- Enhanced user experience with visual URL display in lobby

### Dependencies
- Added `qrcode==8.2` for QR code generation
- Added `socket` module usage for IP detection

### Documentation
- Added `MULTIPLAYER_GUIDE.md` - Complete guide for multiplayer features
- Updated `CLAUDE.md` with new multiplayer features
- Added inline code documentation for new functions

## [1.0.0] - Previous Version

### Features
- Solo gameplay mode
- Asynchronous multiplayer mode (API-based)
- Synchronized multiplayer mode (WebSocket-based)
- Photo GPS extraction from EXIF metadata
- Interactive Leaflet maps
- Scoring system based on distance
- Leaderboard and statistics
- Docker support
- Flask-SocketIO for real-time communication

---

## Upcoming Features

### Planned for Future Releases
- [ ] Mobile-optimized interface
- [ ] Multiple game modes (timed, unlimited, etc.)
- [ ] Custom scoring algorithms
- [ ] Photo filters and categories
- [ ] User profiles and persistent stats
- [ ] Tournament mode
- [ ] Team-based multiplayer
- [ ] Voice chat integration
- [ ] Advanced map markers and styling
- [ ] Photo hints system
- [ ] Achievement system

## Release Links

- **v2.0.0**: https://github.com/blackxt600/GeoQuizz/releases/tag/v2.0.0
- **Repository**: https://github.com/blackxt600/GeoQuizz

## Support

For bug reports and feature requests, please visit:
https://github.com/blackxt600/GeoQuizz/issues
