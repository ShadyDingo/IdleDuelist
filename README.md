# IdleDuelist

A turn-based combat game built with FastAPI and vanilla JavaScript.

## Quick Start

### Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment (optional):**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start the server:**
   ```bash
   start_server.bat
   ```
   Or manually:
   ```bash
   python start_server.py
   ```

4. **Open your browser:**
   Navigate to: http://localhost:8000

### Production Deployment

See [README_DEPLOYMENT.md](README_DEPLOYMENT.md) for Railway deployment instructions.

For production readiness checklist, see [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md).

## Project Structure

```
IdleDuelist/
├── app/                 # Application package
│   ├── core/           # Config, logging, cache, in-memory state
│   ├── db/             # Database manager + bootstrap helpers
│   └── services/       # Player tracking, matchmaking state utilities
├── assets/              # Game assets (images, backgrounds, etc.)
├── static/              # Frontend files
│   ├── game.html        # Main game interface
│   └── index.html       # Landing page
├── tests/               # Test files
│   ├── test_game_logic.py
│   └── test_api.py
├── server.py            # Main backend server
├── game_logic.py        # Game mechanics
├── models.py            # Pydantic request models
├── error_handlers.py    # Error handling
├── env_validation.py    # Environment validation
├── backup_database.py   # Database backup script
├── start_server.py      # Server startup script
├── start_server.bat     # Windows startup script
├── requirements.txt     # Python dependencies
├── pytest.ini          # Test configuration
├── railway.json        # Railway deployment config
├── .env.example        # Environment variables template
└── README_DEPLOYMENT.md # Deployment guide
```

## Features

- Character creation and customization
- Turn-based combat system
- Equipment and ability management
- PvP and PvE combat
- Store system for equipment
- Feedback system
- Leaderboards
- Auto-combat for PvE
- Persistent player profiles + match history storage
- Competitive PvP MMR with Redis-backed queueing

## Online Architecture & Persistence

- **Modular backend:** `app/core` centralizes configuration/logging/Redis management, `app/db` abstracts SQLite/PostgreSQL differences, and `app/services` contains state stores plus the new `PlayerTrackingService`.
- **Player telemetry tables:** startup now ensures `player_profiles`, `player_sessions`, `player_progress_log`, and `pvp_matches` exist on both SQLite (local) and PostgreSQL (Railway). New analytics endpoints expose this data:
  - `GET /api/player/profile`
  - `GET /api/player/progress/{character_id}`
  - `GET /api/player/matches`
- **Queue + combat state backed by Redis:** `state_service` seamlessly toggles between Redis (`REDIS_URL`) and the in-memory fallback, so Railway deployments can scale horizontally without losing combat data.
- **Railway deployment tips:**
  1. Provision a PostgreSQL service and set `DATABASE_URL` in Railway.
  2. (Optional) Provision Redis and set `REDIS_URL` for distributed combat queues.
  3. Ensure `CORS_ORIGINS` lists your production domain(s) – wildcards are blocked in production.
  4. Push to `main` and Railway will rebuild automatically using `railway.json`.

## API Documentation

See [API_DOCS.md](API_DOCS.md) for complete API documentation.

## Testing

Run tests with:
```bash
pytest
```

Run specific test file:
```bash
pytest tests/test_game_logic.py
```

## Environment Variables

See `.env.example` for all available environment variables.

**Required for Production:**
- `ENVIRONMENT=production`
- `JWT_SECRET_KEY` (minimum 32 characters)
- `CORS_ORIGINS` (comma-separated list of allowed origins)
- `DATABASE_URL` (PostgreSQL connection string)

**Optional:**
- `REDIS_URL` (Redis connection string)
- `REDIS_NAMESPACE` (defaults to `idleduelist`, useful when sharing Redis)
- `COMBAT_STATE_TTL`, `AUTO_FIGHT_TTL`, `PVP_QUEUE_TTL`, `ACTIVE_SESSION_TTL` for fine-tuning expirations
- `JWT_ALGORITHM` (default: HS256)
- `PORT` (default: 8000)

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.

## Production Readiness

This project includes:
- Security hardening (CORS, rate limiting)
- Proper logging infrastructure
- Error handling and recovery
- Input validation
- Health checks and metrics
- Database backup scripts
- Environment validation
- Comprehensive documentation

## Contributing

1. Create a feature branch
2. Make your changes
3. Add tests for new features
4. Run tests and ensure they pass
5. Submit a pull request

## License

[Your License Here]

Enjoy playing IdleDuelist!
