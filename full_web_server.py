#!/usr/bin/env python3
"""
Full-Featured IdleDuelist Web Server
Includes all main game features: faction passives, armor set bonuses, ability counterplay, etc.
"""

import os
import json
import sqlite3
import random
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional

# Import the main game logic
from idle_duelist import (
    PlayerData, FACTION_DATA, ARMOR_SET_BONUSES, ABILITY_DATA, 
    ABILITY_COUNTERS, EQUIPMENT_DATA, WEAPON_DATA
)

app = FastAPI(title="IdleDuelist Full Game", version="1.0.0")

# Database setup
def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('full_game.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize the database with tables"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Players table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    player_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Duel logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS duels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player1_id TEXT NOT NULL,
                    player2_id TEXT NOT NULL,
                    winner_id TEXT,
                    duel_log TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            print("✅ Full game database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

# Web Player class that extends the main game's PlayerData
class WebPlayer(PlayerData):
    def __init__(self, player_id: str, username: str):
        super().__init__(player_id, username)
        self.rating = 1200  # Starting rating
        self.wins = 0
        self.losses = 0
        self.duel_history = []

    def to_dict(self):
        """Convert player to dictionary for JSON serialization"""
        data = super().to_dict()
        data.update({
            'rating': self.rating,
            'wins': self.wins,
            'losses': self.losses,
            'duel_history': self.duel_history
        })
        return data

    @classmethod
    def from_dict(cls, data: dict):
        """Create player from dictionary"""
        player = cls(data['id'], data['username'])
        # Set all attributes from the data
        for key, value in data.items():
            if hasattr(player, key):
                setattr(player, key, value)
        return player

# Request/Response models
class PlayerRequest(BaseModel):
    username: str
    faction: str
    armor_type: str
    weapon1: str
    weapon2: str

class DuelRequest(BaseModel):
    player_id: str

# Routes
@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main HTML page"""
    try:
        with open("static/full_game.html", "r", encoding="utf-8") as f:
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
    """Create a new player with full game features"""
    try:
        player_id = f"web_{random.randint(10000, 99999)}"
        player = WebPlayer(player_id, player_data['username'])
        
        # Set faction and abilities
        player.faction = player_data['faction']
        faction_data = FACTION_DATA[player.faction]
        player.abilities = faction_data['abilities'][:4]  # First 4 abilities
        
        # Set armor type and generate equipment
        armor_type = player_data['armor_type']
        player.armor_type = armor_type
        
        # Generate full armor set
        armor_slots = ['helmet', 'armor', 'pants', 'boots', 'gloves']
        for slot in armor_slots:
            armor_key = f"{armor_type}_{slot}"
            if armor_key in EQUIPMENT_DATA['armor']:
                armor_data = EQUIPMENT_DATA['armor'][armor_key].copy()
                armor_data['slot'] = slot
                armor_data['rarity'] = 'rare'  # Give good starting gear
                player.equipment[slot] = armor_data
        
        # Set weapons
        weapon1_key = f"weapon_{player_data['weapon1']}"
        weapon2_key = f"weapon_{player_data['weapon2']}"
        
        if weapon1_key in WEAPON_DATA:
            weapon_data = WEAPON_DATA[weapon1_key].copy()
            weapon_data['rarity'] = 'rare'
            player.equipment['main_hand'] = weapon_data
            
        if weapon2_key in WEAPON_DATA:
            weapon_data = WEAPON_DATA[weapon2_key].copy()
            weapon_data['rarity'] = 'rare'
            player.equipment['off_hand'] = weapon_data
        
        # Save to database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO players (id, username, player_data) 
                VALUES (?, ?, ?)
            ''', (player_id, player.username, json.dumps(player.to_dict())))
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
async def duel(request: DuelRequest):
    """Execute a duel with full game features"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM players WHERE id = ?', (request.player_id,))
            player_row = cursor.fetchone()
            
            if not player_row:
                return JSONResponse({"success": False, "error": "Player not found"})
            
            player_data = json.loads(player_row['player_data'])
            player = WebPlayer.from_dict(player_data)
            
            # Create a bot opponent with similar rating
            bot_id = f"bot_{random.randint(10000, 99999)}"
            bot = WebPlayer(bot_id, f"Bot_{random.randint(100, 999)}")
            bot.rating = player.rating + random.randint(-100, 100)
            
            # Generate bot equipment and abilities
            factions = list(FACTION_DATA.keys())
            armor_types = ['cloth', 'leather', 'metal']
            weapons = list(WEAPON_DATA.keys())
            
            bot.faction = random.choice(factions)
            bot.armor_type = random.choice(armor_types)
            
            # Set bot abilities
            faction_data = FACTION_DATA[bot.faction]
            bot.abilities = faction_data['abilities'][:4]
            
            # Generate bot equipment
            for slot in ['helmet', 'armor', 'pants', 'boots', 'gloves']:
                armor_key = f"{bot.armor_type}_{slot}"
                if armor_key in EQUIPMENT_DATA['armor']:
                    armor_data = EQUIPMENT_DATA['armor'][armor_key].copy()
                    armor_data['slot'] = slot
                    armor_data['rarity'] = 'rare'
                    bot.equipment[slot] = armor_data
            
            # Set bot weapons
            bot_weapons = random.sample(weapons, 2)
            for i, weapon_key in enumerate(['main_hand', 'off_hand']):
                if i < len(bot_weapons):
                    weapon_data = WEAPON_DATA[bot_weapons[i]].copy()
                    weapon_data['rarity'] = 'rare'
                    bot.equipment[weapon_key] = weapon_data
            
            # Execute duel using main game logic
            duel_result = execute_duel(player, bot)
            
            # Update player stats
            if duel_result['winner'] == player.id:
                player.wins += 1
                player.rating += 20
            else:
                player.losses += 1
                player.rating = max(800, player.rating - 15)
            
            # Save updated player
            cursor.execute('''
                UPDATE players SET player_data = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (json.dumps(player.to_dict()), player.id))
            
            # Save duel log
            cursor.execute('''
                INSERT INTO duels (player1_id, player2_id, winner_id, duel_log)
                VALUES (?, ?, ?, ?)
            ''', (player.id, bot.id, duel_result['winner'], json.dumps(duel_result)))
            
            conn.commit()
            
            return JSONResponse({
                "success": True,
                "duel_result": duel_result,
                "updated_player": player.to_dict()
            })
            
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

def execute_duel(player1: WebPlayer, player2: WebPlayer) -> dict:
    """Execute a duel using the main game's combat logic"""
    # Reset health for duel
    player1.current_hp = player1.get_total_hp()
    player2.current_hp = player2.get_total_hp()
    
    # Determine turn order based on speed
    if player1.get_total_speed() >= player2.get_total_speed():
        attacker, defender = player1, player2
        attacker_type, defender_type = "player", "opponent"
    else:
        attacker, defender = player2, player1
        attacker_type, defender_type = "opponent", "player"
    
    turn_count = 0
    max_turns = 50  # Prevent infinite loops
    duel_log = []
    
    while player1.current_hp > 0 and player2.current_hp > 0 and turn_count < max_turns:
        turn_count += 1
        
        # Get action (ability or attack)
        action = get_player_action(attacker)
        
        if action.startswith('ability_'):
            ability_name = action.replace('ability_', '')
            if ability_name in attacker.abilities:
                ability_result = execute_ability(attacker, defender, ability_name, attacker_type)
                duel_log.extend(ability_result.get('log', []))
        else:
            # Regular attack
            attack_result = execute_attack(attacker, defender, attacker_type)
            duel_log.extend(attack_result.get('log', []))
        
        # Check if duel is over
        if defender.current_hp <= 0:
            break
        
        # Switch turns
        attacker, defender = defender, attacker
        attacker_type, defender_type = defender_type, attacker_type
    
    # Determine winner
    if player1.current_hp > 0:
        winner = player1.id
        result_text = f"🎉 {player1.username} wins the duel!"
    else:
        winner = player2.id
        result_text = f"💀 {player2.username} wins the duel!"
    
    return {
        "winner": winner,
        "player1_hp": player1.current_hp,
        "player2_hp": player2.current_hp,
        "turns": turn_count,
        "log": duel_log,
        "result": result_text
    }

def get_player_action(player: WebPlayer) -> str:
    """Get player action (ability or attack)"""
    # 70% chance to use ability, 30% chance to attack
    if random.random() < 0.7 and player.abilities:
        ability = random.choice(player.abilities)
        return f"ability_{ability}"
    else:
        return "attack"

def execute_ability(attacker: WebPlayer, defender: WebPlayer, ability_name: str, attacker_type: str) -> dict:
    """Execute an ability using main game logic"""
    log = []
    
    if ability_name not in ABILITY_DATA:
        log.append(f"❌ {attacker.username} tries to use unknown ability: {ability_name}")
        return {"log": log}
    
    ability = ABILITY_DATA[ability_name]
    log.append(f"⚡ {attacker.username} uses {ability['name']}!")
    
    # Apply ability effects
    if 'damage_multiplier' in ability:
        base_damage = attacker.get_total_damage()
        damage = int(base_damage * ability['damage_multiplier'])
        
        # Check for ability counterplay
        if ability_name in ABILITY_COUNTERS:
            counter_abilities = ABILITY_COUNTERS[ability_name]
            if any(ability in defender.active_buffs for ability in counter_abilities):
                log.append(f"🛡️ {defender.username}'s ability counters {ability['name']}!")
                damage = max(1, damage // 2)  # Reduce damage by half
        
        log.append(f"💥 {defender.username} takes {damage} damage!")
        defender.current_hp = max(0, defender.current_hp - damage)
    
    if 'healing' in ability:
        healing = ability['healing']
        if isinstance(healing, dict) and 'amount' in healing:
            heal_amount = healing['amount']
            max_hp = attacker.get_total_hp()
            attacker.current_hp = min(max_hp, attacker.current_hp + heal_amount)
            log.append(f"💚 {attacker.username} heals for {heal_amount} HP!")
    
    # Apply status effects
    if 'effects' in ability:
        for effect, value in ability['effects'].items():
            if effect not in defender.active_buffs:
                defender.active_buffs[effect] = value
                log.append(f"✨ {defender.username} is affected by {effect}!")
    
    return {"log": log}

def execute_attack(attacker: WebPlayer, defender: WebPlayer, attacker_type: str) -> dict:
    """Execute a regular attack"""
    log = []
    
    base_damage = attacker.get_total_damage()
    damage = base_damage
    
    # Check for critical hit
    crit_chance = attacker.get_total_crit_chance()
    is_crit = random.random() < crit_chance
    
    if is_crit:
        damage *= 2
        log.append(f"💥 {attacker.username} lands a critical hit for {damage} damage!")
    else:
        log.append(f"⚔️ {attacker.username} attacks for {damage} damage!")
    
    # Apply damage
    defender.current_hp = max(0, defender.current_hp - damage)
    
    return {"log": log}

@app.get("/leaderboard")
async def get_leaderboard():
    """Get the leaderboard"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM players 
                ORDER BY rating DESC 
                LIMIT 20
            ''')
            players = cursor.fetchall()
            
            leaderboard = []
            for i, player_row in enumerate(players):
                player_data = json.loads(player_row['player_data'])
                leaderboard.append({
                    'rank': i + 1,
                    'username': player_data['username'],
                    'rating': player_data.get('rating', 1200),
                    'wins': player_data.get('wins', 0),
                    'losses': player_data.get('losses', 0),
                    'faction': FACTION_DATA[player_data['faction']]['name'],
                    'armor_type': player_data['armor_type'].title()
                })
            
            return JSONResponse({
                "success": True,
                "leaderboard": leaderboard
            })
            
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

@app.get("/game-data")
async def get_game_data():
    """Get all game data for the frontend"""
    return JSONResponse({
        "factions": FACTION_DATA,
        "armor_set_bonuses": ARMOR_SET_BONUSES,
        "abilities": ABILITY_DATA,
        "ability_counters": ABILITY_COUNTERS,
        "equipment": EQUIPMENT_DATA,
        "weapons": WEAPON_DATA
    })

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({"status": "healthy", "full_game": True})

if __name__ == "__main__":
    init_database()
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
