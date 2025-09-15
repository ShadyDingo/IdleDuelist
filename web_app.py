#!/usr/bin/env python3
"""
IdleDuelist Web Browser Version
A web-based version of the IdleDuelist game using FastAPI and HTML/CSS/JavaScript
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import json
import os
import random
from datetime import datetime
import sqlite3

# Import the game logic from the main app
import sys
sys.path.append('.')

app = FastAPI(title="IdleDuelist Web", description="Web browser version of IdleDuelist")

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
    """Main game page"""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>IdleDuelist - Web Browser Game</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Arial', sans-serif;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: rgba(0, 0, 0, 0.3);
                border-radius: 15px;
                padding: 30px;
                backdrop-filter: blur(10px);
            }
            
            h1 {
                text-align: center;
                font-size: 2.5em;
                margin-bottom: 30px;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
            }
            
            .game-section {
                display: none;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
            }
            
            .game-section.active {
                display: block;
            }
            
            .character-creation {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .form-group {
                margin-bottom: 15px;
            }
            
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            
            input, select {
                width: 100%;
                padding: 10px;
                border: none;
                border-radius: 5px;
                background: rgba(255, 255, 255, 0.9);
                color: #333;
                font-size: 16px;
            }
            
            button {
                background: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                margin: 5px;
                transition: background 0.3s;
            }
            
            button:hover {
                background: #45a049;
            }
            
            button:disabled {
                background: #666;
                cursor: not-allowed;
            }
            
            .stats-display {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }
            
            .stat-card {
                background: rgba(255, 255, 255, 0.1);
                padding: 15px;
                border-radius: 8px;
                text-align: center;
            }
            
            .stat-value {
                font-size: 1.5em;
                font-weight: bold;
                color: #4CAF50;
            }
            
            .duel-log {
                background: rgba(0, 0, 0, 0.5);
                border-radius: 8px;
                padding: 15px;
                max-height: 300px;
                overflow-y: auto;
                font-family: monospace;
                margin: 20px 0;
            }
            
            .nav-buttons {
                text-align: center;
                margin: 20px 0;
            }
            
            .leaderboard {
                display: grid;
                gap: 10px;
            }
            
            .leaderboard-entry {
                display: grid;
                grid-template-columns: 1fr auto auto auto;
                gap: 15px;
                background: rgba(255, 255, 255, 0.1);
                padding: 10px;
                border-radius: 5px;
                align-items: center;
            }
            
            .rating {
                color: #FFD700;
                font-weight: bold;
            }
            
            .wins { color: #4CAF50; }
            .losses { color: #f44336; }
            
            .loading {
                text-align: center;
                padding: 20px;
            }
            
            .error {
                color: #f44336;
                background: rgba(244, 67, 54, 0.1);
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
            }
            
            .success {
                color: #4CAF50;
                background: rgba(76, 175, 80, 0.1);
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⚔️ IdleDuelist Web Edition ⚔️</h1>
            
            <!-- Character Creation -->
            <div id="character-creation" class="game-section active">
                <h2>Create Your Character</h2>
                <form id="character-form">
                    <div class="character-creation">
                        <div>
                            <div class="form-group">
                                <label for="username">Character Name:</label>
                                <input type="text" id="username" name="username" required>
                            </div>
                            
                            <div class="form-group">
                                <label for="faction">Faction:</label>
                                <select id="faction" name="faction" onchange="updateAbilities()">
                                    <option value="order">Order of the Silver Crusade</option>
                                    <option value="shadow">Shadow Covenant</option>
                                    <option value="wilderness">Wilderness Tribe</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="armor-type">Armor Type:</label>
                                <select id="armor-type" name="armor_type">
                                    <option value="cloth">Cloth (Light)</option>
                                    <option value="leather">Leather (Medium)</option>
                                    <option value="metal">Metal (Heavy)</option>
                                </select>
                            </div>
                        </div>
                        
                        <div>
                            <div class="form-group">
                                <label for="weapon1">Primary Weapon:</label>
                                <select id="weapon1" name="weapon1">
                                    <option value="sword">Sword</option>
                                    <option value="dagger">Dagger</option>
                                    <option value="mace">Mace</option>
                                    <option value="bow">Bow</option>
                                    <option value="staff">Staff</option>
                                    <option value="axe">Axe</option>
                                    <option value="hammer">Hammer</option>
                                    <option value="crossbow">Crossbow</option>
                                    <option value="knife">Knife</option>
                                    <option value="shield">Shield</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="weapon2">Secondary Weapon:</label>
                                <select id="weapon2" name="weapon2">
                                    <option value="sword">Sword</option>
                                    <option value="dagger">Dagger</option>
                                    <option value="mace">Mace</option>
                                    <option value="bow">Bow</option>
                                    <option value="staff">Staff</option>
                                    <option value="axe">Axe</option>
                                    <option value="hammer">Hammer</option>
                                    <option value="crossbow">Crossbow</option>
                                    <option value="knife">Knife</option>
                                    <option value="shield">Shield</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label>Abilities:</label>
                                <div id="abilities-display"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="nav-buttons">
                        <button type="submit">Create Character & Start Playing</button>
                    </div>
                </form>
            </div>
            
            <!-- Game Interface -->
            <div id="game-interface" class="game-section">
                <h2>Welcome, <span id="player-name"></span>!</h2>
                
                <div class="stats-display">
                    <div class="stat-card">
                        <div>Rating</div>
                        <div class="stat-value" id="rating">1000</div>
                    </div>
                    <div class="stat-card">
                        <div>Wins</div>
                        <div class="stat-value wins" id="wins">0</div>
                    </div>
                    <div class="stat-card">
                        <div>Losses</div>
                        <div class="stat-value losses" id="losses">0</div>
                    </div>
                    <div class="stat-card">
                        <div>Damage</div>
                        <div class="stat-value" id="damage">15</div>
                    </div>
                    <div class="stat-card">
                        <div>Speed</div>
                        <div class="stat-value" id="speed">8</div>
                    </div>
                    <div class="stat-card">
                        <div>Crit Chance</div>
                        <div class="stat-value" id="crit">5%</div>
                    </div>
                </div>
                
                <div class="nav-buttons">
                    <button onclick="findDuel()">⚔️ Find Duel</button>
                    <button onclick="showLeaderboard()">🏆 Leaderboard</button>
                    <button onclick="showCharacterInfo()">👤 Character Info</button>
                </div>
                
                <div id="duel-log" class="duel-log" style="display: none;"></div>
            </div>
            
            <!-- Leaderboard -->
            <div id="leaderboard" class="game-section">
                <h2>🏆 Leaderboard</h2>
                <div id="leaderboard-content" class="leaderboard">
                    <div class="loading">Loading leaderboard...</div>
                </div>
                <div class="nav-buttons">
                    <button onclick="showGameInterface()">← Back to Game</button>
                </div>
            </div>
            
            <!-- Character Info -->
            <div id="character-info" class="game-section">
                <h2>👤 Character Information</h2>
                <div id="character-details"></div>
                <div class="nav-buttons">
                    <button onclick="showGameInterface()">← Back to Game</button>
                </div>
            </div>
        </div>
        
        <script>
            let currentPlayer = null;
            
            // Game data
            const WEAPONS = {
                'sword': {'damage': 15, 'speed': 8, 'crit_chance': 0.05, 'name': 'Sword'},
                'dagger': {'damage': 12, 'speed': 12, 'crit_chance': 0.08, 'name': 'Dagger'},
                'mace': {'damage': 18, 'speed': 6, 'crit_chance': 0.03, 'name': 'Mace'},
                'bow': {'damage': 14, 'speed': 10, 'crit_chance': 0.07, 'name': 'Bow'},
                'staff': {'damage': 13, 'speed': 9, 'crit_chance': 0.06, 'name': 'Staff'},
                'axe': {'damage': 17, 'speed': 7, 'crit_chance': 0.04, 'name': 'Axe'},
                'hammer': {'damage': 19, 'speed': 5, 'crit_chance': 0.02, 'name': 'Hammer'},
                'crossbow': {'damage': 16, 'speed': 9, 'crit_chance': 0.05, 'name': 'Crossbow'},
                'knife': {'damage': 10, 'speed': 14, 'crit_chance': 0.10, 'name': 'Knife'},
                'shield': {'damage': 8, 'speed': 6, 'crit_chance': 0.02, 'name': 'Shield'}
            };
            
            const FACTIONS = {
                'order': 'Order of the Silver Crusade',
                'shadow': 'Shadow Covenant',
                'wilderness': 'Wilderness Tribe'
            };
            
            const ABILITIES = {
                'order': ['Healing Light', 'Shield of Faith', 'Righteous Fury', 'Purification'],
                'shadow': ['Shadow Strike', 'Vanish', 'Shadow Clone', 'Assassinate'],
                'wilderness': ['Wild Growth', 'Thorn Barrier', 'Nature\'s Wrath', 'Spirit Form']
            };
            
            // Initialize when DOM loads
            document.addEventListener('DOMContentLoaded', function() {
                console.log('DOM loaded');
                updateAbilities();
                setupForm();
            });
            
            // Update abilities display
            function updateAbilities() {
                const faction = document.getElementById('faction').value;
                const display = document.getElementById('abilities-display');
                const abilities = ABILITIES[faction];
                
                display.innerHTML = abilities.map(ability => 
                    '<div style="background: rgba(255,255,255,0.1); padding: 5px; margin: 2px; border-radius: 3px;">' + ability + '</div>'
                ).join('');
            }
            
            // Setup form submission
            function setupForm() {
                const form = document.getElementById('character-form');
                if (form) {
                    form.addEventListener('submit', handleFormSubmit);
                    console.log('Form setup complete');
                }
            }
            
            // Handle form submission
            async function handleFormSubmit(e) {
                e.preventDefault();
                console.log('Form submitted');
                
                const formData = new FormData(e.target);
                const playerData = Object.fromEntries(formData.entries());
                console.log('Player data:', playerData);
                
                try {
                    const response = await fetch('/create-player', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(playerData)
                    });
                    
                    const result = await response.json();
                    console.log('Response:', result);
                    
                    if (result.success) {
                        currentPlayer = result.player;
                        showGameInterface();
                        updatePlayerDisplay();
                    } else {
                        alert('Error: ' + result.error);
                    }
                } catch (error) {
                    console.error('Error:', error);
                    alert('Error: ' + error.message);
                }
            }
            
            // Show sections
            function showSection(sectionId) {
                document.querySelectorAll('.game-section').forEach(section => {
                    section.classList.remove('active');
                });
                document.getElementById(sectionId).classList.add('active');
            }
            
            function showGameInterface() {
                showSection('game-interface');
            }
            
            function showLeaderboard() {
                showSection('leaderboard');
                loadLeaderboard();
            }
            
            function showCharacterInfo() {
                showSection('character-info');
                loadCharacterInfo();
            }
            
            // Update player display
            function updatePlayerDisplay() {
                if (!currentPlayer) return;
                
                document.getElementById('player-name').textContent = currentPlayer.username;
                document.getElementById('rating').textContent = currentPlayer.rating;
                document.getElementById('wins').textContent = currentPlayer.wins;
                document.getElementById('losses').textContent = currentPlayer.losses;
                
                const weapon1 = WEAPONS[currentPlayer.weapon1];
                const weapon2 = WEAPONS[currentPlayer.weapon2];
                
                const damage = Math.floor((weapon1.damage + weapon2.damage) * 0.75);
                const speed = Math.floor((weapon1.speed + weapon2.speed) * 0.8);
                const crit = Math.floor((weapon1.crit_chance + weapon2.crit_chance) * 0.6 * 100);
                
                document.getElementById('damage').textContent = damage;
                document.getElementById('speed').textContent = speed;
                document.getElementById('crit').textContent = crit + '%';
            }
            
            // Find duel
            async function findDuel() {
                if (!currentPlayer) return;
                
                const duelLog = document.getElementById('duel-log');
                duelLog.style.display = 'block';
                duelLog.innerHTML = '<div class="loading">Finding opponent...</div>';
                
                try {
                    const response = await fetch('/duel', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({player_id: currentPlayer.id})
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        displayDuelResult(result);
                        currentPlayer = result.updated_player;
                        updatePlayerDisplay();
                    } else {
                        duelLog.innerHTML = '<div class="error">Error: ' + result.error + '</div>';
                    }
                } catch (error) {
                    duelLog.innerHTML = '<div class="error">Error: ' + error.message + '</div>';
                }
            }
            
            // Display duel result
            function displayDuelResult(result) {
                const duelLog = document.getElementById('duel-log');
                const timestamp = new Date().toLocaleTimeString();
                
                let html = '<div><strong>[' + timestamp + ']</strong> Duel Results:</div>';
                html += '<div>⚔️ ' + result.player_name + ' vs ' + result.opponent_name + '</div>';
                html += '<div>💥 Damage dealt: ' + result.player_damage + '</div>';
                html += '<div>💥 Damage received: ' + result.opponent_damage + '</div>';
                
                if (result.winner === currentPlayer.id) {
                    html += '<div class="success">🏆 Victory! (+20 rating)</div>';
                } else {
                    html += '<div class="error">💀 Defeat! (-15 rating)</div>';
                }
                
                html += '<div>New Rating: ' + result.updated_player.rating + '</div><br>';
                duelLog.innerHTML = html + duelLog.innerHTML;
            }
            
            // Load leaderboard
            async function loadLeaderboard() {
                try {
                    const response = await fetch('/leaderboard');
                    const players = await response.json();
                    const content = document.getElementById('leaderboard-content');
                    
                    if (players.length === 0) {
                        content.innerHTML = '<div class="error">No players found</div>';
                        return;
                    }
                    
                    content.innerHTML = players.map(function(player, index) {
                        return '<div class="leaderboard-entry">' +
                            '<div><strong>#' + (index + 1) + '</strong> ' + player.username + '</div>' +
                            '<div class="rating">' + player.rating + '</div>' +
                            '<div class="wins">' + player.wins + 'W</div>' +
                            '<div class="losses">' + player.losses + 'L</div>' +
                            '</div>';
                    }).join('');
                } catch (error) {
                    document.getElementById('leaderboard-content').innerHTML = 
                        '<div class="error">Error: ' + error.message + '</div>';
                }
            }
            
            // Load character info
            function loadCharacterInfo() {
                if (!currentPlayer) return;
                
                const details = document.getElementById('character-details');
                const abilities = ABILITIES[currentPlayer.faction];
                
                details.innerHTML = 
                    '<div class="stats-display">' +
                        '<div class="stat-card">' +
                            '<div>Faction</div>' +
                            '<div class="stat-value">' + FACTIONS[currentPlayer.faction] + '</div>' +
                        '</div>' +
                        '<div class="stat-card">' +
                            '<div>Armor</div>' +
                            '<div class="stat-value">' + currentPlayer.armor_type.charAt(0).toUpperCase() + currentPlayer.armor_type.slice(1) + '</div>' +
                        '</div>' +
                        '<div class="stat-card">' +
                            '<div>Primary Weapon</div>' +
                            '<div class="stat-value">' + WEAPONS[currentPlayer.weapon1].name + '</div>' +
                        '</div>' +
                        '<div class="stat-card">' +
                            '<div>Secondary Weapon</div>' +
                            '<div class="stat-value">' + WEAPONS[currentPlayer.weapon2].name + '</div>' +
                        '</div>' +
                    '</div>' +
                    '<h3>Abilities:</h3>' +
                    '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-top: 10px;">' +
                        abilities.map(function(ability) {
                            return '<div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; text-align: center;">' + ability + '</div>';
                        }).join('') +
                    '</div>';
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

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
    uvicorn.run(app, host="0.0.0.0", port=8001)
