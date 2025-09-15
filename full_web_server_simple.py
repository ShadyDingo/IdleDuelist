#!/usr/bin/env python3
"""
Full-Featured IdleDuelist Web Server (Simplified)
Includes all main game features without Kivy dependencies
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

app = FastAPI(title="IdleDuelist Full Game", version="1.0.0")

# Game data (copied from idle_duelist.py to avoid Kivy dependencies)
FACTION_DATA = {
    'order_of_the_silver_crusade': {
        'name': 'Order of the Silver Crusade',
        'description': 'Holy warriors focused on defense and healing',
        'passive': 'divine_protection',  # 10% damage reduction
        'passive_value': 0.10,
        'secondary_passive': 'holy_resistance',  # Immune to poison effects
        'secondary_value': True,
        'abilities': ['divine_strike', 'shield_of_faith', 'healing_light', 'righteous_fury', 'purification'],
        'theme_colors': {'primary': (0.8, 0.8, 1.0), 'secondary': (1.0, 1.0, 0.8)}
    },
    'shadow_covenant': {
        'name': 'Shadow Covenant',
        'description': 'Stealthy assassins focused on critical hits',
        'passive': 'shadow_mastery',  # 15% increased crit chance
        'passive_value': 0.15,
        'secondary_passive': 'stealth_damage',  # +10% damage when invisible
        'secondary_value': 0.10,
        'abilities': ['shadow_strike', 'vanish', 'poison_blade', 'assassinate', 'shadow_clone'],
        'theme_colors': {'primary': (0.3, 0.1, 0.5), 'secondary': (0.5, 0.1, 0.3)}
    },
    'wilderness_tribe': {
        'name': 'Wilderness Tribe',
        'description': 'Nature mages focused on adaptability',
        'passive': 'natures_blessing',  # 5% HP regeneration per turn
        'passive_value': 0.05,
        'secondary_passive': 'nature_affinity',  # +10% damage vs slowed enemies
        'secondary_value': 0.10,
        'abilities': ['natures_wrath', 'thorn_barrier', 'wild_growth', 'earthquake', 'spirit_form'],
        'theme_colors': {'primary': (0.2, 0.8, 0.2), 'secondary': (0.4, 0.6, 0.2)}
    }
}

# Armor Set Bonuses - 3-piece and 5-piece combinations
ARMOR_SET_BONUSES = {
    'cloth': {
        'name': 'Lightfoot',
        '3_piece': {
            'name': 'Swift Step',
            'effects': {'dodge_bonus': 0.05, 'speed_bonus': 2},  # +5% dodge, +2 speed
            'description': 'Enhanced mobility and evasion'
        },
        '5_piece': {
            'name': 'Wind Walker',
            'effects': {'dodge_bonus': 0.10, 'speed_bonus': 5, 'crit_chance': 0.05},  # +10% dodge, +5 speed, +5% crit
            'description': 'Master of speed and precision strikes'
        }
    },
    'leather': {
        'name': 'Balanced',
        '3_piece': {
            'name': 'Adaptive Combat',
            'effects': {'stat_bonus': 0.05, 'armor_penetration': 1},  # +5% to all stats, +1 armor pen
            'description': 'Versatile fighting techniques'
        },
        '5_piece': {
            'name': 'Perfect Balance',
            'effects': {'stat_bonus': 0.10, 'armor_penetration': 3, 'damage_bonus': 0.05},  # +10% to all stats, +3 armor pen, +5% damage
            'description': 'Harmonious mastery of all combat arts'
        }
    },
    'metal': {
        'name': 'Fortress',
        '3_piece': {
            'name': 'Iron Will',
            'effects': {'defense_bonus': 3, 'damage_reduction': 0.05},  # +3 defense, +5% damage reduction
            'description': 'Unwavering defensive stance'
        },
        '5_piece': {
            'name': 'Immovable Mountain',
            'effects': {'defense_bonus': 8, 'damage_reduction': 0.10, 'damage_reflect': 0.05},  # +8 defense, +10% damage reduction, +5% damage reflect
            'description': 'Unbreakable fortress that strikes back'
        }
    }
}

# Ability System
ABILITY_DATA = {
    'divine_strike': {
        'name': 'Divine Strike',
        'description': 'Holy attack that ignores armor',
        'damage_multiplier': 1.5,
        'armor_penetration': 999,  # Ignores all armor
        'cooldown': 3,
        'faction': 'order_of_the_silver_crusade'
    },
    'shield_of_faith': {
        'name': 'Shield of Faith',
        'description': 'Grants temporary invulnerability',
        'damage_reduction': 1.0,  # 100% damage reduction
        'duration': 2,
        'cooldown': 5,
        'faction': 'order_of_the_silver_crusade'
    },
    'healing_light': {
        'name': 'Healing Light',
        'description': 'Restores health over time',
        'healing': {'amount': 15, 'duration': 3},
        'cooldown': 4,
        'faction': 'order_of_the_silver_crusade'
    },
    'righteous_fury': {
        'name': 'Righteous Fury',
        'description': 'Increases damage for next attack',
        'damage_multiplier': 1.8,
        'cooldown': 3,
        'faction': 'order_of_the_silver_crusade'
    },
    'purification': {
        'name': 'Purification',
        'description': 'Removes all negative effects',
        'cleanse': True,
        'cooldown': 4,
        'faction': 'order_of_the_silver_crusade'
    },
    'shadow_strike': {
        'name': 'Shadow Strike',
        'description': 'Guaranteed critical hit from shadows',
        'damage_multiplier': 1.8,
        'guaranteed_crit': True,
        'cooldown': 4,
        'faction': 'shadow_covenant'
    },
    'vanish': {
        'name': 'Vanish',
        'description': 'Become invisible for 2 turns',
        'effects': {'invisible': 2},
        'cooldown': 5,
        'faction': 'shadow_covenant'
    },
    'poison_blade': {
        'name': 'Poison Blade',
        'description': 'Poisons enemy for damage over time',
        'effects': {'poison': 3},
        'cooldown': 3,
        'faction': 'shadow_covenant'
    },
    'assassinate': {
        'name': 'Assassinate',
        'description': 'High damage attack that ignores buffs',
        'damage_multiplier': 2.0,
        'ignores_buffs': True,
        'cooldown': 5,
        'faction': 'shadow_covenant'
    },
    'shadow_clone': {
        'name': 'Shadow Clone',
        'description': 'Creates a clone that attacks once',
        'clone_attack': True,
        'cooldown': 6,
        'faction': 'shadow_covenant'
    },
    'natures_wrath': {
        'name': "Nature's Wrath",
        'description': 'Powerful nature attack that reveals stealth',
        'damage_multiplier': 1.6,
        'reveals_stealth': True,
        'cooldown': 4,
        'faction': 'wilderness_tribe'
    },
    'thorn_barrier': {
        'name': 'Thorn Barrier',
        'description': 'Reflects damage back to attackers',
        'damage_reflect': 0.3,
        'duration': 3,
        'cooldown': 4,
        'faction': 'wilderness_tribe'
    },
    'wild_growth': {
        'name': 'Wild Growth',
        'description': 'Increases all stats temporarily',
        'effects': {'stat_buff': 0.2},
        'duration': 3,
        'cooldown': 5,
        'faction': 'wilderness_tribe'
    },
    'earthquake': {
        'name': 'Earthquake',
        'description': 'Stuns enemy and deals area damage',
        'damage_multiplier': 1.4,
        'effects': {'stun': 1},
        'cooldown': 5,
        'faction': 'wilderness_tribe'
    },
    'spirit_form': {
        'name': 'Spirit Form',
        'description': 'Reduces incoming damage and immune to stun',
        'damage_reduction': 0.4,
        'stun_immunity': True,
        'duration': 3,
        'cooldown': 6,
        'faction': 'wilderness_tribe'
    }
}

# Ability Counterplay System
ABILITY_COUNTERS = {
    'shield_of_faith': ['divine_strike'],      # Divine Strike ignores invulnerability
    'vanish': ['natures_wrath'],               # Nature's Wrath reveals invisible enemies
    'poison_blade': ['purification'],          # Purification removes poison effects
    'earthquake': ['spirit_form'],             # Spirit Form immune to stun effects
    'shadow_strike': ['thorn_barrier'],        # Thorn Barrier reflects guaranteed crits
    'assassinate': ['shield_of_faith'],        # Shield of Faith prevents execution
    'healing_light': ['poison_blade'],         # Poison counters healing over time
    'righteous_fury': ['spirit_form'],         # Spirit Form reduces damage buffs
    'wild_growth': ['assassinate'],            # Assassinate ignores stat buffs
    'shadow_clone': ['earthquake'],            # Earthquake hits both original and clone
}

# Equipment data
EQUIPMENT_DATA = {
    'armor': {
        # CLOTH: High speed, low defense, good for dodging builds
        'cloth_helmet': {'name': 'Cloth Helmet', 'speed': 6, 'defense': 1},
        'cloth_armor': {'name': 'Cloth Armor', 'speed': 8, 'defense': 2},
        'cloth_pants': {'name': 'Cloth Pants', 'speed': 5, 'defense': 1},
        'cloth_boots': {'name': 'Cloth Boots', 'speed': 7, 'defense': 1},
        'cloth_gloves': {'name': 'Cloth Gloves', 'speed': 4, 'defense': 1},
        
        # LEATHER: Balanced stats, versatile builds
        'leather_helmet': {'name': 'Leather Helmet', 'speed': 4, 'defense': 3},
        'leather_armor': {'name': 'Leather Armor', 'speed': 5, 'defense': 4},
        'leather_pants': {'name': 'Leather Pants', 'speed': 3, 'defense': 3},
        'leather_boots': {'name': 'Leather Boots', 'speed': 4, 'defense': 3},
        'leather_gloves': {'name': 'Leather Gloves', 'speed': 3, 'defense': 2},
        
        # METAL: High defense, low speed, tank builds
        'metal_helmet': {'name': 'Metal Helmet', 'speed': 1, 'defense': 6},
        'metal_armor': {'name': 'Metal Armor', 'speed': 2, 'defense': 8},
        'metal_pants': {'name': 'Metal Pants', 'speed': 1, 'defense': 6},
        'metal_boots': {'name': 'Metal Boots', 'speed': 2, 'defense': 5},
        'metal_gloves': {'name': 'Metal Gloves', 'speed': 1, 'defense': 4},
    },
    'weapons': {
        'weapon_sword': {'name': 'Sword', 'attack': 15, 'speed': 3, 'crit_chance': 0.05},
        'weapon_axe': {'name': 'Axe', 'attack': 18, 'speed': 2, 'crit_chance': 0.08},
        'weapon_bow': {'name': 'Bow', 'attack': 12, 'speed': 4, 'crit_chance': 0.10},
        'weapon_crossbow': {'name': 'Crossbow', 'attack': 16, 'speed': 2, 'crit_chance': 0.12},
        'weapon_knife': {'name': 'Knife', 'attack': 10, 'speed': 5, 'crit_chance': 0.15},
        'weapon_mace': {'name': 'Mace', 'attack': 14, 'speed': 3, 'crit_chance': 0.06},
        'weapon_hammer': {'name': 'Hammer', 'attack': 20, 'speed': 1, 'crit_chance': 0.04},
        'weapon_shield': {'name': 'Shield', 'attack': 8, 'speed': 2, 'defense': 5},
        'weapon_staff': {'name': 'Staff', 'attack': 13, 'speed': 3, 'crit_chance': 0.07},
    }
}

WEAPON_DATA = EQUIPMENT_DATA['weapons']

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

# Web Player class
class WebPlayer:
    def __init__(self, player_id: str, username: str):
        self.id = player_id
        self.username = username
        self.faction = 'order_of_the_silver_crusade'
        self.armor_type = 'cloth'
        self.abilities = []
        self.equipment = {}
        self.rating = 1200
        self.wins = 0
        self.losses = 0
        self.current_hp = 100
        self.active_buffs = {}
        self.duel_history = []

    def to_dict(self):
        """Convert player to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'username': self.username,
            'faction': self.faction,
            'armor_type': self.armor_type,
            'abilities': self.abilities,
            'equipment': self.equipment,
            'rating': self.rating,
            'wins': self.wins,
            'losses': self.losses,
            'current_hp': self.current_hp,
            'active_buffs': self.active_buffs,
            'duel_history': self.duel_history
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create player from dictionary"""
        player = cls(data['id'], data['username'])
        player.faction = data.get('faction', 'order_of_the_silver_crusade')
        player.armor_type = data.get('armor_type', 'cloth')
        player.abilities = data.get('abilities', [])
        player.equipment = data.get('equipment', {})
        player.rating = data.get('rating', 1200)
        player.wins = data.get('wins', 0)
        player.losses = data.get('losses', 0)
        player.current_hp = data.get('current_hp', 100)
        player.active_buffs = data.get('active_buffs', {})
        player.duel_history = data.get('duel_history', [])
        return player

    def get_total_hp(self):
        """Calculate total HP"""
        base_hp = 100
        constitution_bonus = 0
        
        # Add equipment bonuses
        for item in self.equipment.values():
            if 'constitution' in item:
                constitution_bonus += item['constitution']
        
        return base_hp + constitution_bonus

    def get_total_damage(self):
        """Calculate total damage"""
        base_damage = 20
        
        # Add weapon damage
        for slot in ['main_hand', 'off_hand']:
            if slot in self.equipment:
                weapon = self.equipment[slot]
                if 'attack' in weapon:
                    base_damage += weapon['attack']
        
        # Add faction passive
        faction_data = FACTION_DATA[self.faction]
        if faction_data['passive'] == 'shadow_mastery':
            base_damage = int(base_damage * 1.05)  # Small damage bonus
        
        return base_damage

    def get_total_defense(self):
        """Calculate total defense"""
        base_defense = 5
        
        # Add armor defense
        for slot in ['helmet', 'armor', 'pants', 'boots', 'gloves']:
            if slot in self.equipment:
                armor = self.equipment[slot]
                if 'defense' in armor:
                    base_defense += armor['defense']
        
        # Add faction passive
        faction_data = FACTION_DATA[self.faction]
        if faction_data['passive'] == 'divine_protection':
            base_defense = int(base_defense * 1.1)  # 10% defense bonus
        
        return base_defense

    def get_total_speed(self):
        """Calculate total speed"""
        base_speed = 10
        
        # Add armor speed
        for slot in ['helmet', 'armor', 'pants', 'boots', 'gloves']:
            if slot in self.equipment:
                armor = self.equipment[slot]
                if 'speed' in armor:
                    base_speed += armor['speed']
        
        # Add weapon speed
        for slot in ['main_hand', 'off_hand']:
            if slot in self.equipment:
                weapon = self.equipment[slot]
                if 'speed' in weapon:
                    base_speed += weapon['speed']
        
        return base_speed

    def get_total_crit_chance(self):
        """Calculate total critical hit chance"""
        base_crit = 0.05
        
        # Add weapon crit chance
        for slot in ['main_hand', 'off_hand']:
            if slot in self.equipment:
                weapon = self.equipment[slot]
                if 'crit_chance' in weapon:
                    base_crit += weapon['crit_chance']
        
        # Add faction passive
        faction_data = FACTION_DATA[self.faction]
        if faction_data['passive'] == 'shadow_mastery':
            base_crit += faction_data['passive_value']  # 15% crit bonus
        
        return min(0.95, base_crit)  # Cap at 95%

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
