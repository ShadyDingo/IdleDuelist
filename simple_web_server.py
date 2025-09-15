#!/usr/bin/env python3
"""
Simple IdleDuelist Web Server
Serves static HTML and handles API endpoints
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import json
import os
import random
from datetime import datetime
import sqlite3

app = FastAPI(title="IdleDuelist Web", description="Web browser version of IdleDuelist")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database setup
def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('web_duelist.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_web_database():
    """Initialize database for web version"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Players table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    rating INTEGER DEFAULT 1000,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    player_data TEXT
                )
            ''')
            
            # Duels table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS duels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player1_id TEXT,
                    player2_id TEXT,
                    winner_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    duel_log TEXT
                )
            ''')
            
            conn.commit()
            print("✅ Web database initialized")
    except Exception as e:
        print(f"❌ Web database error: {e}")

# Initialize database
init_web_database()

# Game data (simplified version)
WEAPONS = {
    'sword': {'name': 'Sword', 'damage': 15, 'speed': 8, 'crit_chance': 0.05},
    'dagger': {'name': 'Dagger', 'damage': 12, 'speed': 12, 'crit_chance': 0.08},
    'mace': {'name': 'Mace', 'damage': 18, 'speed': 6, 'crit_chance': 0.03},
    'bow': {'name': 'Bow', 'damage': 14, 'speed': 10, 'crit_chance': 0.07},
    'staff': {'name': 'Staff', 'damage': 13, 'speed': 9, 'crit_chance': 0.06},
    'axe': {'name': 'Axe', 'damage': 17, 'speed': 7, 'crit_chance': 0.04},
    'hammer': {'name': 'Hammer', 'damage': 19, 'speed': 5, 'crit_chance': 0.02},
    'crossbow': {'name': 'Crossbow', 'damage': 16, 'speed': 9, 'crit_chance': 0.05},
    'knife': {'name': 'Knife', 'damage': 10, 'speed': 14, 'crit_chance': 0.10},
    'shield': {'name': 'Shield', 'damage': 8, 'speed': 6, 'crit_chance': 0.02}
}

ARMOR_TYPES = ['cloth', 'leather', 'metal']

FACTIONS = {
    'order': {'name': 'Order of the Silver Crusade', 'passive': 'Righteous Fury'},
    'shadow': {'name': 'Shadow Covenant', 'passive': 'Shadow Strike'},
    'wilderness': {'name': 'Wilderness Tribe', 'passive': 'Nature\'s Wrath'}
}

ABILITIES = {
    'order': ['Healing Light', 'Shield of Faith', 'Righteous Fury', 'Purification'],
    'shadow': ['Shadow Strike', 'Vanish', 'Shadow Clone', 'Assassinate'],
    'wilderness': ['Wild Growth', 'Thorn Barrier', 'Nature\'s Wrath', 'Spirit Form']
}

class WebPlayer:
    def __init__(self, player_id, username):
        self.id = player_id
        self.username = username
        self.rating = 1000
        self.wins = 0
        self.losses = 0
        self.weapon1 = 'sword'
        self.weapon2 = 'sword'
        self.armor_type = 'cloth'
        self.faction = 'order'
        self.abilities = ABILITIES[self.faction]
        
    def get_stats(self):
        """Calculate player stats"""
        weapon1_stats = WEAPONS[self.weapon1]
        weapon2_stats = WEAPONS[self.weapon2]
        
        # Dual wield bonus
        total_damage = (weapon1_stats['damage'] + weapon2_stats['damage']) * 0.75
        total_speed = (weapon1_stats['speed'] + weapon2_stats['speed']) * 0.8
        total_crit = (weapon1_stats['crit_chance'] + weapon2_stats['crit_chance']) * 0.6
        
        return {
            'damage': int(total_damage),
            'speed': int(total_speed),
            'crit_chance': total_crit,
            'health': 100,
            'armor': 5 if self.armor_type == 'cloth' else 10 if self.armor_type == 'leather' else 15
        }
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'rating': self.rating,
            'wins': self.wins,
            'losses': self.losses,
            'weapon1': self.weapon1,
            'weapon2': self.weapon2,
            'armor_type': self.armor_type,
            'faction': self.faction,
            'abilities': self.abilities
        }

def simulate_duel(player1, player2):
    """Simulate a duel between two players"""
    p1_stats = player1.get_stats()
    p2_stats = player2.get_stats()
    
    # Simple duel simulation
    p1_damage = p1_stats['damage'] + random.randint(-5, 5)
    p2_damage = p2_stats['damage'] + random.randint(-5, 5)
    
    # Speed affects who goes first
    if p1_stats['speed'] > p2_stats['speed']:
        winner = player1 if p1_damage > p2_damage else player2
    else:
        winner = player2 if p2_damage > p1_damage else player1
    
    # Update ratings and wins/losses
    if winner.id == player1.id:
        player1.wins += 1
        player2.losses += 1
        player1.rating += 20
        player2.rating = max(800, player2.rating - 15)
    else:
        player2.wins += 1
        player1.losses += 1
        player2.rating += 20
        player1.rating = max(800, player1.rating - 15)
    
    return winner, p1_damage, p2_damage

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main HTML page"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as e:
        print(f"Error reading HTML file: {e}")
        return HTMLResponse(content="<h1>Error loading page</h1><p>Please check the server logs.</p>")

@app.get("/get-player/{username}")
async def get_player(username: str):
    """Get a player by username"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM players WHERE username = ?', (username,))
            player_row = cursor.fetchone()
            
            if player_row:
                player_data = json.loads(player_row['player_data'])
                return JSONResponse({
                    "success": True,
                    "player": player_data
                })
            else:
                return JSONResponse({
                    "success": False,
                    "error": "Player not found"
                })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

@app.post("/create-player")
async def create_player(player_data: dict):
    """Create a new player"""
    try:
        player_id = f"web_{random.randint(10000, 99999)}"
        player = WebPlayer(player_id, player_data['username'])
        player.faction = player_data['faction']
        player.armor_type = player_data['armor_type']
        player.weapon1 = player_data['weapon1']
        player.weapon2 = player_data['weapon2']
        player.abilities = ABILITIES[player.faction]
        
        # Save to database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO players (id, username, rating, wins, losses, player_data)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (player.id, player.username, player.rating, player.wins, player.losses, json.dumps(player.to_dict())))
            conn.commit()
        
        return JSONResponse({
            "success": True,
            "player": player.to_dict()
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

@app.post("/duel")
async def duel(player_data: dict):
    """Find and execute a duel"""
    try:
        player_id = player_data['player_id']
        
        # Get player from database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM players WHERE id = ?', (player_id,))
            player_row = cursor.fetchone()
            
            if not player_row:
                return JSONResponse({"success": False, "error": "Player not found"})
            
            player_data_dict = json.loads(player_row['player_data'])
            player = WebPlayer(player_data_dict['id'], player_data_dict['username'])
            player.__dict__.update(player_data_dict)
        
        # Find opponent (simplified - just get another player)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM players WHERE id != ? ORDER BY RANDOM() LIMIT 1', (player_id,))
            opponent_row = cursor.fetchone()
            
            if not opponent_row:
                return JSONResponse({"success": False, "error": "No opponents available"})
            
            opponent_data = json.loads(opponent_row['player_data'])
            opponent = WebPlayer(opponent_data['id'], opponent_data['username'])
            opponent.__dict__.update(opponent_data)
        
        # Simulate duel
        winner, p1_damage, p2_damage = simulate_duel(player, opponent)
        
        # Save results
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Update players
            cursor.execute('''
                UPDATE players SET rating = ?, wins = ?, losses = ?, player_data = ?
                WHERE id = ?
            ''', (player.rating, player.wins, player.losses, json.dumps(player.to_dict()), player.id))
            
            cursor.execute('''
                UPDATE players SET rating = ?, wins = ?, losses = ?, player_data = ?
                WHERE id = ?
            ''', (opponent.rating, opponent.wins, opponent.losses, json.dumps(opponent.to_dict()), opponent.id))
            
            # Save duel record
            cursor.execute('''
                INSERT INTO duels (player1_id, player2_id, winner_id, duel_log)
                VALUES (?, ?, ?, ?)
            ''', (player.id, opponent.id, winner.id, json.dumps({
                'player_damage': p1_damage,
                'opponent_damage': p2_damage,
                'timestamp': datetime.now().isoformat()
            })))
            
            conn.commit()
        
        return JSONResponse({
            "success": True,
            "winner": winner.id,
            "player_name": player.username,
            "opponent_name": opponent.username,
            "player_damage": p1_damage,
            "opponent_damage": p2_damage,
            "updated_player": player.to_dict()
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

@app.get("/leaderboard")
async def get_leaderboard():
    """Get leaderboard"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT username, rating, wins, losses 
                FROM players 
                ORDER BY rating DESC 
                LIMIT 20
            ''')
            players = [dict(row) for row in cursor.fetchall()]
        
        return JSONResponse(players)
    except Exception as e:
        return JSONResponse({"error": str(e)})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({"status": "healthy", "web_version": True})

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
