#!/usr/bin/env python3
"""
Full-Featured IdleDuelist Web Server (Simplified)
Includes all main game features without Kivy dependencies
"""

import os
import json
import sqlite3
import random
import bcrypt
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Optional

app = FastAPI(title="IdleDuelist Full Game", version="1.0.0")

# Mount static files for assets
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

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
        'weapon_fists': {'name': 'Fists', 'attack': 5, 'speed': 6, 'crit_chance': 0.02},
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

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

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
                    password_hash TEXT NOT NULL,
                    player_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Check if password_hash column exists, if not add it
            cursor.execute("PRAGMA table_info(players)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'password_hash' not in columns:
                print("Adding password_hash column to existing players table...")
                cursor.execute('ALTER TABLE players ADD COLUMN password_hash TEXT DEFAULT ""')
                print("✅ Database schema updated with password support")
            else:
                print("✅ Database schema already up to date")
            
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
            
            # Generate AI bot characters if none exist
            generate_ai_bots()
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

def generate_ai_bots():
    """Generate 10 AI bot characters with random loadouts"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if we already have AI bots
            cursor.execute("SELECT COUNT(*) FROM players WHERE username LIKE 'Bot_%'")
            bot_count = cursor.fetchone()[0]
            
            if bot_count >= 10:
                print(f"✅ {bot_count} AI bots already exist")
                return
            
            print(f"Generating AI bots... (found {bot_count}, need 10)")
            
            # Generate 10 AI bots with random loadouts
            for i in range(10):
                bot_id = f"bot_{random.randint(10000, 99999)}"
                bot_username = f"Bot_{random.randint(100, 999)}"
                
                # Check if username already exists
                cursor.execute("SELECT COUNT(*) FROM players WHERE username = ?", (bot_username,))
                while cursor.fetchone()[0] > 0:
                    bot_username = f"Bot_{random.randint(100, 999)}"
                    cursor.execute("SELECT COUNT(*) FROM players WHERE username = ?", (bot_username,))
                
                # Create bot player
                bot = WebPlayer(bot_id, bot_username)
                
                # Random faction
                bot.faction = random.choice(list(FACTION_DATA.keys()))
                faction_data = FACTION_DATA[bot.faction]
                bot.abilities = faction_data['abilities'][:4]  # First 4 abilities
                
                # Random armor type
                bot.armor_type = random.choice(['cloth', 'leather', 'metal'])
                
                # Generate full armor set
                armor_slots = ['helmet', 'armor', 'pants', 'boots', 'gloves']
                for slot in armor_slots:
                    armor_key = f"{bot.armor_type}_{slot}"
                    if armor_key in EQUIPMENT_DATA['armor']:
                        armor_data = EQUIPMENT_DATA['armor'][armor_key].copy()
                        armor_data['slot'] = slot
                        armor_data['rarity'] = 'rare'  # Give good starting gear
                        bot.equipment[slot] = armor_data
                
                # Random weapons
                weapon1_name = random.choice(['sword', 'axe', 'bow', 'crossbow', 'knife', 'mace', 'hammer', 'shield', 'staff', 'fists'])
                weapon2_name = random.choice(['sword', 'axe', 'bow', 'crossbow', 'knife', 'mace', 'hammer', 'shield', 'staff', 'fists'])
                bot.weapon1 = weapon1_name
                bot.weapon2 = weapon2_name
                
                # Set weapon equipment
                weapon1_key = f"weapon_{weapon1_name}"
                weapon2_key = f"weapon_{weapon2_name}"
                
                if weapon1_key in WEAPON_DATA:
                    weapon_data = WEAPON_DATA[weapon1_key].copy()
                    weapon_data['slot'] = 'main_hand'
                    weapon_data['rarity'] = 'rare'
                    bot.equipment['main_hand'] = weapon_data
                
                if weapon2_key in WEAPON_DATA:
                    weapon_data = WEAPON_DATA[weapon2_key].copy()
                    weapon_data['slot'] = 'off_hand'
                    weapon_data['rarity'] = 'rare'
                    bot.equipment['off_hand'] = weapon_data
                
                # Calculate initial stats
                initial_stats = calculatePlayerStats(bot.to_dict())
                bot.max_hp = initial_stats['hp']
                bot.current_hp = initial_stats['hp']
                
                # Give bots some wins/losses to make them realistic
                bot.wins = random.randint(0, 50)
                bot.losses = random.randint(0, 50)
                bot.rating = 1200 + random.randint(-200, 200)
                
                # Save bot to database
                cursor.execute('''
                    INSERT INTO players (id, username, password_hash, player_data) 
                    VALUES (?, ?, ?, ?)
                ''', (bot.id, bot.username, hash_password("bot_password"), json.dumps(bot.to_dict())))
            
            conn.commit()
            print("✅ Generated 10 AI bot characters with random loadouts")
            
    except Exception as e:
        print(f"❌ Failed to generate AI bots: {e}")

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
        self.max_hp = 100
        self.weapon1 = 'fists'  # Default to fists if no weapons
        self.weapon2 = 'fists'  # Default to fists if no weapons
        self.active_buffs = {}
        self.status_effects = {}
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
            'max_hp': self.max_hp,
            'weapon1': self.weapon1,
            'weapon2': self.weapon2,
            'active_buffs': self.active_buffs,
            'status_effects': self.status_effects,
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
        player.max_hp = data.get('max_hp', 100)
        player.weapon1 = data.get('weapon1', 'fists')
        player.weapon2 = data.get('weapon2', 'fists')
        player.active_buffs = data.get('active_buffs', {})
        player.status_effects = data.get('status_effects', {})
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

@app.post("/login")
async def login(credentials: dict):
    """Login with username and password"""
    try:
        username = credentials.get('username', '').strip()
        password = credentials.get('password', '').strip()
        
        if not username or not password:
            return JSONResponse({
                "success": False,
                "error": "Username and password are required"
            })
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, password_hash, player_data 
                FROM players WHERE username = ?
            ''', (username,))
            player_row = cursor.fetchone()
            
            if not player_row:
                return JSONResponse({
                    "success": False,
                    "error": "Invalid username or password"
                })
            
            # Verify password (handle empty password_hash for old accounts)
            stored_hash = player_row.get('password_hash', '')
            if not stored_hash:
                return JSONResponse({
                    "success": False,
                    "error": "This account was created before password security was added. Please create a new account."
                })
            
            if not verify_password(password, stored_hash):
                return JSONResponse({
                    "success": False,
                    "error": "Invalid username or password"
                })
            
            # Return player data (without password hash)
            player_data = json.loads(player_row['player_data'])
            return JSONResponse({
                "success": True,
                "player": player_data,
                "message": "Login successful!"
            })
            
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

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
        # Validate required fields
        username = player_data.get('username', '').strip()
        password = player_data.get('password', '').strip()
        
        if not username or not password:
            return JSONResponse({
                "success": False,
                "error": "Username and password are required"
            })
        
        if len(password) < 6:
            return JSONResponse({
                "success": False,
                "error": "Password must be at least 6 characters long"
            })
        
        # Hash the password
        password_hash = hash_password(password)
        
        player_id = f"web_{random.randint(10000, 99999)}"
        player = WebPlayer(player_id, username)
        
        # Set faction and abilities
        player.faction = player_data['faction']
        faction_data = FACTION_DATA[player.faction]
        player.abilities = faction_data['abilities'][:4]  # First 4 abilities
        
        # Set default equipment: full cloth set, sword mainhand, shield offhand
        player.armor_type = 'cloth'
        
        # Generate full cloth armor set
        armor_slots = ['helmet', 'armor', 'pants', 'boots', 'gloves']
        for slot in armor_slots:
            armor_key = f"cloth_{slot}"
            if armor_key in EQUIPMENT_DATA['armor']:
                armor_data = EQUIPMENT_DATA['armor'][armor_key].copy()
                armor_data['slot'] = slot
                armor_data['rarity'] = 'rare'  # Give good starting gear
                player.equipment[slot] = armor_data
        
        # Set default weapons: sword mainhand, shield offhand
        player.weapon1 = 'sword'
        player.weapon2 = 'shield'
        
        # Set weapon equipment
        sword_data = WEAPON_DATA['weapon_sword'].copy()
        sword_data['slot'] = 'main_hand'
        sword_data['rarity'] = 'rare'
        player.equipment['main_hand'] = sword_data
        
        shield_data = WEAPON_DATA['weapon_shield'].copy()
        shield_data['slot'] = 'off_hand'
        shield_data['rarity'] = 'rare'
        player.equipment['off_hand'] = shield_data
        
        # Save to database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Handle both old and new database schemas
            try:
                cursor.execute('''
                    INSERT INTO players (id, username, password_hash, player_data) 
                    VALUES (?, ?, ?, ?)
                ''', (player_id, player.username, password_hash, json.dumps(player.to_dict())))
            except sqlite3.OperationalError as e:
                if "no column named password_hash" in str(e):
                    # Fallback for old database schema
                    cursor.execute('''
                        INSERT INTO players (id, username, player_data) 
                        VALUES (?, ?, ?)
                    ''', (player_id, player.username, json.dumps(player.to_dict())))
                else:
                    raise
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
async def duel(request: dict):
    """Execute a duel with full game features"""
    try:
        username = request.get('username')
        if not username:
            return JSONResponse({"success": False, "error": "Username required"})
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM players WHERE username = ?', (username,))
            player_row = cursor.fetchone()
            
            if not player_row:
                return JSONResponse({"success": False, "error": "Player not found"})
            
            player_data = json.loads(player_row['player_data'])
            # Ensure id field is present for WebPlayer.from_dict()
            if 'id' not in player_data:
                player_data['id'] = player_row['id']
            player = WebPlayer.from_dict(player_data)
            
            # Select a random opponent from existing players (including AI bots)
            cursor.execute('SELECT * FROM players WHERE username != ? ORDER BY RANDOM() LIMIT 1', (username,))
            opponent_row = cursor.fetchone()
            
            if not opponent_row:
                return JSONResponse({"success": False, "error": "No opponents available"})
            
            opponent_data = json.loads(opponent_row['player_data'])
            # Ensure id field is present for WebPlayer.from_dict()
            if 'id' not in opponent_data:
                opponent_data['id'] = opponent_row['id']
            
                    # Execute duel using turn-based combat system
                    duel_result = simulateTurnBasedCombat(player_data, opponent_data)
            
            # Update player stats
            player_wins = player_data.get('wins', 0)
            player_losses = player_data.get('losses', 0)
            
            opponent_username = opponent_data['username']
            
            if duel_result['winner'] == username:
                player_wins += 1
                result_text = f"🎉 {username} WINS THE DUEL!"
            else:
                player_losses += 1
                result_text = f"💀 {opponent_username} WINS THE DUEL!"
            
            # Update player data
            player_data['wins'] = player_wins
            player_data['losses'] = player_losses
            
            # Update rating based on win/loss (simple +25/-25 system)
            current_rating = player_data.get('rating', 1200)
            if duel_result['winner'] == username:
                player_data['rating'] = current_rating + 25
            else:
                player_data['rating'] = max(1000, current_rating - 25)  # Don't go below 1000
            
            # Save updated player
            cursor.execute('''
                UPDATE players SET player_data = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE username = ?
            ''', (json.dumps(player_data), username))
            
            # Update opponent stats too (if they're a real player, not AI)
            if not opponent_username.startswith('Bot_'):
                opponent_wins = opponent_data.get('wins', 0)
                opponent_losses = opponent_data.get('losses', 0)
                opponent_rating = opponent_data.get('rating', 1200)
                
                if duel_result['winner'] == opponent_username:
                    opponent_wins += 1
                    opponent_data['rating'] = opponent_rating + 25
                else:
                    opponent_losses += 1
                    opponent_data['rating'] = max(1000, opponent_rating - 25)
                
                opponent_data['wins'] = opponent_wins
                opponent_data['losses'] = opponent_losses
                
                cursor.execute('''
                    UPDATE players SET player_data = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE username = ?
                ''', (json.dumps(opponent_data), opponent_username))
            
            conn.commit()
            
            return JSONResponse({
                "success": True,
                "combat_log": duel_result['log'],
                "player_wins": player_wins,
                "player_losses": player_losses,
                "result": result_text
            })
            
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

def executeTurnBasedAction(attacker_name, attacker_faction, attacker_armor, attacker_weapon1, attacker_weapon2,
                          attacker_hp, attacker_stats, attacker_buffs, attacker_status_effects,
                          defender_name, defender_faction, defender_armor, defender_weapon1, defender_weapon2,
                          defender_hp, defender_stats, defender_buffs, defender_status_effects,
                          log, turn_number):
    """Execute a single turn-based action with detailed logging"""
    
    # Add turn indicator
    log.append(f"Turn {turn_number}: {attacker_name}'s action")
    
    # Determine action (ability vs attack)
    action = getTurnAction(attacker_name, attacker_faction, attacker_buffs)
    
    if action == 'ability':
        # Execute ability
        ability = selectAbility(attacker_faction, attacker_buffs)
        if ability:
            # Get ability data
            ability_data = ABILITY_DATA[ability]
            
            # Add ability icon to log
            ability_icon = f"<img src='/assets/abilities/ability_{ability}.PNG' width='20' height='20'>" if ability != 'natures_wrath' else f"<img src='/assets/abilities/ability_nature's_wrath.png' width='20' height='20'>"
            
            log.append(f"{ability_icon} {attacker_name} uses {ability_data['name']}!")
            
            # Apply ability effects
            if 'damage' in ability_data['effects']:
                base_damage = ability_data['effects']['damage']
                # Apply faction and armor bonuses
                total_damage = calculateAbilityDamage(base_damage, attacker_faction, attacker_armor, defender_armor)
                defender_hp -= total_damage
                log.append(f"💥 {defender_name} takes {total_damage} damage!")
            
            if 'heal' in ability_data['effects']:
                heal_amount = ability_data['effects']['heal']
                attacker_hp = min(attacker_stats['hp'], attacker_hp + heal_amount)
                log.append(f"💚 {attacker_name} heals for {heal_amount} HP!")
            
            # Apply buffs/debuffs
            for effect, value in ability_data['effects'].items():
                if effect in ['damage_multiplier', 'speed_boost', 'defense_boost']:
                    attacker_buffs[effect] = value
                    log.append(f"✨ {attacker_name} gains {effect}!")
    else:
        # Execute attack
        base_damage = calculateAttackDamage(attacker_weapon1, attacker_weapon2, attacker_faction, attacker_armor)
        
        # Apply damage multiplier if active
        if 'damage_multiplier' in attacker_buffs:
            base_damage = int(base_damage * attacker_buffs['damage_multiplier'])
            del attacker_buffs['damage_multiplier']  # One-time use
        
        # Check for crit
        crit_chance = attacker_stats['crit_chance']
        is_crit = random.random() < crit_chance
        
        if is_crit:
            base_damage = int(base_damage * 1.5)
            log.append(f"💥 {attacker_name} attacks {defender_name} for {base_damage} CRITICAL damage!")
        else:
            log.append(f"⚔️ {attacker_name} attacks {defender_name} for {base_damage} damage!")
        
        defender_hp -= base_damage
    
    return attacker_hp, defender_hp, log

def getTurnAction(player_name, faction, active_buffs):
    """Determine if player uses ability or attack this turn"""
    # Simple logic: 30% chance for ability, 70% for attack
    # Could be made more sophisticated based on faction, health, etc.
    return 'ability' if random.random() < 0.3 else 'attack'

def selectAbility(faction, active_buffs):
    """Select an ability to use"""
    faction_abilities = FACTION_DATA[faction]['abilities']
    return random.choice(faction_abilities)

def calculateAbilityDamage(base_damage, attacker_faction, attacker_armor, defender_armor):
    """Calculate ability damage with faction and armor bonuses"""
    damage = base_damage
    
    # Apply faction damage bonus
    faction_data = FACTION_DATA[attacker_faction]
    if 'damage_bonus' in faction_data:
        damage += faction_data['damage_bonus']
    
    # Apply armor set bonuses
    armor_bonuses = ARMOR_SET_BONUSES.get(attacker_armor, {}).get('5_piece', {}).get('effects', {})
    if 'damage_bonus' in armor_bonuses:
        damage += armor_bonuses['damage_bonus']
    
    return max(1, damage)

def calculateAttackDamage(weapon1, weapon2, faction, armor):
    """Calculate attack damage from weapons"""
    weapon1_data = WEAPON_DATA.get(f'weapon_{weapon1}', {'attack': 5})
    weapon2_data = WEAPON_DATA.get(f'weapon_{weapon2}', {'attack': 5})
    
    base_damage = weapon1_data.get('attack', 5) + weapon2_data.get('attack', 5)
    
    # Apply faction bonus
    faction_data = FACTION_DATA[faction]
    if 'damage_bonus' in faction_data:
        base_damage += faction_data['damage_bonus']
    
    # Apply armor set bonuses
    armor_bonuses = ARMOR_SET_BONUSES.get(armor, {}).get('5_piece', {}).get('effects', {})
    if 'damage_bonus' in armor_bonuses:
        base_damage += armor_bonuses['damage_bonus']
    
    return max(1, base_damage)

def simulateTurnBasedCombat(player_data: dict, opponent_data: dict) -> dict:
    """Simulate turn-based combat with step-by-step execution"""
    log = []
    
    # Extract player stats
    player_name = player_data['username']
    player_faction = player_data['faction']
    player_armor = player_data['armor_type']
    player_weapon1 = player_data['weapon1']
    player_weapon2 = player_data['weapon2']
    
    opponent_name = opponent_data['username']
    opponent_faction = opponent_data['faction']
    opponent_armor = opponent_data['armor_type']
    opponent_weapon1 = opponent_data['weapon1']
    opponent_weapon2 = opponent_data['weapon2']
    
    # Calculate base stats
    player_stats = calculatePlayerStats(player_data)
    opponent_stats = calculatePlayerStats(opponent_data)
    
    # Initialize combat state
    player_hp = player_stats['hp']
    opponent_hp = opponent_stats['hp']
    
    player_active_buffs = {}
    opponent_active_buffs = {}
    player_status_effects = {}
    opponent_status_effects = {}
    
    log.append(f"⚔️ {player_name} vs {opponent_name}")
    log.append(f"🎯 {player_name}: {player_hp} HP | {opponent_name}: {opponent_hp} HP")
    
    # Combat loop - multiple rounds with turn-based execution
    max_rounds = 8
    turn_number = 0
    
    for round_num in range(1, max_rounds + 1):
        if player_hp <= 0 or opponent_hp <= 0:
            break
            
        log.append(f"\n--- Round {round_num} ---")
        
        # Determine turn order based on speed
        player_speed = player_stats['speed']
        opponent_speed = opponent_stats['speed']
        
        # Apply speed modifiers from buffs
        if 'speed_boost' in player_active_buffs:
            player_speed += player_active_buffs['speed_boost']
        if 'speed_boost' in opponent_active_buffs:
            opponent_speed += opponent_active_buffs['speed_boost']
        
        # Player goes first if speed is higher (or equal, then random)
        player_first = player_speed > opponent_speed or (player_speed == opponent_speed and random.random() < 0.5)
        
        # Execute turns with step-by-step logging
        if player_first:
            # Player turn
            turn_number += 1
            player_hp, opponent_hp, log = executeTurnBasedAction(
                player_name, player_faction, player_armor, player_weapon1, player_weapon2,
                player_hp, player_stats, player_active_buffs, player_status_effects,
                opponent_name, opponent_faction, opponent_armor, opponent_weapon1, opponent_weapon2,
                opponent_hp, opponent_stats, opponent_active_buffs, opponent_status_effects,
                log, turn_number
            )
            
            # Opponent turn (if still alive)
            if opponent_hp > 0:
                turn_number += 1
                opponent_hp, player_hp, log = executeTurnBasedAction(
                    opponent_name, opponent_faction, opponent_armor, opponent_weapon1, opponent_weapon2,
                    opponent_hp, opponent_stats, opponent_active_buffs, opponent_status_effects,
                    player_name, player_faction, player_armor, player_weapon1, player_weapon2,
                    player_hp, player_stats, player_active_buffs, player_status_effects,
                    log, turn_number
                )
        else:
            # Opponent turn
            turn_number += 1
            opponent_hp, player_hp, log = executeTurnBasedAction(
                opponent_name, opponent_faction, opponent_armor, opponent_weapon1, opponent_weapon2,
                opponent_hp, opponent_stats, opponent_active_buffs, opponent_status_effects,
                player_name, player_faction, player_armor, player_weapon1, player_weapon2,
                player_hp, player_stats, player_active_buffs, player_status_effects,
                log, turn_number
            )
            
            # Player turn (if still alive)
            if player_hp > 0:
                turn_number += 1
                player_hp, opponent_hp, log = executeTurnBasedAction(
                    player_name, player_faction, player_armor, player_weapon1, player_weapon2,
                    player_hp, player_stats, player_active_buffs, player_status_effects,
                    opponent_name, opponent_faction, opponent_armor, opponent_weapon1, opponent_weapon2,
                    opponent_hp, opponent_stats, opponent_active_buffs, opponent_status_effects,
                    log, turn_number
                )
        
        # Process status effects at end of round
        player_hp, player_active_buffs, player_status_effects = processStatusEffects(
            player_name, player_hp, player_active_buffs, player_status_effects, log
        )
        opponent_hp, opponent_active_buffs, opponent_status_effects = processStatusEffects(
            opponent_name, opponent_hp, opponent_active_buffs, opponent_status_effects, log
        )
        
        # Update HP display
        log.append(f"💚 {player_name}: {max(0, player_hp)} HP | {opponent_name}: {max(0, opponent_hp)} HP")
    
    # Determine winner
    if player_hp > opponent_hp:
        winner = player_name
        log.append(f"\n🎉 {player_name} WINS THE DUEL!")
    elif opponent_hp > player_hp:
        winner = opponent_name
        log.append(f"\n💀 {opponent_name} WINS THE DUEL!")
    else:
        winner = "draw"
        log.append(f"\n🤝 THE DUEL ENDS IN A DRAW!")
    
    return {
        'winner': winner,
        'combat_log': log,
        'player_final_hp': max(0, player_hp),
        'opponent_final_hp': max(0, opponent_hp),
        'rounds': min(max_rounds, round_num),
        'total_turns': turn_number
    }
    
    # Combat status effects
    player_buffs = {}
    opponent_buffs = {}
    
    log.append(f"⚔️ {player_name} vs {opponent_name}")
    log.append(f"🎯 {player_name}: {player_hp}/{player_max_hp} HP | {opponent_name}: {opponent_hp}/{opponent_max_hp} HP")
    log.append("--- COMBAT BEGINS ---")
    
    # Determine turn order (speed-based)
    player_speed = player_stats['speed']
    opponent_speed = opponent_stats['speed']
    
    if player_speed >= opponent_speed:
        turn_order = [(player_name, player_stats, player_buffs, opponent_name, opponent_stats, opponent_buffs)]
        turn_order.append((opponent_name, opponent_stats, opponent_buffs, player_name, player_stats, player_buffs))
    else:
        turn_order = [(opponent_name, opponent_stats, opponent_buffs, player_name, player_stats, player_buffs)]
        turn_order.append((player_name, player_stats, player_buffs, opponent_name, opponent_stats, opponent_buffs))
    
    turn_count = 0
    max_turns = 20  # Reasonable duel length
    
    # Main combat loop
    while player_hp > 0 and opponent_hp > 0 and turn_count < max_turns:
        turn_count += 1
        log.append(f"\n--- ROUND {turn_count} ---")
        
        # Process each turn
        for attacker_name, attacker_stats, attacker_buffs, defender_name, defender_stats, defender_buffs in turn_order:
            if (attacker_name == player_name and player_hp <= 0) or (attacker_name == opponent_name and opponent_hp <= 0):
                continue
                
            # Determine action (70% ability, 30% attack)
            action_type = "ability" if random.random() < 0.7 else "attack"
            
            if action_type == "ability":
                # Use faction ability
                faction_data = FACTION_DATA[attacker_stats['faction']]
                abilities = faction_data['abilities']
                ability = random.choice(abilities)
                
                log.append(f"⚡ {attacker_name} uses {ability.replace('_', ' ').title()}!")
                
                # Apply ability effects
                ability_result = applyAbilityEffect(ability, attacker_name, defender_name, attacker_stats, defender_stats, attacker_buffs, defender_buffs)
                log.extend(ability_result['log'])
                
                # Update HP
                if attacker_name == player_name:
                    player_hp = ability_result['attacker_hp']
                    opponent_hp = ability_result['defender_hp']
                else:
                    opponent_hp = ability_result['attacker_hp']
                    player_hp = ability_result['defender_hp']
                    
            else:
                # Regular attack
                attack_result = performAttack(attacker_name, defender_name, attacker_stats, defender_stats, attacker_buffs, defender_buffs)
                log.extend(attack_result['log'])
                
                # Update HP
                if attacker_name == player_name:
                    player_hp = attack_result['attacker_hp']
                    opponent_hp = attack_result['defender_hp']
                else:
                    opponent_hp = attack_result['attacker_hp']
                    player_hp = attack_result['defender_hp']
            
            # Check for combat end
            if player_hp <= 0 or opponent_hp <= 0:
                break
        
        # Apply faction passives at end of round
        player_hp = applyFactionPassives(player_name, player_stats, player_hp, player_max_hp, player_buffs)
        opponent_hp = applyFactionPassives(opponent_name, opponent_stats, opponent_hp, opponent_max_hp, opponent_buffs)
        
        # Status effect cleanup
        player_buffs = cleanupStatusEffects(player_buffs)
        opponent_buffs = cleanupStatusEffects(opponent_buffs)
    
    # Determine winner
    if player_hp > 0:
        winner = player_name
        log.append(f"\n🎉 {player_name} WINS THE DUEL!")
        log.append(f"🏆 Final HP: {player_name} ({player_hp}/{player_max_hp}) | {opponent_name} (0/{opponent_max_hp})")
    else:
        winner = opponent_name
        log.append(f"\n💀 {opponent_name} WINS THE DUEL!")
        log.append(f"💀 Final HP: {player_name} (0/{player_max_hp}) | {opponent_name} ({opponent_hp}/{opponent_max_hp})")
    
    log.append(f"⚔️ Combat lasted {turn_count} rounds")
    
    return {
        'winner': winner,
        'log': log,
        'turns': turn_count,
        'player_final_hp': max(0, player_hp),
        'opponent_final_hp': max(0, opponent_hp)
    }

def calculatePlayerStats(player_data: dict) -> dict:
    """Calculate comprehensive player stats including all bonuses"""
    faction = player_data['faction']
    armor_type = player_data['armor_type']
    weapon1 = player_data['weapon1']
    weapon2 = player_data['weapon2']
    
    # Base stats
    hp = 100
    attack = 20
    defense = 10
    speed = 10
    crit_chance = 0.05
    dodge_chance = 0.05
    
    # Weapon bonuses
    weapon1_data = WEAPON_DATA.get(weapon1, {})
    weapon2_data = WEAPON_DATA.get(weapon2, {})
    
    attack += weapon1_data.get('attack', 0) + weapon2_data.get('attack', 0)
    speed += int((weapon1_data.get('speed', 0) + weapon2_data.get('speed', 0)) / 2)
    crit_chance += (weapon1_data.get('crit_chance', 0) + weapon2_data.get('crit_chance', 0)) / 2
    
    # Armor set bonuses (assuming 5-piece for full effect)
    armor_bonuses = ARMOR_SET_BONUSES.get(armor_type, {}).get('5_piece', {}).get('effects', {})
    
    if 'defense_bonus' in armor_bonuses:
        defense += armor_bonuses['defense_bonus']
    if 'speed_bonus' in armor_bonuses:
        speed += armor_bonuses['speed_bonus']
    if 'dodge_bonus' in armor_bonuses:
        dodge_chance += armor_bonuses['dodge_bonus']
    if 'crit_chance' in armor_bonuses:
        crit_chance += armor_bonuses['crit_chance']
    
    # Faction passives
    faction_data = FACTION_DATA.get(faction, {})
    
    if faction_data.get('passive') == 'divine_protection':
        # 10% damage reduction (applied during damage calculation)
        pass
    elif faction_data.get('passive') == 'shadow_mastery':
        crit_chance += faction_data.get('passive_value', 0.15)
    elif faction_data.get('passive') == 'natures_blessing':
        # 5% HP regen per turn (applied during combat)
        pass
    
    return {
        'hp': hp,
        'attack': attack,
        'defense': defense,
        'speed': speed,
        'crit_chance': min(0.95, crit_chance),
        'dodge_chance': min(0.95, dodge_chance),
        'faction': faction,
        'armor_type': armor_type
    }

def applyAbilityEffect(ability_name: str, attacker_name: str, defender_name: str, 
                      attacker_stats: dict, defender_stats: dict, 
                      attacker_buffs: dict, defender_buffs: dict) -> dict:
    """Apply ability effects and return updated HP values"""
    log = []
    attacker_hp = attacker_stats['hp']
    defender_hp = defender_stats['hp']
    
    # Get ability data
    ability = ABILITY_DATA.get(ability_name, {})
    
    # Apply damage abilities
    if 'damage_multiplier' in ability:
        base_damage = attacker_stats['attack']
        damage = int(base_damage * ability['damage_multiplier'])
        
        # Check for crit
        if random.random() < attacker_stats['crit_chance']:
            damage = int(damage * 1.5)
            log.append(f"💥 {attacker_name} scores a CRITICAL HIT!")
        
        # Apply defense
        defense_reduction = defender_stats['defense']
        damage = max(1, damage - defense_reduction)
        
        # Check for dodge
        if random.random() < defender_stats['dodge_chance']:
            log.append(f"💨 {defender_name} DODGES the attack!")
            damage = 0
        
        if damage > 0:
            defender_hp = max(0, defender_hp - damage)
            log.append(f"⚔️ {defender_name} takes {damage} damage!")
    
    # Apply healing abilities
    if 'healing' in ability:
        healing_data = ability['healing']
        if isinstance(healing_data, dict) and 'amount' in healing_data:
            heal_amount = healing_data['amount']
            max_hp = attacker_stats['hp']
            attacker_hp = min(max_hp, attacker_hp + heal_amount)
            log.append(f"💚 {attacker_name} heals for {heal_amount} HP!")
    
    # Apply status effects
    if 'effects' in ability:
        for effect, value in ability['effects'].items():
            defender_buffs[effect] = value
            log.append(f"✨ {defender_name} is affected by {effect.replace('_', ' ')}!")
    
    return {
        'log': log,
        'attacker_hp': attacker_hp,
        'defender_hp': defender_hp
    }

def performAttack(attacker_name: str, defender_name: str, attacker_stats: dict, 
                 defender_stats: dict, attacker_buffs: dict, defender_buffs: dict) -> dict:
    """Perform a regular attack"""
    log = []
    attacker_hp = attacker_stats['hp']
    defender_hp = defender_stats['hp']
    
    base_damage = attacker_stats['attack']
    damage = base_damage
    
    # Check for crit
    if random.random() < attacker_stats['crit_chance']:
        damage = int(damage * 1.5)
        log.append(f"💥 {attacker_name} scores a CRITICAL HIT!")
    
    # Apply defense
    defense_reduction = defender_stats['defense']
    damage = max(1, damage - defense_reduction)
    
    # Check for dodge
    if random.random() < defender_stats['dodge_chance']:
        log.append(f"💨 {defender_name} DODGES the attack!")
        damage = 0
    
    if damage > 0:
        defender_hp = max(0, defender_hp - damage)
        log.append(f"⚔️ {attacker_name} attacks {defender_name} for {damage} damage!")
    
    return {
        'log': log,
        'attacker_hp': attacker_hp,
        'defender_hp': defender_hp
    }

def applyFactionPassives(player_name: str, stats: dict, current_hp: int, max_hp: int, buffs: dict) -> int:
    """Apply faction passives at end of turn"""
    faction_data = FACTION_DATA.get(stats['faction'], {})
    
    # Nature's Blessing - HP regeneration
    if faction_data.get('passive') == 'natures_blessing':
        regen_amount = int(max_hp * faction_data.get('passive_value', 0.05))
        current_hp = min(max_hp, current_hp + regen_amount)
        if regen_amount > 0:
            print(f"💚 {player_name} regenerates {regen_amount} HP from Nature's Blessing")
    
    return current_hp

def cleanupStatusEffects(buffs: dict) -> dict:
    """Clean up expired status effects"""
    # Simple cleanup - remove effects after 1 turn for now
    return {}

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

@app.post("/update-loadout")
async def update_loadout(request: dict):
    """Update player loadout (faction, armor, weapons)"""
    try:
        username = request.get('username')
        new_faction = request.get('faction')
        new_armor = request.get('armor_type')
        new_weapon1 = request.get('weapon1')
        new_weapon2 = request.get('weapon2')
        
        if not username:
            return JSONResponse({"success": False, "error": "Username required"})
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM players WHERE username = ?', (username,))
            player_row = cursor.fetchone()
            
            if not player_row:
                return JSONResponse({"success": False, "error": "Player not found"})
            
            player_data = json.loads(player_row['player_data'])
            
            # Update loadout
            if new_faction:
                player_data['faction'] = new_faction
            if new_armor:
                player_data['armor_type'] = new_armor
            if new_weapon1:
                player_data['weapon1'] = new_weapon1
            if new_weapon2:
                player_data['weapon2'] = new_weapon2
            
            # Save updated player
            cursor.execute('''
                UPDATE players SET player_data = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE username = ?
            ''', (json.dumps(player_data), username))
            
            conn.commit()
            
            return JSONResponse({
                "success": True,
                "player": player_data,
                "message": "Loadout updated successfully!"
            })
            
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

@app.get("/leaderboard")
async def get_leaderboard():
    """Get the leaderboard"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM players 
                ORDER BY json_extract(player_data, '$.rating') DESC 
                LIMIT 20
            ''')
            players = cursor.fetchall()
            
            leaderboard = []
            for i, player_row in enumerate(players):
                player_data = json.loads(player_row['player_data'])
                wins = player_data.get('wins', 0)
                losses = player_data.get('losses', 0)
                total_games = wins + losses
                win_rate = (wins / total_games * 100) if total_games > 0 else 0
                
                leaderboard.append({
                    'rank': i + 1,
                    'username': player_data['username'],
                    'rating': player_data.get('rating', 1200),
                    'wins': wins,
                    'losses': losses,
                    'win_rate': round(win_rate, 1),
                    'faction': FACTION_DATA[player_data['faction']]['name'],
                    'armor_type': player_data['armor_type'].title(),
                    'is_bot': player_data['username'].startswith('Bot_')
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
    return JSONResponse({"status": "healthy", "full_game": True, "version": "2.0"})

if __name__ == "__main__":
    init_database()
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
