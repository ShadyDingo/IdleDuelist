# 🌐 IdleDuelist Online Integration Guide

## Overview
This guide explains how to integrate the online multiplayer functionality into your existing IdleDuelist mobile app.

## 🏗️ Architecture

### Backend Components
- **FastAPI Server** (`backend_server.py`): Handles player data, duels, and real-time communication
- **PostgreSQL Database**: Stores player profiles, loadouts, and duel results
- **WebSocket**: Real-time communication for live dueling
- **Redis**: Caching and session management
- **Nginx**: Reverse proxy and SSL termination

### Mobile App Changes
- **NetworkManager** (`network_manager.py`): Handles online/offline states and server communication
- **Player Sync**: Upload/download player data
- **Real Opponents**: Replace bots with real player loadouts
- **Offline Queue**: Store operations when offline, sync when online

## 🚀 Implementation Steps

### 1. Backend Setup

#### Install Dependencies
```bash
pip install -r backend_requirements.txt
```

#### Database Setup
```bash
# Create PostgreSQL database
createdb idle_duelist

# Run migrations (if using Alembic)
alembic upgrade head
```

#### Start Backend Server
```bash
python backend_server.py
```

### 2. Mobile App Integration

#### Add Network Dependencies
Add to your `requirements.txt`:
```
requests==2.31.0
websocket-client==1.6.4
```

#### Integrate NetworkManager
```python
# In your main app file
from network_manager import NetworkManager

class IdleDuelistApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.network_manager = NetworkManager("https://your-server.com")
        self.network_manager.register_sync_callback(self.on_data_synced)
        self.network_manager.register_duel_callback(self.on_duel_event)
    
    def on_data_synced(self, success):
        if success:
            print("Data synced with server!")
        else:
            print("Failed to sync data")
    
    def on_duel_event(self, event_type, data):
        if event_type == "duel_request":
            self.handle_duel_request(data)
        elif event_type == "duel_result":
            self.handle_duel_result(data)
```

#### Modify Player Data Management
```python
# In your PlayerData class
def sync_with_server(self):
    """Sync player data with server"""
    if self.app.network_manager:
        player_data = {
            "username": self.username,
            "rating": self.rating,
            "wins": self.wins,
            "losses": self.losses,
            "equipment": self.equipment,
            "faction": self.faction,
            "abilities": self.abilities
        }
        return self.app.network_manager.sync_player_data(player_data)
    return False

def load_from_server(self):
    """Load player data from server"""
    if self.app.network_manager:
        data = self.app.network_manager.get_player_data()
        if data:
            self.username = data["username"]
            self.rating = data["rating"]
            self.wins = data["wins"]
            self.losses = data["losses"]
            self.equipment = data["equipment"]
            self.faction = data["faction"]
            self.abilities = data["abilities"]
            return True
    return False
```

#### Replace Bot Opponents with Real Players
```python
# In your CombatScreen class
def get_opponent(self):
    """Get opponent from server instead of generating bot"""
    if self.app.network_manager and self.app.network_manager.is_online:
        # Get real opponent from server
        opponents = self.app.network_manager.get_available_opponents(1)
        if opponents:
            opponent_data = opponents[0]
            opponent = PlayerData()
            opponent.username = opponent_data["username"]
            opponent.rating = opponent_data["rating"]
            opponent.equipment = opponent_data["loadout"]
            opponent.faction = opponent_data["faction"]
            return opponent
    
    # Fallback to bot if offline
    return self.app.data_manager.create_bot_opponent(self.app.current_player.rating)
```

#### Add Offline Duel Processing
```python
# In your main app
def check_offline_duels(self):
    """Check for duels that happened while offline"""
    if self.network_manager and self.network_manager.is_online:
        offline_duels = self.network_manager.get_offline_duels()
        for duel in offline_duels:
            self.process_offline_duel(duel)

def process_offline_duel(self, duel_data):
    """Process a duel that happened while offline"""
    # Update player stats based on duel result
    if duel_data["winner_id"] == self.current_player.id:
        self.current_player.wins += 1
        self.current_player.rating += 20
    else:
        self.current_player.losses += 1
        self.current_player.rating = max(800, self.current_player.rating - 15)
    
    # Save updated data
    self.data_manager.save_data()
    
    # Show notification to player
    self.show_notification(f"You were dueled while offline! Result: {'Win' if duel_data['winner_id'] == self.current_player.id else 'Loss'}")
```

### 3. Deployment

#### Production Server Setup
```bash
# Clone your repository
git clone https://github.com/yourusername/IdleDuelist.git
cd IdleDuelist

# Set up environment variables
export DATABASE_URL="postgresql://user:password@localhost/idle_duelist"
export REDIS_URL="redis://localhost:6379"

# Start services with Docker Compose
docker-compose up -d
```

#### SSL Certificate Setup
```bash
# Generate SSL certificate (use Let's Encrypt for production)
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes
```

#### Google Play Store Deployment
1. **Build APK with Buildozer**:
   ```bash
   buildozer android debug
   ```

2. **Sign APK for release**:
   ```bash
   buildozer android release
   ```

3. **Upload to Google Play Console**

## 🔧 Configuration

### Environment Variables
```bash
# Backend
DATABASE_URL=postgresql://user:password@localhost/idle_duelist
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here

# Mobile App
SERVER_URL=https://your-server.com
API_KEY=your-api-key-here
```

### Server Configuration
```python
# In backend_server.py
BASE_URL = "https://your-domain.com"
CORS_ORIGINS = ["https://your-domain.com", "http://localhost:8000"]
```

## 🎮 Gameplay Flow

### Online Mode
1. **Player opens app** → Connects to server
2. **Creates/loads character** → Syncs with server
3. **Requests duel** → Server finds opponent
4. **Duels real player** → Results saved to server
5. **Character available** → Other players can duel your character

### Offline Mode
1. **Player goes offline** → App stores operations locally
2. **Other players duel** → Your character fights automatically
3. **Player returns** → App syncs results and updates stats
4. **Combined stats** → Shows total wins/losses including offline duels

## 🔒 Security Considerations

### Authentication
- Implement JWT tokens for player authentication
- Use secure session management
- Validate all input data

### Rate Limiting
- Limit duel requests per player
- Prevent spam and abuse
- Implement cooldown periods

### Data Validation
- Validate all equipment and stats
- Prevent cheating and exploits
- Regular security audits

## 📊 Monitoring and Analytics

### Server Monitoring
- Monitor server performance
- Track player activity
- Monitor error rates

### Game Analytics
- Track player engagement
- Monitor balance issues
- Analyze popular builds

## 🚀 Future Enhancements

### Advanced Features
- **Guilds/Clans**: Group players together
- **Tournaments**: Organized competitive events
- **Leaderboards**: Global and regional rankings
- **Chat System**: Player communication
- **Achievements**: Unlockable rewards

### Performance Optimizations
- **Caching**: Redis for frequently accessed data
- **CDN**: Fast asset delivery
- **Load Balancing**: Multiple server instances
- **Database Optimization**: Indexing and query optimization

## 🐛 Troubleshooting

### Common Issues
1. **Connection Timeouts**: Check server status and network
2. **Sync Failures**: Verify data format and server endpoints
3. **WebSocket Issues**: Check firewall and proxy settings
4. **Database Errors**: Verify connection strings and permissions

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📱 Mobile Considerations

### Battery Optimization
- Minimize network requests
- Use efficient data structures
- Implement smart sync intervals

### Offline Support
- Store critical data locally
- Queue operations for later sync
- Graceful degradation when offline

### Network Efficiency
- Compress data transfers
- Use efficient serialization
- Implement request batching

This integration will transform your IdleDuelist into a fully online multiplayer experience where players can duel each other's characters in real-time, with automatic offline dueling and stat synchronization!
