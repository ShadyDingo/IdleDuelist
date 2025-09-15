# 📱 IdleDuelist Mobile App Integration Guide

## Your Live Backend is Ready!
**URL**: `https://idle-duelist-backend-production.up.railway.app`

## Quick Integration Steps:

### 1. Update NetworkManager in Your Mobile App
```python
# In your idle_duelist.py file, find the NetworkManager initialization
# and change it to:

from network_manager import NetworkManager

class IdleDuelistApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Update this line to use your live backend:
        self.network_manager = NetworkManager("https://idle-duelist-backend-production.up.railway.app")
        self.network_manager.register_sync_callback(self.on_data_synced)
        self.network_manager.register_duel_callback(self.on_duel_event)
```

### 2. Add Online/Offline Mode Toggle
```python
def check_connection(self):
    """Check if we can connect to the server"""
    if self.network_manager.check_connection():
        self.show_message("✅ Connected to online server!")
        return True
    else:
        self.show_message("❌ Offline mode - playing locally")
        return False
```

### 3. Sync Player Data on Startup
```python
def sync_player_data(self):
    """Sync player data with server"""
    if self.network_manager:
        player_data = {
            "id": self.current_player.id,
            "username": self.current_player.username,
            "rating": self.current_player.rating,
            "wins": self.current_player.wins,
            "losses": self.current_player.losses
        }
        success = self.network_manager.sync_player_data(player_data)
        if success:
            self.show_message("Data synced with server!")
```

## Test Your Integration:

### 1. Run Your Mobile App
```bash
python idle_duelist.py
```

### 2. Check Connection
- Look for "Connected to online server!" message
- Check if player data syncs

### 3. Test Online Features
- Create a character
- Check if it appears in stats: https://idle-duelist-backend-production.up.railway.app/stats

## Your Backend Endpoints:

### Health Check
- **GET** `/health` - Check if server is running
- **Response**: `{"status":"healthy","simple":true}`

### Player Management
- **POST** `/players/register` - Register/update player
- **GET** `/stats` - Get server statistics

### Example Player Registration
```json
{
  "id": "player_123",
  "username": "MyCharacter",
  "rating": 1000,
  "wins": 0,
  "losses": 0
}
```

## Troubleshooting:

### If Connection Fails:
1. Check your internet connection
2. Verify the server URL is correct
3. Check Railway logs for errors

### If Data Doesn't Sync:
1. Check NetworkManager logs
2. Verify player data format
3. Test endpoints manually with curl

## Next Steps:
1. **Test basic connectivity** with your mobile app
2. **Add more backend features** (dueling, matchmaking)
3. **Deploy mobile app** to Google Play Store
4. **Scale up** when you have more players

Your IdleDuelist is now online and ready for multiplayer! 🎉
