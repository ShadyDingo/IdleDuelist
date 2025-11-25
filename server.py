#!/usr/bin/env python3
"""
IdleDuelist Server
Main backend server with API endpoints
"""

import os
import json
import sqlite3
import random
import bcrypt
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Depends, Body, Header
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import JWTError, jwt

# Import game logic
from game_logic import (
    calculate_combat_stats, generate_equipment, roll_equipment_rarity,
    calculate_damage, check_hit, calculate_exp_gain, process_level_up,
    get_equipment_stats, get_weapon_type, get_weapon_attack_speed,
    get_weapon_damage_type, get_abilities_for_weapon, get_ability_by_id,
    PRIMARY_STATS, EQUIPMENT_SLOTS, WEAPON_TYPES, RARITIES
)

app = FastAPI(title="IdleDuelist", version="2.0.0")

# CORS middleware - restrict to specific domains in production
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Database connection - supports both SQLite (dev) and PostgreSQL (prod)
DATABASE = "idleduelist.db"
DATABASE_URL = os.getenv("DATABASE_URL", None)  # Railway provides this for PostgreSQL
USE_POSTGRES = DATABASE_URL is not None and DATABASE_URL.startswith("postgres")

# Redis connection for caching and state management
REDIS_URL = os.getenv("REDIS_URL", None)
redis_client = None

# Combat state management - will use Redis in production
combat_states = {}
pvp_queue = {}  # character_id -> joined_at timestamp
auto_fight_sessions = {}  # session_id -> session_data

def get_db_connection():
    """Get database connection - SQLite for dev, PostgreSQL for prod"""
    if USE_POSTGRES:
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            # Parse DATABASE_URL (format: postgresql://user:password@host:port/dbname)
            conn = psycopg2.connect(DATABASE_URL)
            conn.cursor_factory = RealDictCursor
            return conn
        except ImportError:
            print("Warning: psycopg2 not installed, falling back to SQLite")
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            return conn
    else:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn

def get_redis_client():
    """Get Redis client or return None if not available"""
    global redis_client
    if redis_client is not None:
        return redis_client
    
    if REDIS_URL:
        try:
            import redis
            redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            # Test connection
            redis_client.ping()
            return redis_client
        except (ImportError, Exception) as e:
            print(f"Warning: Redis not available: {e}, using in-memory storage")
            return None
    return None

def init_database():
    """Initialize database with all tables - compatible with both SQLite and PostgreSQL"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table - PostgreSQL uses VARCHAR, SQLite uses TEXT
    if USE_POSTGRES:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(255) PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    # Characters table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS characters (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT UNIQUE NOT NULL,
            level INTEGER DEFAULT 1,
            exp INTEGER DEFAULT 0,
            skill_points INTEGER DEFAULT 3,
            stats_json TEXT NOT NULL,
            equipment_json TEXT NOT NULL,
            inventory_json TEXT NOT NULL,
            auto_combat BOOLEAN DEFAULT 0,
            gold INTEGER DEFAULT 0,
            pvp_enabled BOOLEAN DEFAULT 0,
            combat_stance TEXT DEFAULT 'balanced',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Add gold and pvp_enabled columns if they don't exist (for existing databases)
    try:
        cursor.execute('ALTER TABLE characters ADD COLUMN gold INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('ALTER TABLE characters ADD COLUMN pvp_enabled BOOLEAN DEFAULT 0')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE characters ADD COLUMN combat_stance TEXT DEFAULT "balanced"')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Combat logs table
    if USE_POSTGRES:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS combat_logs (
                id SERIAL PRIMARY KEY,
                character1_id VARCHAR(255) NOT NULL,
                character2_id VARCHAR(255) NOT NULL,
                winner_id VARCHAR(255),
                log_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character1_id) REFERENCES characters (id),
                FOREIGN KEY (character2_id) REFERENCES characters (id)
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS combat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character1_id TEXT NOT NULL,
                character2_id TEXT NOT NULL,
                winner_id TEXT,
                log_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character1_id) REFERENCES characters (id),
                FOREIGN KEY (character2_id) REFERENCES characters (id)
            )
        ''')
    
    # Chat messages table
    if USE_POSTGRES:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                character_id VARCHAR(255) NOT NULL,
                character_name VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters (id)
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id TEXT NOT NULL,
                character_name TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters (id)
            )
        ''')
    
    # Abilities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS abilities (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            cooldown_seconds INTEGER NOT NULL,
            damage_multiplier REAL NOT NULL,
            damage_type TEXT NOT NULL,
            mana_cost INTEGER NOT NULL,
            weapon_type TEXT NOT NULL,
            is_ultimate BOOLEAN DEFAULT 0
        )
    ''')
    
    # Character abilities (loadout/hotkey assignments)
    if USE_POSTGRES:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS character_abilities (
                id SERIAL PRIMARY KEY,
                character_id VARCHAR(255) NOT NULL,
                ability_id VARCHAR(255) NOT NULL,
                slot_position INTEGER NOT NULL,
                FOREIGN KEY (character_id) REFERENCES characters (id),
                FOREIGN KEY (ability_id) REFERENCES abilities (id),
                UNIQUE(character_id, slot_position)
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS character_abilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id TEXT NOT NULL,
                ability_id TEXT NOT NULL,
                slot_position INTEGER NOT NULL,
                FOREIGN KEY (character_id) REFERENCES characters (id),
                FOREIGN KEY (ability_id) REFERENCES abilities (id),
                UNIQUE(character_id, slot_position)
            )
        ''')
    
    # PvE enemies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pve_enemies (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            level INTEGER NOT NULL,
            stats_json TEXT NOT NULL,
            description TEXT,
            story_order INTEGER NOT NULL,
            unlocked_at_level INTEGER DEFAULT 1,
            gold_min INTEGER DEFAULT 1,
            gold_max INTEGER DEFAULT 1,
            drop_chance REAL DEFAULT 0.0
        )
    ''')
    
    # Add new columns if they don't exist (for existing databases)
    try:
        cursor.execute('ALTER TABLE pve_enemies ADD COLUMN description TEXT')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE pve_enemies ADD COLUMN gold_min INTEGER DEFAULT 1')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE pve_enemies ADD COLUMN gold_max INTEGER DEFAULT 1')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE pve_enemies ADD COLUMN drop_chance REAL DEFAULT 0.0')
    except sqlite3.OperationalError:
        pass
    
    # Character PvE progress
    if USE_POSTGRES:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS character_pve_progress (
                id SERIAL PRIMARY KEY,
                character_id VARCHAR(255) NOT NULL,
                highest_enemy_defeated VARCHAR(255),
                enemies_unlocked_json TEXT NOT NULL,
                FOREIGN KEY (character_id) REFERENCES characters (id),
                UNIQUE(character_id)
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS character_pve_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id TEXT NOT NULL,
                highest_enemy_defeated TEXT,
                enemies_unlocked_json TEXT NOT NULL,
                FOREIGN KEY (character_id) REFERENCES characters (id),
                UNIQUE(character_id)
            )
        ''')
    
    # Store items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS store_items (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            slot TEXT NOT NULL,
            weapon_type TEXT,
            base_price INTEGER NOT NULL,
            level_requirement INTEGER DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")
    
    # Initialize default data
    initialize_default_data()


def initialize_default_data():
    """Initialize default abilities, PvE enemies, and store items"""
    from game_logic import ABILITIES
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Initialize abilities
    for weapon_type, abilities in ABILITIES.items():
        for ability in abilities:
            cursor.execute('''
                INSERT OR IGNORE INTO abilities 
                (id, name, description, cooldown_seconds, damage_multiplier, damage_type, mana_cost, weapon_type, is_ultimate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ability['id'], ability['name'], ability['description'],
                ability['cooldown_seconds'], ability['damage_multiplier'],
                ability['damage_type'], ability['mana_cost'], weapon_type,
                1 if ability['is_ultimate'] else 0
            ))
    
    # Initialize PvE enemies (30 specific enemies with exact stats and rewards)
    # Clear existing enemies before inserting updated list
    cursor.execute("DELETE FROM pve_enemies")
    
    # Balanced PvE enemies - roughly 2.5-3x level in total stats for appropriate challenge
    # Enemies should be beatable by similarly-leveled players with decent equipment
    pve_enemies_data = [
        {'id': 'chicken', 'name': 'Chicken', 'level': 1, 'stats': {'might': 1, 'agility': 2, 'vitality': 1, 'intellect': 0, 'wisdom': 0, 'charisma': 0}, 'description': 'Harmless barn birds that peck at ankles. More annoying than dangerous.', 'gold_min': 1, 'gold_max': 1, 'drop_chance': 0.0},
        {'id': 'forest_rat', 'name': 'Forest Rat', 'level': 3, 'stats': {'might': 2, 'agility': 6, 'vitality': 3, 'intellect': 1, 'wisdom': 0, 'charisma': 0}, 'description': 'Oversized rodents twisted by wild magic. Quick and skittish.', 'gold_min': 1, 'gold_max': 2, 'drop_chance': 0.0},
        {'id': 'goblin_scout', 'name': 'Goblin Scout', 'level': 5, 'stats': {'might': 4, 'agility': 9, 'vitality': 4, 'intellect': 1, 'wisdom': 1, 'charisma': 0}, 'description': 'Sneaky ambushers who dart from shadow to shadow.', 'gold_min': 1, 'gold_max': 3, 'drop_chance': 0.1},
        {'id': 'cave_slime', 'name': 'Cave Slime', 'level': 8, 'stats': {'might': 3, 'agility': 2, 'vitality': 16, 'intellect': 2, 'wisdom': 3, 'charisma': 0}, 'description': 'Gelatinous blobs that digest anything organic.', 'gold_min': 2, 'gold_max': 4, 'drop_chance': 0.2},
        {'id': 'ork_grunt', 'name': 'Ork Grunt', 'level': 10, 'stats': {'might': 18, 'agility': 4, 'vitality': 12, 'intellect': 1, 'wisdom': 0, 'charisma': 0}, 'description': 'Brutish frontline fighters serving stronger warlords.', 'gold_min': 2, 'gold_max': 5, 'drop_chance': 0.5},
        {'id': 'bandit_cutpurse', 'name': 'Bandit Cutpurse', 'level': 12, 'stats': {'might': 8, 'agility': 22, 'vitality': 6, 'intellect': 2, 'wisdom': 2, 'charisma': 0}, 'description': 'High-speed thieves who rely on mobility to survive.', 'gold_min': 4, 'gold_max': 7, 'drop_chance': 0.5},
        {'id': 'skeleton_warrior', 'name': 'Skeleton Warrior', 'level': 15, 'stats': {'might': 18, 'agility': 3, 'vitality': 25, 'intellect': 0, 'wisdom': 4, 'charisma': 0}, 'description': 'Reanimated bones that act on forgotten commands.', 'gold_min': 6, 'gold_max': 10, 'drop_chance': 0.7},
        {'id': 'gnoll_raider', 'name': 'Gnoll Raider', 'level': 18, 'stats': {'might': 26, 'agility': 16, 'vitality': 16, 'intellect': 0, 'wisdom': 2, 'charisma': 0}, 'description': 'Savage hyena-folk who overwhelm caravans in packs.', 'gold_min': 8, 'gold_max': 12, 'drop_chance': 0.8},
        {'id': 'cave_spider', 'name': 'Cave Spider', 'level': 20, 'stats': {'might': 7, 'agility': 30, 'vitality': 14, 'intellect': 13, 'wisdom': 4, 'charisma': 0}, 'description': 'Venomous hunters whose webs block entire tunnels.', 'gold_min': 10, 'gold_max': 15, 'drop_chance': 1.0},
        {'id': 'bog_zombie', 'name': 'Bog Zombie', 'level': 23, 'stats': {'might': 16, 'agility': 1, 'vitality': 50, 'intellect': 4, 'wisdom': 5, 'charisma': 0}, 'description': 'Rotting corpses preserved by swamp sorcery.', 'gold_min': 12, 'gold_max': 18, 'drop_chance': 1.0},
        {'id': 'lizardfolk_scout', 'name': 'Lizardfolk Scout', 'level': 26, 'stats': {'might': 22, 'agility': 33, 'vitality': 22, 'intellect': 5, 'wisdom': 4, 'charisma': 0}, 'description': 'Cold-blooded hunters defending marsh territory.', 'gold_min': 14, 'gold_max': 22, 'drop_chance': 1.2},
        {'id': 'dire_wolf', 'name': 'Dire Wolf', 'level': 30, 'stats': {'might': 33, 'agility': 43, 'vitality': 20, 'intellect': 0, 'wisdom': 0, 'charisma': 0}, 'description': 'Moon-touched predators leading lesser wolf packs.', 'gold_min': 18, 'gold_max': 28, 'drop_chance': 1.5},
        {'id': 'ogre_brute', 'name': 'Ogre Brute', 'level': 33, 'stats': {'might': 62, 'agility': 6, 'vitality': 37, 'intellect': 0, 'wisdom': 0, 'charisma': 0}, 'description': 'Massive simple monsters who smash everything.', 'gold_min': 22, 'gold_max': 32, 'drop_chance': 1.7},
        {'id': 'wraithling', 'name': 'Wraithling', 'level': 36, 'stats': {'might': 6, 'agility': 24, 'vitality': 6, 'intellect': 35, 'wisdom': 46, 'charisma': 0}, 'description': 'Flickering spirits wandering ruins in search of warmth.', 'gold_min': 24, 'gold_max': 35, 'drop_chance': 1.8},
        {'id': 'lizardfolk_shaman', 'name': 'Lizardfolk Shaman', 'level': 40, 'stats': {'might': 7, 'agility': 7, 'vitality': 20, 'intellect': 39, 'wisdom': 56, 'charisma': 0}, 'description': 'Mystics who summon storms and serpents.', 'gold_min': 28, 'gold_max': 40, 'drop_chance': 2.0},
        {'id': 'stone_golem', 'name': 'Stone Golem', 'level': 44, 'stats': {'might': 28, 'agility': 1, 'vitality': 95, 'intellect': 0, 'wisdom': 16, 'charisma': 0}, 'description': 'Ancient guardians carved from enchanted rock.', 'gold_min': 40, 'gold_max': 60, 'drop_chance': 2.5},
        {'id': 'frost_troll', 'name': 'Frost Troll', 'level': 48, 'stats': {'might': 45, 'agility': 8, 'vitality': 82, 'intellect': 0, 'wisdom': 15, 'charisma': 0}, 'description': 'Regenerating monsters of the frozen wastes.', 'gold_min': 45, 'gold_max': 70, 'drop_chance': 2.7},
        {'id': 'vampire_thrall', 'name': 'Vampire Thrall', 'level': 52, 'stats': {'might': 33, 'agility': 65, 'vitality': 18, 'intellect': 41, 'wisdom': 0, 'charisma': 9}, 'description': 'Graceful undead servants with life-draining strikes.', 'gold_min': 50, 'gold_max': 80, 'drop_chance': 3.0},
        {'id': 'flame_elemental', 'name': 'Flame Elemental', 'level': 56, 'stats': {'might': 1, 'agility': 27, 'vitality': 19, 'intellect': 79, 'wisdom': 52, 'charisma': 0}, 'description': 'Living firestorms born from volcanic vents.', 'gold_min': 55, 'gold_max': 90, 'drop_chance': 3.2},
        {'id': 'arcane_sentinel', 'name': 'Arcane Sentinel', 'level': 60, 'stats': {'might': 10, 'agility': 1, 'vitality': 20, 'intellect': 93, 'wisdom': 65, 'charisma': 0}, 'description': 'Hovering constructs guarding forgotten libraries.', 'gold_min': 60, 'gold_max': 100, 'drop_chance': 3.5},
        {'id': 'corrupted_druid', 'name': 'Corrupted Druid', 'level': 65, 'stats': {'might': 11, 'agility': 11, 'vitality': 31, 'intellect': 51, 'wisdom': 100, 'charisma': 0}, 'description': 'Once-kind wardens now twisted by blight magic.', 'gold_min': 70, 'gold_max': 120, 'drop_chance': 4.0},
        {'id': 'blighted_treant', 'name': 'Blighted Treant', 'level': 70, 'stats': {'might': 23, 'agility': 1, 'vitality': 162, 'intellect': 1, 'wisdom': 33, 'charisma': 0}, 'description': 'Infected forest guardians dripping toxic sap.', 'gold_min': 80, 'gold_max': 130, 'drop_chance': 4.5},
        {'id': 'aether_warden', 'name': 'Aether Warden', 'level': 74, 'stats': {'might': 1, 'agility': 24, 'vitality': 24, 'intellect': 81, 'wisdom': 103, 'charisma': 0}, 'description': 'Riftwalkers who bend space around them.', 'gold_min': 90, 'gold_max': 150, 'drop_chance': 5.0},
        {'id': 'lich_adept', 'name': 'Lich Adept', 'level': 78, 'stats': {'might': 1, 'agility': 1, 'vitality': 25, 'intellect': 132, 'wisdom': 85, 'charisma': 0}, 'description': 'Apprentice necromancers wielding soul-draining magic.', 'gold_min': 100, 'gold_max': 160, 'drop_chance': 5.5},
        {'id': 'wyvern_stalker', 'name': 'Wyvern Stalker', 'level': 82, 'stats': {'might': 77, 'agility': 114, 'vitality': 51, 'intellect': 13, 'wisdom': 1, 'charisma': 0}, 'description': 'Silent aerial hunters with venomous tails.', 'gold_min': 120, 'gold_max': 180, 'drop_chance': 6.0},
        {'id': 'void_wraith', 'name': 'Void Wraith', 'level': 86, 'stats': {'might': 1, 'agility': 41, 'vitality': 15, 'intellect': 80, 'wisdom': 132, 'charisma': 0}, 'description': 'Entities from a lightless dimension whispering madness.', 'gold_min': 130, 'gold_max': 200, 'drop_chance': 7.0},
        {'id': 'titan_construct', 'name': 'Titan Construct', 'level': 90, 'stats': {'might': 84, 'agility': 1, 'vitality': 167, 'intellect': 28, 'wisdom': 1, 'charisma': 0}, 'description': 'Colossal machines built by civilizations long gone.', 'gold_min': 150, 'gold_max': 230, 'drop_chance': 8.0},
        {'id': 'demon_knight', 'name': 'Demon Knight', 'level': 94, 'stats': {'might': 145, 'agility': 30, 'vitality': 88, 'intellect': 1, 'wisdom': 30, 'charisma': 0}, 'description': 'Elite hellwarriors clad in cursed armor.', 'gold_min': 170, 'gold_max': 260, 'drop_chance': 9.0},
        {'id': 'ancient_dragon', 'name': 'Ancient Dragon', 'level': 98, 'stats': {'might': 91, 'agility': 46, 'vitality': 91, 'intellect': 46, 'wisdom': 32, 'charisma': 0}, 'description': 'World-shaping titans whose breath shifts landscapes.', 'gold_min': 200, 'gold_max': 300, 'drop_chance': 10.0},
        {'id': 'demon_lord_regent', 'name': 'Demon Lord Regent', 'level': 100, 'stats': {'might': 63, 'agility': 32, 'vitality': 47, 'intellect': 93, 'wisdom': 78, 'charisma': 0}, 'description': 'Infernal rulers capable of warping reality itself.', 'gold_min': 250, 'gold_max': 350, 'drop_chance': 12.0}
    ]
    
    for i, enemy in enumerate(pve_enemies_data):
        cursor.execute('''
            INSERT OR REPLACE INTO pve_enemies 
            (id, name, level, stats_json, description, story_order, unlocked_at_level, gold_min, gold_max, drop_chance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            enemy['id'], enemy['name'], enemy['level'],
            json.dumps(enemy['stats']), enemy['description'],
            i + 1, enemy['level'],  # story_order and unlocked_at_level
            enemy['gold_min'], enemy['gold_max'], enemy['drop_chance']
        ))
    
    # Initialize store items (Common rarity only, all weapon types)
    store_items = []
    for weapon_type in WEAPON_TYPES:
        weapon_names = {
            'sword': 'Sword', 'staff': 'Staff', 'bow': 'Bow',
            'dagger': 'Dagger', 'mace': 'Mace'
        }
        store_items.append({
            'id': f"store_{weapon_type}",
            'name': f"Common {weapon_names[weapon_type]}",
            'slot': 'main_hand',
            'weapon_type': weapon_type,
            'base_price': 100,
            'level_requirement': 1
        })
    
    # Add armor pieces
    armor_slots = ['helmet', 'chest', 'legs', 'boots', 'gloves']
    for slot in armor_slots:
        slot_names = {
            'helmet': 'Helmet', 'chest': 'Chestplate', 'legs': 'Leggings',
            'boots': 'Boots', 'gloves': 'Gloves'
        }
        store_items.append({
            'id': f"store_{slot}",
            'name': f"Common {slot_names[slot]}",
            'slot': slot,
            'weapon_type': None,
            'base_price': 75,
            'level_requirement': 1
        })
    
    for item in store_items:
        cursor.execute('''
            INSERT OR IGNORE INTO store_items 
            (id, name, slot, weapon_type, base_price, level_requirement)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            item['id'], item['name'], item['slot'],
            item['weapon_type'], item['base_price'], item['level_requirement']
        ))
    
    conn.commit()
    conn.close()
    print("Default data initialized")

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-min-32-chars")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = 24
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Security scheme for FastAPI
security = HTTPBearer()

# Password hashing
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# JWT Token functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency to get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = verify_token(token, "access")
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # Verify user still exists
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return {"user_id": user['id'], "username": user['username']}

# Pydantic models
class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class CreateCharacterRequest(BaseModel):
    name: str
    user_id: Optional[str] = None

class AllocateSkillsRequest(BaseModel):
    stats: Dict[str, int]

class EquipItemRequest(BaseModel):
    character_id: Optional[str] = None
    item_id: str
    slot: str

class CombatRequest(BaseModel):
    character_id: Optional[str] = None
    opponent_id: Optional[str] = None
    is_pve: bool = False

class ChatMessageRequest(BaseModel):
    message: str

# Helper functions
def generate_id() -> str:
    """Generate a unique ID"""
    return f"{random.randint(100000, 999999)}{int(datetime.now().timestamp())}"

def get_default_stats() -> Dict[str, int]:
    """Get default starting stats (10 in each)"""
    return {stat: 10 for stat in PRIMARY_STATS}

# Routes
@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the landing page"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Landing page not found</h1>")

@app.get("/game", response_class=HTMLResponse)
async def game():
    """Serve the main game page"""
    try:
        with open("static/game.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Game page not found</h1>")

# Authentication endpoints
@app.post("/api/register")
async def register(request: RegisterRequest):
    """Register a new user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if username exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (request.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create user
    user_id = generate_id()
    password_hash = hash_password(request.password)
    
    cursor.execute(
        "INSERT INTO users (id, username, password_hash, email) VALUES (?, ?, ?, ?)",
        (user_id, request.username, password_hash, request.email)
    )
    
    conn.commit()
    conn.close()
    
    return {"success": True, "user_id": user_id, "message": "Account created successfully"}

@app.post("/api/login")
async def login(request: LoginRequest):
    """Login and return JWT tokens and user data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (request.username,)
    )
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not verify_password(request.password, user['password_hash']):
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Get user's character
    cursor.execute(
        "SELECT * FROM characters WHERE user_id = ? LIMIT 1",
        (user['id'],)
    )
    character = cursor.fetchone()
    
    conn.close()
    
    # Create JWT tokens
    access_token = create_access_token(data={"sub": user['id'], "username": user['username']})
    refresh_token = create_refresh_token(data={"sub": user['id']})
    
    result = {
        "success": True,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user['id'],
        "username": user['username'],
        "has_character": character is not None
    }
    
    if character:
        result["character_id"] = character['id']
        result["character_name"] = character['name']
    
    return result

@app.post("/api/auth/refresh")
async def refresh_token(refresh_token: str = Body(..., embed=True)):
    """Refresh access token using refresh token"""
    payload = verify_token(refresh_token, "refresh")
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # Verify user still exists
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Create new access token
    new_access_token = create_access_token(data={"sub": user['id'], "username": user['username']})
    
    return {
        "success": True,
        "access_token": new_access_token,
        "token_type": "bearer"
    }

# Character endpoints
@app.post("/api/character/create")
async def create_character(request: CreateCharacterRequest, current_user: dict = Depends(get_current_user)):
    """Create a new character"""
    user_id = current_user["user_id"]
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if character name exists
    cursor.execute("SELECT id FROM characters WHERE name = ?", (request.name,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Character name already exists")
    
    # Check if user already has a character
    cursor.execute("SELECT id FROM characters WHERE user_id = ?", (user_id,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="User already has a character")
    
    # Create character
    character_id = generate_id()
    default_stats = get_default_stats()
    default_equipment = {slot: None for slot in EQUIPMENT_SLOTS}
    default_inventory = []
    
    cursor.execute(
        """INSERT INTO characters 
           (id, user_id, name, level, exp, skill_points, stats_json, equipment_json, inventory_json)
           VALUES (?, ?, ?, 1, 0, 3, ?, ?, ?)""",
        (
            character_id, user_id, request.name,
            json.dumps(default_stats),
            json.dumps(default_equipment),
            json.dumps(default_inventory)
        )
    )
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "character_id": character_id,
        "message": "Character created successfully"
    }

@app.get("/api/character/list")
async def list_characters(current_user: dict = Depends(get_current_user)):
    """List characters for the authenticated user"""
    user_id = current_user["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, level FROM characters WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    characters = [{
        "id": row['id'],
        "name": row['name'],
        "level": row['level']
    } for row in rows]
    
    return {"success": True, "characters": characters}

@app.get("/api/character/{character_id}")
async def get_character(character_id: str, current_user: dict = Depends(get_current_user)):
    """Get character data"""
    user_id = current_user["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM characters WHERE id = ? AND user_id = ?", (character_id, user_id))
    character = cursor.fetchone()
    
    if not character:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Parse JSON fields
    stats = json.loads(character['stats_json'])
    equipment = json.loads(character['equipment_json'])
    inventory = json.loads(character['inventory_json'])
    
    # Calculate combat stats
    equipment_stats = get_equipment_stats(equipment)
    combat_stats = calculate_combat_stats(stats, equipment_stats, equipment)
    
    conn.close()
    
    # Get gold and pvp_enabled (handle missing columns gracefully for existing databases)
    try:
        gold = character['gold'] if 'gold' in character.keys() else 0
    except (KeyError, AttributeError):
        gold = 0
    
    try:
        pvp_enabled = bool(character['pvp_enabled']) if 'pvp_enabled' in character.keys() else False
    except (KeyError, AttributeError):
        pvp_enabled = False
    
    try:
        combat_stance = character.get('combat_stance', 'balanced')
    except (KeyError, AttributeError):
        combat_stance = 'balanced'
    
    return {
        "success": True,
        "character": {
            "id": character['id'],
            "name": character['name'],
            "level": character['level'],
            "exp": character['exp'],
            "skill_points": character['skill_points'],
            "stats": stats,
            "equipment": equipment,
            "inventory": inventory,
            "combat_stats": combat_stats,
            "auto_combat": bool(character['auto_combat']),
            "gold": gold,
            "pvp_enabled": pvp_enabled,
            "combat_stance": combat_stance
        }
    }


@app.put("/api/character/{character_id}/stance")
async def update_combat_stance(character_id: str, request: Dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Update combat stance"""
    user_id = current_user["user_id"]
    stance = request.get('stance')
    if stance not in ['offensive', 'defensive', 'balanced']:
        raise HTTPException(status_code=400, detail="Invalid stance. Must be 'offensive', 'defensive', or 'balanced'")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM characters WHERE id = ? AND user_id = ?", (character_id, user_id))
    character = cursor.fetchone()
    
    if not character:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    cursor.execute(
        "UPDATE characters SET combat_stance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (stance, character_id)
    )
    
    conn.commit()
    conn.close()
    
    return {"success": True, "stance": stance}

@app.post("/api/character/{character_id}/skills")
async def allocate_skills(character_id: str, request: AllocateSkillsRequest, current_user: dict = Depends(get_current_user)):
    """Allocate skill points"""
    user_id = current_user["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM characters WHERE id = ? AND user_id = ?", (character_id, user_id))
    character = cursor.fetchone()
    
    if not character:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    current_stats = json.loads(character['stats_json'])
    available_points = character['skill_points']
    
    # Calculate total points being allocated
    total_new_points = sum(request.stats.values())
    total_current_points = sum(current_stats.values())
    base_points = len(PRIMARY_STATS) * 10  # Starting 10 in each
    
    points_used = total_current_points - base_points
    new_points_used = sum(request.stats.values()) - base_points
    
    # Validate points
    if new_points_used > points_used + available_points:
        conn.close()
        raise HTTPException(status_code=400, detail="Not enough skill points")
    
    # Validate stat values (min 1, max 100 base)
    for stat, value in request.stats.items():
        if stat not in PRIMARY_STATS:
            conn.close()
            raise HTTPException(status_code=400, detail=f"Invalid stat: {stat}")
        if value < 1 or value > 100:
            conn.close()
            raise HTTPException(status_code=400, detail=f"Stat {stat} must be between 1 and 100")
    
    # Update stats
    new_skill_points = available_points - (new_points_used - points_used)
    
    cursor.execute(
        "UPDATE characters SET stats_json = ?, skill_points = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (json.dumps(request.stats), new_skill_points, character_id)
    )
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Skills allocated successfully"}

# Equipment endpoints
@app.post("/api/equipment/drop")
async def drop_equipment(request: Dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Generate and drop equipment"""
    user_id = current_user["user_id"]
    character_id = request.get('character_id')
    is_pvp = request.get('is_pvp', False)
    
    if not character_id:
        raise HTTPException(status_code=400, detail="character_id required")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify character belongs to user
    cursor.execute("SELECT level FROM characters WHERE id = ? AND user_id = ?", (character_id, user_id))
    character = cursor.fetchone()
    
    if not character:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    level = character['level']
    rarity = roll_equipment_rarity(is_pvp)
    slot = random.choice(EQUIPMENT_SLOTS)
    
    equipment = generate_equipment(slot, rarity, level)
    
    # Add to inventory
    cursor.execute("SELECT inventory_json FROM characters WHERE id = ?", (character_id,))
    char = cursor.fetchone()
    inventory = json.loads(char['inventory_json'])
    inventory.append(equipment)
    
    cursor.execute(
        "UPDATE characters SET inventory_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (json.dumps(inventory), character_id)
    )
    
    conn.commit()
    conn.close()
    
    return {"success": True, "equipment": equipment}

@app.post("/api/equipment/equip")
async def equip_item(request: Dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Equip an item"""
    user_id = current_user["user_id"]
    character_id = request.get('character_id')
    
    # Verify character belongs to user
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM characters WHERE id = ? AND user_id = ?", (character_id, user_id))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="Character not found or access denied")
    conn.close()
    item_id = request.get('item_id')
    slot = request.get('slot')
    
    if not character_id or not item_id or not slot:
        raise HTTPException(status_code=400, detail="character_id, item_id, and slot required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT equipment_json, inventory_json FROM characters WHERE id = ?", (character_id,))
    character = cursor.fetchone()
    
    if not character:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    equipment = json.loads(character['equipment_json'])
    inventory = json.loads(character['inventory_json'])
    
    # Find item in inventory
    item = None
    item_index = None
    for i, inv_item in enumerate(inventory):
        if inv_item.get('id') == item_id:
            item = inv_item
            item_index = i
            break
    
    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found in inventory")
    
    if item.get('slot') != slot:
        conn.close()
        raise HTTPException(status_code=400, detail="Item slot mismatch")
    
    # Unequip current item if any
    current_item = equipment.get(slot)
    if current_item:
        inventory.append(current_item)
    
    # Equip new item
    equipment[slot] = item
    inventory.pop(item_index)
    
    cursor.execute(
        "UPDATE characters SET equipment_json = ?, inventory_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (json.dumps(equipment), json.dumps(inventory), character_id)
    )
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Item equipped successfully"}

@app.post("/api/equipment/unequip")
async def unequip_item(request: Dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Unequip an item"""
    user_id = current_user["user_id"]
    character_id = request.get('character_id')
    
    # Verify character belongs to user
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM characters WHERE id = ? AND user_id = ?", (character_id, user_id))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="Character not found or access denied")
    conn.close()
    slot = request.get('slot')
    
    if not character_id or not slot:
        raise HTTPException(status_code=400, detail="character_id and slot required")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT equipment_json, inventory_json FROM characters WHERE id = ?", (character_id,))
    character = cursor.fetchone()
    
    if not character:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    equipment = json.loads(character['equipment_json'])
    inventory = json.loads(character['inventory_json'])
    
    if slot not in equipment or not equipment[slot]:
        conn.close()
        raise HTTPException(status_code=400, detail="No item equipped in that slot")
    
    # Move to inventory
    inventory.append(equipment[slot])
    equipment[slot] = None
    
    cursor.execute(
        "UPDATE characters SET equipment_json = ?, inventory_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (json.dumps(equipment), json.dumps(inventory), character_id)
    )
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Item unequipped successfully"}

# Combat state management functions
def generate_combat_id() -> str:
    """Generate a unique combat ID"""
    return f"combat_{random.randint(100000, 999999)}{int(datetime.now().timestamp())}"

def initialize_combat_state(character1_id: str, character2_data: Dict, is_pvp: bool = False) -> str:
    """Initialize a new combat state and return combat_id"""
    combat_id = generate_combat_id()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get player character
    cursor.execute("SELECT * FROM characters WHERE id = ?", (character1_id,))
    char1 = cursor.fetchone()
    
    if not char1:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    char1_stats = json.loads(char1['stats_json'])
    char1_equipment = json.loads(char1['equipment_json'])
    char1_equipment_stats = get_equipment_stats(char1_equipment)
    char1_combat = calculate_combat_stats(char1_stats, char1_equipment_stats, char1_equipment)
    char1_weapon_type = get_weapon_type(char1_equipment)
    
    # Get ability loadout and combat stance
    cursor.execute("SELECT ability_id, slot_position FROM character_abilities WHERE character_id = ? ORDER BY slot_position", (character1_id,))
    loadout_rows = cursor.fetchall()
    ability_loadout = {}
    for row in loadout_rows:
        ability_loadout[row['slot_position']] = row['ability_id']
    
    # Get combat stance (handle missing column gracefully)
    try:
        combat_stance = char1['combat_stance'] if 'combat_stance' in char1.keys() else 'balanced'
    except (KeyError, AttributeError):
        combat_stance = 'balanced'
    
    # Get opponent data
    if isinstance(character2_data, dict) and 'id' in character2_data:
        # AI or offline player
        char2_combat = character2_data.get('combat_stats', {})
        char2_name = character2_data.get('name', 'Enemy')
        char2_id = character2_data.get('id')
        char2_level = character2_data.get('level', 1)
        char2_weapon_type = get_weapon_type(character2_data.get('equipment', {}))
    else:
        # Live player
        cursor.execute("SELECT * FROM characters WHERE id = ?", (character2_data,))
        char2 = cursor.fetchone()
        if not char2:
            conn.close()
            raise HTTPException(status_code=404, detail="Opponent not found")
        
        char2_stats = json.loads(char2['stats_json'])
        char2_equipment = json.loads(char2['equipment_json'])
        char2_equipment_stats = get_equipment_stats(char2_equipment)
        char2_combat = calculate_combat_stats(char2_stats, char2_equipment_stats, char2_equipment)
        char2_name = char2['name']
        char2_id = char2['id']
        char2_level = char2['level']
        char2_weapon_type = get_weapon_type(char2_equipment)
    
    conn.close()
    
    # Initialize combat state
    combat_state = {
        'combat_id': combat_id,
        'character1_id': character1_id,
        'character2_id': char2_id,
        'is_pvp': is_pvp,
        'is_auto_fight': False,  # Flag to indicate if this is part of an auto-fight session
        'started_at': datetime.now().isoformat(),
        'player1': {
            'id': character1_id,
            'name': char1['name'],
            'level': char1['level'],
            'current_hp': char1_combat['max_hp'],
            'max_hp': char1_combat['max_hp'],
            'current_mana': char1_combat['max_mana'],
            'max_mana': char1_combat['max_mana'],
            'combat_stats': char1_combat,
            'weapon_type': char1_weapon_type,
            'attack_speed': get_weapon_attack_speed(char1_weapon_type, char1_equipment),
            'equipment': char1_equipment,  # Store equipment for dual wielding calculations
            'last_attack_time': datetime.now().timestamp(),
            'last_mana_regen_time': datetime.now().timestamp(),
            'auto_attack_enabled': True,
            'auto_ability_enabled': False,
            'ability_cooldowns': {},
            'buffs': {},
            'debuffs': {}
        },
        'player2': {
            'id': char2_id,
            'name': char2_name,
            'level': char2_level,
            'current_hp': char2_combat['max_hp'],
            'max_hp': char2_combat['max_hp'],
            'current_mana': char2_combat.get('max_mana', 50),
            'max_mana': char2_combat.get('max_mana', 50),
            'combat_stats': char2_combat,
            'weapon_type': char2_weapon_type,
            'attack_speed': get_weapon_attack_speed(char2_weapon_type, char2_equipment),
            'equipment': char2_equipment,  # Store equipment for dual wielding calculations
            'last_attack_time': datetime.now().timestamp(),
            'last_mana_regen_time': datetime.now().timestamp(),
            'auto_attack_enabled': True,
            'auto_ability_enabled': False,
            'ability_cooldowns': {},
            'buffs': {},
            'debuffs': {}
        },
        'combat_log': [],
        'visual_events': [],  # For frontend animations
        'winner_id': None,
        'is_active': True
    }
    
    set_combat_state(combat_id, combat_state)
    return combat_id

# Combat endpoints
@app.post("/api/combat/start")
async def start_combat(request: Dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Start a new combat encounter"""
    user_id = current_user["user_id"]
    character_id = request.get('character_id')
    
    # Verify character belongs to user
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM characters WHERE id = ? AND user_id = ?", (character_id, user_id))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="Character not found or access denied")
    conn.close()
    opponent_id = request.get('opponent_id')
    enemy_id = request.get('enemy_id')  # For PvE
    is_pvp = request.get('is_pvp', False)
    
    if not character_id:
        raise HTTPException(status_code=400, detail="character_id required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if is_pvp:
        if not opponent_id:
            raise HTTPException(status_code=400, detail="opponent_id required for PvP")
        
        # Get opponent character
        cursor.execute("SELECT * FROM characters WHERE id = ?", (opponent_id,))
        opponent = cursor.fetchone()
        
        if not opponent:
            conn.close()
            raise HTTPException(status_code=404, detail="Opponent not found")
        
        opponent_stats = json.loads(opponent['stats_json'])
        opponent_equipment = json.loads(opponent['equipment_json'])
        opponent_equipment_stats = get_equipment_stats(opponent_equipment)
        opponent_combat = calculate_combat_stats(opponent_stats, opponent_equipment_stats, opponent_equipment)
        
        opponent_data = {
            'id': opponent['id'],
            'name': opponent['name'],
            'level': opponent['level'],
            'stats': opponent_stats,
            'equipment': opponent_equipment,
            'combat_stats': opponent_combat
        }
    else:
        # PvE - get enemy data
        if not enemy_id:
            raise HTTPException(status_code=400, detail="enemy_id required for PvE")
        
        cursor.execute("SELECT * FROM pve_enemies WHERE id = ?", (enemy_id,))
        enemy = cursor.fetchone()
        
        if not enemy:
            conn.close()
            raise HTTPException(status_code=404, detail="Enemy not found")
        
        enemy_stats = json.loads(enemy['stats_json'])
        enemy_equipment = {slot: None for slot in EQUIPMENT_SLOTS}
        enemy_equipment_stats = get_equipment_stats(enemy_equipment)
        enemy_combat = calculate_combat_stats(enemy_stats, enemy_equipment_stats)
        
        opponent_data = {
            'id': enemy['id'],
            'name': enemy['name'],
            'level': enemy['level'],
            'stats': enemy_stats,
            'equipment': enemy_equipment,
            'combat_stats': enemy_combat
        }
    
    conn.close()
    
    combat_id = initialize_combat_state(character_id, opponent_data, is_pvp)
    
    return {"success": True, "combat_id": combat_id}

@app.get("/api/combat/state/{combat_id}")
async def get_combat_state(combat_id: str):
    """Get current combat state (polling endpoint)"""
    state = get_combat_state(combat_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Combat not found")
    
    # Process combat turns if active
    if state['is_active']:
        process_combat_turns(combat_id)
    
    # Get visual events and clear them (so frontend only gets new events)
    visual_events = state.get('visual_events', [])
    
    # Debug: log visual events being sent
    if visual_events:
        print(f"[DEBUG] Sending {len(visual_events)} visual events for combat {combat_id}: {[e.get('type') for e in visual_events]}")
    
    response = {"success": True, "combat": state}
    # Always include visual_events array, even if empty
    response['visual_events'] = visual_events
    
    # Clear after sending (so frontend only gets new events)
    state['visual_events'] = []
    set_combat_state(combat_id, state)  # Save updated state
    
    return response

def process_combat_turns(combat_id: str):
    """Process combat turns based on attack speeds"""
    state = get_combat_state(combat_id)
    if state is None:
        return
    if not state['is_active']:
        return
    
    current_time = datetime.now().timestamp()
    player1 = state['player1']
    player2 = state['player2']
    
    # Check for stuns before processing actions
    player1_stunned = any(d.get('type') == 'stun' and current_time < d.get('expires_at', 0) 
                         for d in player1['debuffs'].values())
    player2_stunned = any(d.get('type') == 'stun' and current_time < d.get('expires_at', 0) 
                         for d in player2['debuffs'].values())
    
    # Process player1 auto-attack (if not stunned)
    if player1['auto_attack_enabled'] and player1['current_hp'] > 0 and not player1_stunned:
        time_since_last_attack = current_time - player1['last_attack_time']
        if time_since_last_attack >= player1['attack_speed']:
            perform_auto_attack(state, 'player1', 'player2')
            player1['last_attack_time'] = current_time
    
    # Process player2 auto-attack (if not stunned)
    if player2['auto_attack_enabled'] and player2['current_hp'] > 0 and not player2_stunned:
        time_since_last_attack = current_time - player2['last_attack_time']
        if time_since_last_attack >= player2['attack_speed']:
            perform_auto_attack(state, 'player2', 'player1')
            player2['last_attack_time'] = current_time
    
    # Process auto-abilities (if not stunned)
    if player1['auto_ability_enabled'] and player1['current_hp'] > 0 and not player1_stunned:
        process_auto_abilities(state, 'player1', 'player2')
    
    if player2['auto_ability_enabled'] and player2['current_hp'] > 0 and not player2_stunned:
        process_auto_abilities(state, 'player2', 'player1')
    
    # Regenerate mana for both players
    regenerate_mana(state, 'player1', current_time)
    regenerate_mana(state, 'player2', current_time)
    
    # Process status effects
    process_status_effects(state, 'player1', current_time)
    process_status_effects(state, 'player2', current_time)
    
    # Update ability cooldowns
    update_ability_cooldowns(state, current_time)
    
    # Check for combat end
    if player1['current_hp'] <= 0 or player2['current_hp'] <= 0:
        end_combat(combat_id)

def perform_auto_attack(state: Dict, attacker_key: str, defender_key: str):
    """Perform an auto-attack"""
    attacker = state[attacker_key]
    defender = state[defender_key]
    
    if attacker['current_hp'] <= 0 or defender['current_hp'] <= 0:
        return
    
    weapon_type = attacker['weapon_type']
    damage_type = get_weapon_damage_type(weapon_type)
    
    hit, crit, dodged, parried = check_hit(attacker['combat_stats'], defender['combat_stats'])
    
    # Add visual event for attack animation
    state['visual_events'].append({
        'type': 'attack',
        'attacker': attacker_key,
        'defender': defender_key,
        'timestamp': datetime.now().timestamp()
    })
    
    if hit:
        # Get attacker equipment for dual wielding calculation
        attacker_equipment = attacker.get('equipment', {})
        damage = calculate_damage(
            attacker['combat_stats'],
            defender['combat_stats'],
            crit,
            damage_type,
            1.0,  # Basic attack multiplier
            attacker.get('buffs', {}),
            defender.get('debuffs', {}),
            attacker_equipment
        )
        defender['current_hp'] = max(0, defender['current_hp'] - damage)
        
        # Add visual events for hit and damage number
        state['visual_events'].append({
            'type': 'hit',
            'target': defender_key,
            'damage': damage,
            'is_crit': crit,
            'timestamp': datetime.now().timestamp()
        })
        
        crit_text = " (CRIT!)" if crit else ""
        state['combat_log'].append(
            f"{attacker['name']} attacks {defender['name']} for {damage} damage{crit_text}"
        )
    elif dodged:
        # Add visual event for dodge
        state['visual_events'].append({
            'type': 'dodge',
            'target': defender_key,
            'timestamp': datetime.now().timestamp()
        })
        state['combat_log'].append(f"{defender['name']} dodges {attacker['name']}'s attack!")
    elif parried:
        # Add visual event for parry
        state['visual_events'].append({
            'type': 'parry',
            'target': defender_key,
            'timestamp': datetime.now().timestamp()
        })
        state['combat_log'].append(f"{defender['name']} parries {attacker['name']}'s attack!")
    else:
        # Miss (shouldn't normally happen, but handle it)
        state['visual_events'].append({
            'type': 'miss',
            'target': defender_key,
            'timestamp': datetime.now().timestamp()
        })
        state['combat_log'].append(f"{attacker['name']} misses {defender['name']}!")

def process_auto_abilities(state: Dict, attacker_key: str, defender_key: str):
    """Process auto-triggered abilities with loadout cycling and stance-based prioritization"""
    attacker = state[attacker_key]
    current_time = datetime.now().timestamp()
    
    # Check if stunned
    for debuff_data in attacker['debuffs'].values():
        if debuff_data.get('type') == 'stun' and current_time < debuff_data.get('expires_at', 0):
            return  # Stunned, cannot use abilities
    
    # Get equipped weapon abilities
    weapon_type = attacker['weapon_type']
    if not weapon_type:
        return
    
    abilities = get_abilities_for_weapon(weapon_type)
    ability_loadout = attacker.get('ability_loadout', {})
    combat_stance = attacker.get('combat_stance', 'balanced')
    last_slot = attacker.get('last_ability_slot_used', 0)
    
    # If no loadout, use default behavior (first available non-ultimate)
    if not ability_loadout:
        regular_abilities = [a for a in abilities if not a['is_ultimate']]
        for ability in regular_abilities:
            ability_id = ability['id']
            cooldown_key = f"{ability_id}_cooldown"
            if (cooldown_key not in attacker['ability_cooldowns'] or 
                current_time >= attacker['ability_cooldowns'][cooldown_key]):
                if attacker['current_mana'] >= ability['mana_cost']:
                    trigger_ability(state, attacker_key, defender_key, ability_id)
                    break
        return
    
    # Get available abilities from loadout, sorted by priority (slot order)
    available_abilities = []
    for slot in sorted(ability_loadout.keys(), key=int):
        ability_id = ability_loadout[slot]
        ability = next((a for a in abilities if a['id'] == ability_id), None)
        if not ability or ability['is_ultimate']:
            continue  # Skip ultimates in auto-combat
        
        cooldown_key = f"{ability_id}_cooldown"
        is_off_cooldown = (cooldown_key not in attacker['ability_cooldowns'] or 
                          current_time >= attacker['ability_cooldowns'][cooldown_key])
        has_mana = attacker['current_mana'] >= ability['mana_cost']
        
        if is_off_cooldown and has_mana:
            available_abilities.append({
                'ability': ability,
                'slot': int(slot),
                'ability_id': ability_id
            })
    
    if not available_abilities:
        return  # No abilities available
    
    # Filter by stance if needed
    if combat_stance == 'offensive':
        # Prioritize damage-dealing abilities
        available_abilities.sort(key=lambda x: x['ability'].get('damage_multiplier', 0), reverse=True)
    elif combat_stance == 'defensive':
        # Prioritize defensive abilities (those with buffs or debuffs that help defense)
        # For now, just use loadout order
        available_abilities.sort(key=lambda x: x['slot'])
    else:  # balanced
        # Use loadout order, starting from last used slot
        available_abilities.sort(key=lambda x: (x['slot'] >= last_slot, x['slot']))
    
    # Use first available ability
    selected = available_abilities[0]
    trigger_ability(state, attacker_key, defender_key, selected['ability_id'])
    attacker['last_ability_slot_used'] = selected['slot']

def regenerate_mana(state: Dict, player_key: str, current_time: float):
    """Regenerate mana based on mana_regen_per_second"""
    player = state[player_key]
    if player['current_hp'] <= 0:
        return
    
    mana_regen = player['combat_stats'].get('mana_regen_per_second', 1.0)
    last_regen = player.get('last_mana_regen_time', current_time)
    time_elapsed = current_time - last_regen
    
    if time_elapsed > 0:
        mana_gained = mana_regen * time_elapsed
        player['current_mana'] = min(
            player['max_mana'],
            player['current_mana'] + mana_gained
        )
        player['last_mana_regen_time'] = current_time

def process_status_effects(state: Dict, player_key: str, current_time: float):
    """Process active buffs and debuffs"""
    player = state[player_key]
    if player['current_hp'] <= 0:
        return
    
    # Track last process time to apply DoT effects per second
    last_process = player.get('last_status_process_time', current_time)
    time_elapsed = current_time - last_process
    
    # Process buffs
    expired_buffs = []
    for buff_id, buff_data in player['buffs'].items():
        if current_time >= buff_data['expires_at']:
            expired_buffs.append(buff_id)
        else:
            # Apply buff effects (damage over time, healing, etc.)
            if buff_data['type'] == 'damage_boost':
                # Handled in damage calculation
                pass
            elif buff_data['type'] == 'heal_over_time':
                # Heal per second
                if time_elapsed >= 1.0:  # Process every second
                    heal_amount = buff_data.get('power', 0)
                    player['current_hp'] = min(
                        player['max_hp'],
                        player['current_hp'] + heal_amount
                    )
                    state['visual_events'].append({
                        'type': 'heal',
                        'target': player_key,
                        'amount': heal_amount,
                        'timestamp': current_time
                    })
    
    # Remove expired buffs
    for buff_id in expired_buffs:
        del player['buffs'][buff_id]
    
    # Process debuffs
    expired_debuffs = []
    for debuff_id, debuff_data in player['debuffs'].items():
        if current_time >= debuff_data['expires_at']:
            expired_debuffs.append(debuff_id)
        else:
            # Apply debuff effects
            if debuff_data['type'] == 'poison':
                # Poison damage per second
                if time_elapsed >= 1.0:  # Process every second
                    # Sum all poison stacks
                    poison_stacks = [ddata for did, ddata in player['debuffs'].items() 
                                   if ddata['type'] == 'poison' and current_time < ddata['expires_at']]
                    total_poison_damage = sum(stack.get('power', 0) for stack in poison_stacks)
                    if total_poison_damage > 0:
                        player['current_hp'] = max(0, player['current_hp'] - total_poison_damage)
                        state['visual_events'].append({
                            'type': 'poison',
                            'target': player_key,
                            'damage': int(total_poison_damage),
                            'timestamp': current_time
                        })
            elif debuff_data['type'] == 'stun':
                # Prevent actions (handled in action processing)
                pass
            # Slow and vulnerability are handled in stat calculations
    
    # Remove expired debuffs
    for debuff_id in expired_debuffs:
        del player['debuffs'][debuff_id]
    
    # Update last process time
    if time_elapsed >= 1.0:
        player['last_status_process_time'] = current_time

def apply_status_effect(state: Dict, target_key: str, effect_type: str, power: float, duration: float, 
                       charisma: int = 0, max_stacks: int = 5, aoe: bool = False):
    """Apply a status effect (buff or debuff) to a player with stacking support"""
    target = state[target_key]
    current_time = datetime.now().timestamp()
    
    # Charisma affects effect power and duration
    power_multiplier = 1.0 + (charisma * 0.01)  # +1% per Charisma point
    duration_multiplier = 1.0 + (charisma * 0.02)  # +2% per Charisma point
    
    adjusted_power = power * power_multiplier
    adjusted_duration = duration * duration_multiplier
    
    effect_id = f"{effect_type}_{int(current_time * 1000)}"
    
    effect_data = {
        'type': effect_type,
        'power': adjusted_power,
        'applied_at': current_time,
        'expires_at': current_time + adjusted_duration
    }
    
    # Determine if it's a buff or debuff
    buff_types = ['damage_boost', 'defense_boost', 'speed_boost', 'heal_over_time']
    if effect_type in buff_types:
        # Check stacking for buffs
        existing_stacks = [bid for bid, bdata in target['buffs'].items() if bdata['type'] == effect_type]
        if len(existing_stacks) >= max_stacks:
            # Remove oldest stack
            oldest_id = min(existing_stacks, key=lambda bid: target['buffs'][bid]['applied_at'])
            del target['buffs'][oldest_id]
        target['buffs'][effect_id] = effect_data
    else:
        # Check status resistance (Wisdom-based)
        wisdom = target['combat_stats'].get('magic_resistance', 0) / 0.5  # Rough estimate
        resistance_chance = min(wisdom * 0.001, 0.5)  # Max 50% resistance
        
        if random.random() > resistance_chance:
            # Check stacking for debuffs
            existing_stacks = [did for did, ddata in target['debuffs'].items() if ddata['type'] == effect_type]
            if len(existing_stacks) >= max_stacks:
                # Remove oldest stack
                oldest_id = min(existing_stacks, key=lambda did: target['debuffs'][did]['applied_at'])
                del target['debuffs'][oldest_id]
            target['debuffs'][effect_id] = effect_data

def update_ability_cooldowns(state: Dict, current_time: float):
    """Update ability cooldowns"""
    for player_key in ['player1', 'player2']:
        player = state[player_key]
        cooldowns_to_remove = []
        
        for cooldown_key, cooldown_end in player['ability_cooldowns'].items():
            if current_time >= cooldown_end:
                cooldowns_to_remove.append(cooldown_key)
        
        for key in cooldowns_to_remove:
            del player['ability_cooldowns'][key]

def trigger_ability(state: Dict, attacker_key: str, defender_key: str, ability_id: str):
    """Trigger an ability"""
    attacker = state[attacker_key]
    defender = state[defender_key]
    
    ability = get_ability_by_id(ability_id)
    if not ability:
        return
    
    # Check mana
    if attacker['current_mana'] < ability['mana_cost']:
        return
    
    # Check cooldown
    current_time = datetime.now().timestamp()
    cooldown_key = f"{ability_id}_cooldown"
    if cooldown_key in attacker['ability_cooldowns']:
        if current_time < attacker['ability_cooldowns'][cooldown_key]:
            return
    
    # Consume mana
    attacker['current_mana'] -= ability['mana_cost']
    
    # Set cooldown
    attacker['ability_cooldowns'][cooldown_key] = current_time + ability['cooldown_seconds']
    
    # Add visual event for ability use
    state['visual_events'].append({
        'type': 'ability',
        'attacker': attacker_key,
        'defender': defender_key,
        'ability_id': ability_id,
        'ability_name': ability['name'],
        'timestamp': datetime.now().timestamp()
    })
    
    # Calculate damage
    hit, crit, dodged, parried = check_hit(attacker['combat_stats'], defender['combat_stats'])
    
    if hit:
        is_crit = crit or ability_id.endswith('_assassinate')  # Assassinate always crits
        # Get attacker equipment for dual wielding calculation
        attacker_equipment = attacker.get('equipment', {})
        damage = calculate_damage(
            attacker['combat_stats'],
            defender['combat_stats'],
            is_crit,
            ability['damage_type'],
            ability['damage_multiplier'],
            attacker.get('buffs', {}),
            defender.get('debuffs', {}),
            attacker_equipment
        )
        defender['current_hp'] = max(0, defender['current_hp'] - damage)
        
        # Add visual event for ability hit
        state['visual_events'].append({
            'type': 'hit',
            'target': defender_key,
            'damage': damage,
            'is_crit': is_crit,
            'is_ability': True,
            'ability_name': ability['name'],
            'timestamp': datetime.now().timestamp()
        })
        
        # Apply status effects from ability
        if 'status_effects' in ability:
            # Get attacker's charisma for effect scaling
            attacker_charisma = attacker.get('charisma', 0)
            for effect in ability['status_effects']:
                # Roll for chance
                if random.random() <= effect.get('chance', 1.0):
                    effect_type = effect['type']
                    effect_power = effect.get('power', 0)
                    effect_duration = effect.get('duration', 5)
                    max_stacks = effect.get('max_stacks', 5)
                    is_aoe = effect.get('aoe', False)
                    target = effect.get('target', 'enemy')
                    
                    # Determine target
                    if target == 'self':
                        apply_target = attacker_key
                    else:
                        apply_target = defender_key
                    
                    apply_status_effect(
                        state, 
                        apply_target, 
                        effect_type, 
                        effect_power, 
                        effect_duration,
                        attacker_charisma,
                        max_stacks,
                        is_aoe
                    )
        
        crit_text = " (CRIT!)" if is_crit else ""
        state['combat_log'].append(
            f"{attacker['name']} uses {ability['name']} on {defender['name']} for {damage} damage{crit_text}"
        )
    elif dodged:
        # Add visual event for dodge
        state['visual_events'].append({
            'type': 'dodge',
            'target': defender_key,
            'timestamp': datetime.now().timestamp()
        })
        state['combat_log'].append(f"{defender['name']} dodges {attacker['name']}'s {ability['name']}!")
    elif parried:
        # Add visual event for parry
        state['visual_events'].append({
            'type': 'parry',
            'target': defender_key,
            'timestamp': datetime.now().timestamp()
        })
        state['combat_log'].append(f"{defender['name']} parries {attacker['name']}'s {ability['name']}!")
    else:
        # Miss
        state['visual_events'].append({
            'type': 'miss',
            'target': defender_key,
            'timestamp': datetime.now().timestamp()
        })
        state['combat_log'].append(f"{attacker['name']}'s {ability['name']} misses {defender['name']}!")

@app.post("/api/combat/ability/{combat_id}")
async def use_ability(combat_id: str, request: Dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Manually trigger an ability"""
    user_id = current_user["user_id"]
    ability_id = request.get('ability_id')
    character_id = request.get('character_id')
    
    # Verify character belongs to user
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM characters WHERE id = ? AND user_id = ?", (character_id, user_id))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="Character not found or access denied")
    conn.close()
    
    state = get_combat_state(combat_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Combat not found")
    
    # Determine which player is using the ability
    if state['player1']['id'] == character_id:
        attacker_key = 'player1'
        defender_key = 'player2'
    elif state['player2']['id'] == character_id:
        attacker_key = 'player2'
        defender_key = 'player1'
    else:
        raise HTTPException(status_code=403, detail="Character not in this combat")
    
    trigger_ability(state, attacker_key, defender_key, ability_id)
    
    # Check for combat end
    if state['player1']['current_hp'] <= 0 or state['player2']['current_hp'] <= 0:
        end_combat(combat_id)
    
    return {"success": True, "combat": state}

@app.post("/api/combat/auto-toggle/{combat_id}")
async def toggle_auto_combat(combat_id: str, request: Dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Toggle auto-attack or auto-ability"""
    user_id = current_user["user_id"]
    character_id = request.get('character_id')
    
    # Verify character belongs to user
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM characters WHERE id = ? AND user_id = ?", (character_id, user_id))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="Character not found or access denied")
    conn.close()
    toggle_type = request.get('toggle_type')  # 'attack' or 'ability'
    enabled = request.get('enabled', True)
    
    state = get_combat_state(combat_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Combat not found")
    
    # Determine which player
    if state['player1']['id'] == character_id:
        player = state['player1']
    elif state['player2']['id'] == character_id:
        player = state['player2']
    else:
        raise HTTPException(status_code=403, detail="Character not in this combat")
    
    if toggle_type == 'attack':
        player['auto_attack_enabled'] = enabled
    elif toggle_type == 'ability':
        player['auto_ability_enabled'] = enabled
    else:
        raise HTTPException(status_code=400, detail="Invalid toggle_type")
    
    return {"success": True, "combat": state}

def end_combat(combat_id: str):
    """End combat and award rewards"""
    if combat_id not in combat_states:
        return
    
    state = get_combat_state(combat_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Combat not found")
    state['is_active'] = False
    
    # Determine winner
    if state['player1']['current_hp'] > 0:
        winner_id = state['player1']['id']
        loser_id = state['player2']['id']
        winner_level = state['player1']['level']
        loser_level = state['player2']['level']
    else:
        winner_id = state['player2']['id']
        loser_id = state['player1']['id']
        winner_level = state['player2']['level']
        loser_level = state['player1']['level']
    
    state['winner_id'] = winner_id
    
    # Skip database updates if this is part of an auto-fight session
    # Rewards will be accumulated and applied at the end of the session
    is_auto_fight = state.get('is_auto_fight', False)
    
    # Calculate rewards (always, so they can be extracted for auto-fight)
    if winner_id == state['player1']['id']:
        # Calculate rewards
        exp_gain = calculate_exp_gain(winner_level, loser_level, state['is_pvp'])
        
        # Calculate gold gain based on enemy data for PvE, or opponent level for PvP
        if not state['is_pvp']:
            # PvE - get enemy data
            enemy_id = state['character2_id']
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT gold_min, gold_max, drop_chance, level FROM pve_enemies WHERE id = ?", (enemy_id,))
            enemy_data = cursor.fetchone()
            
            if enemy_data:
                gold_gain = random.randint(enemy_data['gold_min'], enemy_data['gold_max'])
                drop_chance = enemy_data['drop_chance']
                enemy_level = enemy_data['level']
            else:
                gold_gain = random.randint(1, 5)
                drop_chance = 0.0
                enemy_level = loser_level
            conn.close()
        else:
            # PvP
            gold_gain = 100 + loser_level * 10
            drop_chance = 0.7  # 70% for PvP
            enemy_level = loser_level
        
        # Store rewards in combat state (for auto-fight extraction)
        state['rewards'] = {
            'exp_gained': exp_gain,
            'gold_gained': gold_gain,
            'equipment_dropped': False  # Will be calculated if not auto-fight
        }
        
        # Only update database if not auto-fight
        if not is_auto_fight:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Update character
            cursor.execute("SELECT exp, level, gold, skill_points FROM characters WHERE id = ?", (winner_id,))
            char_data = cursor.fetchone()
            new_exp = char_data['exp'] + exp_gain
            new_level = char_data['level']
            new_gold = char_data['gold'] + gold_gain
            current_skill_points = char_data['skill_points']
            
            # Process level up
            char_dict = {
                'level': new_level,
                'exp': new_exp,
                'skill_points': current_skill_points  # Start with current skill points
            }
            char_dict = process_level_up(char_dict)
            
            cursor.execute(
                "UPDATE characters SET exp = ?, level = ?, skill_points = ?, gold = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (char_dict['exp'], char_dict['level'], char_dict.get('skill_points', 0), new_gold, winner_id)
            )
            
            # Drop equipment based on drop chance
            equipment_dropped = False
            if random.random() * 100 < drop_chance:
                rarity = roll_equipment_rarity(state['is_pvp'], enemy_level)
                slot = random.choice(EQUIPMENT_SLOTS)
                equipment = generate_equipment(slot, rarity, char_dict['level'])
                
                cursor.execute("SELECT inventory_json FROM characters WHERE id = ?", (winner_id,))
                inv_data = cursor.fetchone()
                inventory = json.loads(inv_data['inventory_json'])
                
                # Check inventory limit (100 items)
                if len(inventory) < 100:
                    inventory.append(equipment)
                    equipment_dropped = True
                    cursor.execute(
                        "UPDATE characters SET inventory_json = ? WHERE id = ?",
                        (json.dumps(inventory), winner_id)
                    )
            
            state['rewards']['equipment_dropped'] = equipment_dropped
            
            conn.commit()
            conn.close()

@app.post("/api/combat/end/{combat_id}")
async def end_combat_endpoint(combat_id: str):
    """Manually end combat (cleanup)"""
    state = get_combat_state(combat_id)
    if state is not None:
        end_combat(combat_id)
        # Get final state after end_combat
        final_state = get_combat_state(combat_id)
        return {"success": True, "combat": final_state if final_state else state}
    raise HTTPException(status_code=404, detail="Combat not found")

# Legacy combat endpoint (kept for backwards compatibility, but should use new system)
async def resolve_combat(character1_id: str, character2_id_or_data, is_pvp: bool = True):
    """Resolve a combat encounter"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get player character
    cursor.execute("SELECT * FROM characters WHERE id = ?", (character1_id,))
    char1 = cursor.fetchone()
    
    if not char1:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    char1_stats = json.loads(char1['stats_json'])
    char1_equipment = json.loads(char1['equipment_json'])
    char1_equipment_stats = get_equipment_stats(char1_equipment)
    char1_combat = calculate_combat_stats(char1_stats, char1_equipment_stats, char1_equipment)
    
    # Get opponent
    if isinstance(character2_id_or_data, dict):
        # AI opponent
        char2_data = character2_id_or_data
        char2_combat = char2_data['combat_stats']
        char2_name = char2_data['name']
        char2_id = char2_data['id']
    else:
        # Player opponent
        cursor.execute("SELECT * FROM characters WHERE id = ?", (character2_id_or_data,))
        char2 = cursor.fetchone()
        if not char2:
            conn.close()
            raise HTTPException(status_code=404, detail="Opponent not found")
        
        char2_stats = json.loads(char2['stats_json'])
        char2_equipment = json.loads(char2['equipment_json'])
        char2_equipment_stats = get_equipment_stats(char2_equipment)
        char2_combat = calculate_combat_stats(char2_stats, char2_equipment_stats, char2_equipment)
        char2_name = char2['name']
        char2_id = char2['id']
    
    # Initialize combat
    char1_hp = char1_combat['max_hp']
    char2_hp = char2_combat['max_hp']
    char1_mana = char1_combat['max_mana']
    char2_mana = char2_combat['max_mana']
    
    combat_log = []
    turn = 0
    
    # Determine turn order (higher speed goes first)
    char1_first = char1_combat['speed'] >= char2_combat['speed']
    
    # Combat loop
    while char1_hp > 0 and char2_hp > 0 and turn < 50:  # Max 50 turns
        turn += 1
        combat_log.append(f"--- Turn {turn} ---")
        
        # Character 1's turn
        if char1_hp > 0:
            hit, crit, dodged, parried = check_hit(char1_combat, char2_combat)
            if hit:
                damage = calculate_damage(char1_combat, char2_combat, crit, 'physical', 1.0, None, None, char1_equipment)
                char2_hp -= damage
                combat_log.append(f"{char1['name']} attacks {char2_name} for {damage} damage{' (CRIT!)' if crit else ''}")
            else:
                combat_log.append(f"{char2_name} dodges {char1['name']}'s attack!")
        
        if char2_hp <= 0:
            break
        
        # Character 2's turn
        if char2_hp > 0:
            hit, crit, dodged, parried = check_hit(char2_combat, char1_combat)
            if hit:
                char2_equipment_for_damage = char2_equipment if 'char2_equipment' in locals() else {}
                damage = calculate_damage(char2_combat, char1_combat, crit, 'physical', 1.0, None, None, char2_equipment_for_damage)
                char1_hp -= damage
                combat_log.append(f"{char2_name} attacks {char1['name']} for {damage} damage{' (CRIT!)' if crit else ''}")
            else:
                combat_log.append(f"{char1['name']} dodges {char2_name}'s attack!")
    
    # Determine winner
    if char1_hp > 0:
        winner_id = character1_id
        winner_name = char1['name']
        loser_level = char2_data.get('level', 0) if isinstance(character2_id_or_data, dict) else char2['level']
    else:
        winner_id = char2_id
        winner_name = char2_name
        loser_level = char1['level']
    
    # Calculate EXP
    winner_level = char1['level'] if winner_id == character1_id else (char2_data.get('level', 0) if isinstance(character2_id_or_data, dict) else char2['level'])
    exp_gain = calculate_exp_gain(winner_level, loser_level, is_pvp)
    
    # Update winner's EXP and level
    if winner_id == character1_id:
        cursor.execute("SELECT exp, level FROM characters WHERE id = ?", (character1_id,))
        char_data = cursor.fetchone()
        new_exp = char_data['exp'] + exp_gain
        new_level = char_data['level']
        
        # Process level up
        char_dict = {
            'level': new_level,
            'exp': new_exp,
            'skill_points': char1['skill_points']
        }
        char_dict = process_level_up(char_dict)
        
        cursor.execute(
            "UPDATE characters SET exp = ?, level = ?, skill_points = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (char_dict['exp'], char_dict['level'], char_dict['skill_points'], character1_id)
        )
        
        # Drop equipment
        if random.random() < 0.7:  # 70% drop chance
            rarity = roll_equipment_rarity(is_pvp)
            slot = random.choice(EQUIPMENT_SLOTS)
            equipment = generate_equipment(slot, rarity, char_dict['level'])
            
            cursor.execute("SELECT inventory_json FROM characters WHERE id = ?", (character1_id,))
            inv_data = cursor.fetchone()
            inventory = json.loads(inv_data['inventory_json'])
            inventory.append(equipment)
            
            cursor.execute(
                "UPDATE characters SET inventory_json = ? WHERE id = ?",
                (json.dumps(inventory), character1_id)
            )
    
    # Save combat log
    cursor.execute(
        """INSERT INTO combat_logs (character1_id, character2_id, winner_id, log_json)
           VALUES (?, ?, ?, ?)""",
        (character1_id, char2_id, winner_id, json.dumps(combat_log))
    )
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "winner_id": winner_id,
        "winner_name": winner_name,
        "combat_log": combat_log,
        "exp_gained": exp_gain if winner_id == character1_id else 0
    }

@app.post("/api/combat/auto-toggle")
async def toggle_auto_combat(request: Dict = Body(...)):
    """Toggle auto combat mode"""
    character_id = request.get('character_id')
    auto_combat = request.get('auto_combat', False)
    
    if not character_id:
        raise HTTPException(status_code=400, detail="character_id required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE characters SET auto_combat = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (1 if auto_combat else 0, character_id)
    )
    
    conn.commit()
    conn.close()
    
    return {"success": True, "auto_combat": auto_combat}

# PvE endpoints
@app.get("/api/pve/list")
async def list_pve_enemies(character_id: str):
    """Get available PvE enemies for character"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get character level and progress
    cursor.execute("SELECT level FROM characters WHERE id = ?", (character_id,))
    char = cursor.fetchone()
    if not char:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    char_level = char['level']
    
    # Get PvE progress
    cursor.execute("SELECT enemies_unlocked_json FROM character_pve_progress WHERE character_id = ?", (character_id,))
    progress = cursor.fetchone()
    
    if progress:
        unlocked_enemies = json.loads(progress['enemies_unlocked_json'])
    else:
        unlocked_enemies = ['chicken']  # Start with first enemy (Chicken)
        # Initialize progress
        cursor.execute(
            "INSERT OR IGNORE INTO character_pve_progress (character_id, enemies_unlocked_json) VALUES (?, ?)",
            (character_id, json.dumps(unlocked_enemies))
        )
        conn.commit()
    
    # Get all enemies
    cursor.execute("SELECT * FROM pve_enemies ORDER BY story_order")
    all_enemies = cursor.fetchall()
    
    if not all_enemies:
        conn.close()
        return {"success": True, "enemies": []}
    
    # Ensure unlocked list only contains valid enemy IDs
    valid_enemy_ids = {enemy['id'] for enemy in all_enemies}
    filtered_unlocked = [enemy_id for enemy_id in unlocked_enemies if enemy_id in valid_enemy_ids]
    if filtered_unlocked != unlocked_enemies:
        unlocked_enemies = filtered_unlocked
        cursor.execute(
            "UPDATE character_pve_progress SET enemies_unlocked_json = ? WHERE character_id = ?",
            (json.dumps(unlocked_enemies), character_id)
        )
        conn.commit()
    
    # Always unlock the first enemy (Chicken) by default
    first_enemy_id = all_enemies[0]['id']
    if first_enemy_id not in unlocked_enemies:
        unlocked_enemies.insert(0, first_enemy_id)
        cursor.execute(
            "UPDATE character_pve_progress SET enemies_unlocked_json = ? WHERE character_id = ?",
            (json.dumps(unlocked_enemies), character_id)
        )
        conn.commit()
    
    conn.close()
    
    enemies_list = []
    for enemy in all_enemies:
        is_unlocked = enemy['id'] in unlocked_enemies
        keys = enemy.keys()
        description = enemy['description'] if 'description' in keys and enemy['description'] else ''
        gold_min = enemy['gold_min'] if 'gold_min' in keys and enemy['gold_min'] is not None else 1
        gold_max = enemy['gold_max'] if 'gold_max' in keys and enemy['gold_max'] is not None else gold_min
        drop_chance = enemy['drop_chance'] if 'drop_chance' in keys and enemy['drop_chance'] is not None else 0.0
        enemies_list.append({
            'id': enemy['id'],
            'name': enemy['name'],
            'level': enemy['level'],
            'description': description,
            'story_order': enemy['story_order'],
            'unlocked': is_unlocked,
            'gold_min': gold_min,
            'gold_max': gold_max,
            'drop_chance': drop_chance
        })
    
    return {"success": True, "enemies": enemies_list}

def unlock_next_enemy(character_id: str, enemy_id: str) -> bool:
    """Unlock the next PvE enemy after defeating current one"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current progress
    cursor.execute("SELECT enemies_unlocked_json FROM character_pve_progress WHERE character_id = ?", (character_id,))
    progress = cursor.fetchone()
    
    if progress:
        unlocked_enemies = json.loads(progress['enemies_unlocked_json'])
    else:
        unlocked_enemies = ['enemy_1']
    
    # Get next enemy
    cursor.execute("SELECT story_order FROM pve_enemies WHERE id = ?", (enemy_id,))
    current_enemy = cursor.fetchone()
    
    if current_enemy:
        next_order = current_enemy['story_order'] + 1
        cursor.execute("SELECT id FROM pve_enemies WHERE story_order = ?", (next_order,))
        next_enemy = cursor.fetchone()
        
        if next_enemy and next_enemy['id'] not in unlocked_enemies:
            unlocked_enemies.append(next_enemy['id'])
            cursor.execute(
                "UPDATE character_pve_progress SET enemies_unlocked_json = ? WHERE character_id = ?",
                (json.dumps(unlocked_enemies), character_id)
            )
            conn.commit()
    
    conn.close()
    return True

@app.post("/api/pve/unlock")
async def unlock_pve_enemy(character_id: str, enemy_id: str):
    """API endpoint to unlock next enemy after defeating current one"""
    unlock_next_enemy(character_id, enemy_id)
    return {"success": True}

@app.post("/api/pve/auto-fight")
async def start_auto_fight(request: Dict = Body(...)):
    """Start an hour-long auto-fight session against a PvE enemy"""
    character_id = request.get('character_id')
    enemy_id = request.get('enemy_id')
    
    if not character_id or not enemy_id:
        raise HTTPException(status_code=400, detail="character_id and enemy_id required")
    
    # Clean up expired sessions and check if character already has an active session
    current_time = datetime.now().timestamp()
    expired_sessions = []
    r = get_redis_client()
    if r:
        # Get all auto-fight session keys from Redis
        session_keys = r.keys("autofight:*")
        for key in session_keys:
            session_id = key.replace("autofight:", "")
            session = get_auto_fight_session(session_id)
            if session:
                # Remove expired or inactive sessions
                if not session['is_active'] or current_time >= session['end_time']:
                    expired_sessions.append(session_id)
                # Check if character has an active session
                elif session['character_id'] == character_id and session['is_active']:
                    raise HTTPException(status_code=400, detail="Auto-fight session already in progress")
    else:
        # Fallback to in-memory dict
        for session_id, session in list(auto_fight_sessions.items()):
            # Remove expired or inactive sessions
            if not session['is_active'] or current_time >= session['end_time']:
                expired_sessions.append(session_id)
            # Check if character has an active session
            elif session['character_id'] == character_id and session['is_active']:
                raise HTTPException(status_code=400, detail="Auto-fight session already in progress")
    
    # Clean up expired sessions
    for session_id in expired_sessions:
        session = get_auto_fight_session(session_id)
        if session:
            if session['is_active']:
                # End the session properly if it expired
                end_auto_fight_session(session_id)
            else:
                # Just remove inactive sessions
                delete_auto_fight_session(session_id)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify character exists
    cursor.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
    char = cursor.fetchone()
    if not char:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Verify enemy exists
    cursor.execute("SELECT * FROM pve_enemies WHERE id = ?", (enemy_id,))
    enemy = cursor.fetchone()
    if not enemy:
        conn.close()
        raise HTTPException(status_code=404, detail="Enemy not found")
    
    # Check if enemy is unlocked
    cursor.execute("SELECT enemies_unlocked_json FROM character_pve_progress WHERE character_id = ?", (character_id,))
    progress = cursor.fetchone()
    unlocked_enemies = ['chicken']  # Default
    if progress:
        unlocked_enemies = json.loads(progress['enemies_unlocked_json'])
    
    if enemy_id not in unlocked_enemies:
        conn.close()
        raise HTTPException(status_code=400, detail="Enemy not unlocked")
    
    # Get enemy gold range
    keys = enemy.keys()
    gold_min = enemy['gold_min'] if 'gold_min' in keys and enemy['gold_min'] is not None else 1
    gold_max = enemy['gold_max'] if 'gold_max' in keys and enemy['gold_max'] is not None else gold_min
    
    conn.close()
    
    # Create auto-fight session
    session_id = f"autofight_{random.randint(100000, 999999)}{int(datetime.now().timestamp())}"
    
    char_stats = json.loads(char['stats_json'])
    char_equipment = json.loads(char['equipment_json'])
    char_equipment_stats = get_equipment_stats(char_equipment)
    char_combat = calculate_combat_stats(char_stats, char_equipment_stats, char_equipment)
    
    enemy_stats = json.loads(enemy['stats_json'])
    enemy_equipment = {slot: None for slot in EQUIPMENT_SLOTS}
    enemy_equipment_stats = get_equipment_stats(enemy_equipment)
    enemy_combat = calculate_combat_stats(enemy_stats, enemy_equipment_stats, enemy_equipment)
    
    # Get player's weapon type and attack speed
    weapon_type = get_weapon_type(char_equipment)
    player_attack_speed = get_weapon_attack_speed(weapon_type, char_equipment) if weapon_type else 2.0  # Default 2.0s
    # Enemy attack speed (assume average 2.0s for enemies)
    enemy_attack_speed = 2.0
    
    session_data = {
        'session_id': session_id,
        'character_id': character_id,
        'enemy_id': enemy_id,
        'enemy_name': enemy['name'],
        'enemy_level': enemy['level'],
        'gold_min': gold_min,
        'gold_max': gold_max,
        'start_time': datetime.now().timestamp(),
        'end_time': datetime.now().timestamp() + 3600,  # 1 hour
        'last_process_time': datetime.now().timestamp(),  # Track last processing time
        'is_active': True,
        'current_combat_id': None,  # Track current battle in progress
        'current_battle_start_time': None,  # Track when current battle started
        'wins': 0,
        'losses': 0,
        'total_exp_gained': 0,
        'total_gold_gained': 0,
        'items_dropped': [],
        'level_ups': 0,
        'total_damage_dealt': 0,
        'total_damage_taken': 0,
        'total_crits': 0,
        'total_dodges': 0,
        'fastest_victory': None,
        'slowest_victory': None,
        'player_combat_stats': char_combat,
        'enemy_combat_stats': enemy_combat,
        'player_level': char['level'],
        'player_exp': char['exp'],
        'player_attack_speed': player_attack_speed,
        'enemy_attack_speed': enemy_attack_speed,
        'player_weapon_type': weapon_type
    }
    set_auto_fight_session(session_id, session_data)
    
    return {"success": True, "session_id": session_id, "message": "Auto-fight started for 1 hour"}

@app.get("/api/pve/auto-fight/{session_id}")
async def get_auto_fight_status(session_id: str):
    """Get status of auto-fight session"""
    session = get_auto_fight_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Process fights if still active (runs synchronously but quickly)
    if session['is_active']:
        process_auto_fight(session_id)
    
    # Calculate time remaining
    current_time = datetime.now().timestamp()
    time_remaining = max(0, session['end_time'] - current_time)
    elapsed_time = current_time - session['start_time']
    
    return {
        "success": True,
        "session": {
            "session_id": session_id,
            "enemy_name": session['enemy_name'],
            "is_active": session['is_active'],
            "time_remaining": int(time_remaining),
            "elapsed_time": int(elapsed_time),
            "wins": session['wins'],
            "losses": session['losses'],
            "total_exp_gained": session['total_exp_gained'],
            "total_gold_gained": session['total_gold_gained'],
            "items_dropped_count": len(session['items_dropped']),
            "level_ups": session['level_ups'],
            "total_damage_dealt": session['total_damage_dealt'],
            "total_damage_taken": session['total_damage_taken'],
            "total_crits": session['total_crits'],
            "total_dodges": session['total_dodges'],
            "fastest_victory": session['fastest_victory'],
            "slowest_victory": session['slowest_victory']
        }
    }

def process_auto_fight(session_id: str):
    """Process auto-fight session - run fights using real combat system until time is up"""
    session = get_auto_fight_session(session_id)
    if session is None:
        return
    if not session['is_active']:
        return
    
    current_time = datetime.now().timestamp()
    
    # Check if time is up
    if current_time >= session['end_time']:
        end_auto_fight_session(session_id)
        return
    
    # If there's a combat in progress, process it
    current_combat_id = session.get('current_combat_id')
    if current_combat_id and current_combat_id in combat_states:
        combat_state = get_combat_state(current_combat_id)
        if combat_state is None:
            session['current_combat_id'] = None
            set_auto_fight_session(session_id, session)
            return
        
        # Process combat turns
        if combat_state['is_active']:
            process_combat_turns(current_combat_id)
            # Update last process time
            session['last_process_time'] = current_time
            set_auto_fight_session(session_id, session)  # Save updated session
            return
        
        # Combat has ended, process rewards
        battle_start_time = session.get('current_battle_start_time', current_time)
        battle_duration = current_time - battle_start_time
        
        # Determine winner
        if combat_state['player1']['current_hp'] > 0:
            # Player won
            session['wins'] += 1
            if session['fastest_victory'] is None or battle_duration < session['fastest_victory']:
                session['fastest_victory'] = battle_duration
            if session['slowest_victory'] is None or battle_duration > session['slowest_victory']:
                session['slowest_victory'] = battle_duration
            
            # Extract rewards from combat state (calculated by end_combat)
            rewards = combat_state.get('rewards', {})
            exp_gain = rewards.get('exp_gained', 0)
            gold_gain = rewards.get('gold_gained', 0)
            equipment_dropped = rewards.get('equipment_dropped', False)
            
            # If equipment was dropped, generate it
            if equipment_dropped:
                rarity = roll_equipment_rarity(False, session['enemy_level'])
                slot = random.choice(EQUIPMENT_SLOTS)
                equipment = generate_equipment(slot, rarity, session['player_level'])
                session['items_dropped'].append(equipment)
            
            session['total_exp_gained'] += exp_gain
            session['total_gold_gained'] += gold_gain
            
            # Check for level up (tracking only, actual level up happens at session end)
            new_exp = session['player_exp'] + session['total_exp_gained']
            char_dict = {
                'level': session['player_level'],
                'exp': new_exp,
                'skill_points': 0  # Just for tracking, actual skill points handled at session end
            }
            old_level = session['player_level']
            char_dict = process_level_up(char_dict)
            if char_dict['level'] > old_level:
                session['level_ups'] += 1
                session['player_level'] = char_dict['level']
        else:
            # Player lost
            session['losses'] += 1
        
        # Clean up combat state
        delete_combat_state(current_combat_id)
        session['current_combat_id'] = None
        session['current_battle_start_time'] = None
        set_auto_fight_session(session_id, session)  # Save updated session
    
    # Check if we should start a new battle
    if current_time >= session['end_time']:
        end_auto_fight_session(session_id)
        return
    
    # Start a new battle if no combat is in progress
    if not session.get('current_combat_id'):
        # Get enemy data for combat initialization
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pve_enemies WHERE id = ?", (session['enemy_id'],))
        enemy = cursor.fetchone()
        
        if not enemy:
            conn.close()
            return
        
        enemy_stats = json.loads(enemy['stats_json'])
        enemy_equipment = {slot: None for slot in EQUIPMENT_SLOTS}
        enemy_equipment_stats = get_equipment_stats(enemy_equipment)
        enemy_combat = calculate_combat_stats(enemy_stats, enemy_equipment_stats)
        
        opponent_data = {
            'id': enemy['id'],
            'name': enemy['name'],
            'level': enemy['level'],
            'stats': enemy_stats,
            'equipment': enemy_equipment,
            'combat_stats': enemy_combat
        }
        
        conn.close()
        
        # Initialize combat state
        try:
            combat_id = initialize_combat_state(session['character_id'], opponent_data, False)
            # Mark this combat as part of auto-fight session
            state = get_combat_state(combat_id)
            if state is not None:
                state['is_auto_fight'] = True
                set_combat_state(combat_id, state)
            session['current_combat_id'] = combat_id
            session['current_battle_start_time'] = current_time
            session['last_process_time'] = current_time
            set_auto_fight_session(session_id, session)  # Save updated session
        except Exception as e:
            # If combat initialization fails, skip this battle
            print(f"Error initializing combat for auto-fight: {e}")
            session['last_process_time'] = current_time
            set_auto_fight_session(session_id, session)  # Save updated session

def end_auto_fight_session(session_id: str):
    """End auto-fight session and apply all rewards"""
    session = get_auto_fight_session(session_id)
    if session is None:
        return
    if not session['is_active']:
        return
    
    session['is_active'] = False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current character data
    cursor.execute("SELECT exp, level, gold, skill_points, inventory_json FROM characters WHERE id = ?", (session['character_id'],))
    char = cursor.fetchone()
    
    if char:
        # Apply all rewards
        new_exp = char['exp'] + session['total_exp_gained']
        new_gold = char['gold'] + session['total_gold_gained']
        new_level = char['level']
        current_skill_points = char['skill_points']
        
        # Process level ups
        char_dict = {
            'level': new_level,
            'exp': new_exp,
            'skill_points': current_skill_points  # Start with current skill points
        }
        char_dict = process_level_up(char_dict)
        
        # Add items to inventory
        inventory = json.loads(char['inventory_json'])
        for item in session['items_dropped']:
            if len(inventory) < 100:  # Respect inventory limit
                inventory.append(item)
        
        # Update character
        cursor.execute(
            "UPDATE characters SET exp = ?, level = ?, skill_points = ?, gold = ?, inventory_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (char_dict['exp'], char_dict['level'], char_dict.get('skill_points', 0), new_gold, json.dumps(inventory), session['character_id'])
        )
        
        conn.commit()
    
    conn.close()
    
    # Unlock next enemy if player won at least once
    if session['wins'] > 0:
        try:
            unlock_next_enemy(session['character_id'], session['enemy_id'])
        except Exception:
            pass  # Ignore unlock errors

@app.post("/api/pve/auto-fight/{session_id}/stop")
async def stop_auto_fight(session_id: str):
    """Manually stop an auto-fight session early"""
    if session_id not in auto_fight_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    end_auto_fight_session(session_id)
    
    return {"success": True, "message": "Auto-fight session stopped"}

# PvP endpoints
@app.post("/api/pvp/queue")
async def pvp_queue(request: Dict = Body(...)):
    """Join or leave PvP queue"""
    character_id = request.get('character_id')
    action = request.get('action', 'join')  # 'join' or 'leave'
    
    if action == 'join':
        pvp_queue[character_id] = datetime.now().isoformat()
        return {"success": True, "message": "Joined PvP queue"}
    elif action == 'leave':
        if character_id in pvp_queue:
            delete_pvp_queue_entry(character_id)
        return {"success": True, "message": "Left PvP queue"}
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

@app.get("/api/pvp/available")
async def get_pvp_available():
    """Get list of offline players with PvP enabled"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, level FROM characters WHERE pvp_enabled = 1 ORDER BY level DESC LIMIT 20")
    players = cursor.fetchall()
    
    conn.close()
    
    players_list = [{'id': p['id'], 'name': p['name'], 'level': p['level']} for p in players]
    
    return {"success": True, "players": players_list}

@app.post("/api/pvp/toggle")
async def toggle_pvp(request: Dict = Body(...)):
    """Enable/disable PvP availability"""
    character_id = request.get('character_id')
    enabled = request.get('enabled', True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE characters SET pvp_enabled = ? WHERE id = ?",
        (1 if enabled else 0, character_id)
    )
    
    conn.commit()
    conn.close()
    
    return {"success": True, "pvp_enabled": enabled}

@app.post("/api/pvp/match")
async def pvp_match(request: Dict = Body(...)):
    """Match with queue or offline opponent"""
    character_id = request.get('character_id')
    opponent_id = request.get('opponent_id')  # Optional, if provided use that
    
    if opponent_id:
        # Use specific opponent
        return {"success": True, "opponent_id": opponent_id}
    
    # Try to match with queue first
    queue_list = [cid for cid in pvp_queue.keys() if cid != character_id]
    if queue_list:
        opponent_id = queue_list[0]
        delete_pvp_queue_entry(opponent_id)
        if character_id in pvp_queue:
            delete_pvp_queue_entry(character_id)
        return {"success": True, "opponent_id": opponent_id, "matched_from": "queue"}
    
    # Fallback to offline players with PvP enabled
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM characters WHERE pvp_enabled = 1 AND id != ? ORDER BY RANDOM() LIMIT 1",
        (character_id,)
    )
    opponent = cursor.fetchone()
    conn.close()
    
    if opponent:
        return {"success": True, "opponent_id": opponent['id'], "matched_from": "offline"}
    
    raise HTTPException(status_code=404, detail="No opponents available")

# Ability endpoints
@app.get("/api/abilities/list")
async def list_abilities(character_id: str):
    """Get abilities for character's equipped weapon"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT equipment_json FROM characters WHERE id = ?", (character_id,))
    char = cursor.fetchone()
    
    if not char:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    equipment = json.loads(char['equipment_json'])
    weapon_type = get_weapon_type(equipment)
    
    abilities = get_abilities_for_weapon(weapon_type)
    
    # Get current loadout
    cursor.execute(
        "SELECT ability_id, slot_position FROM character_abilities WHERE character_id = ? ORDER BY slot_position",
        (character_id,)
    )
    loadout_rows = cursor.fetchall()
    
    loadout = {}
    for row in loadout_rows:
        loadout[row['slot_position']] = row['ability_id']
    
    conn.close()
    
    return {"success": True, "abilities": abilities, "loadout": loadout}

@app.post("/api/abilities/loadout")
async def set_ability_loadout(request: Dict = Body(...)):
    """Set ability loadout (hotkey assignments)"""
    character_id = request.get('character_id')
    loadout = request.get('loadout', {})  # {slot_position: ability_id}
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clear existing loadout
    cursor.execute("DELETE FROM character_abilities WHERE character_id = ?", (character_id,))
    
    # Set new loadout
    for slot_pos, ability_id in loadout.items():
        if ability_id:  # Only insert if ability is assigned
            cursor.execute(
                "INSERT INTO character_abilities (character_id, ability_id, slot_position) VALUES (?, ?, ?)",
                (character_id, ability_id, int(slot_pos))
            )
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Loadout updated"}

# Store endpoints
@app.get("/api/store/list")
async def list_store_items(character_id: str):
    """Get available store items for character level"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT level FROM characters WHERE id = ?", (character_id,))
    char = cursor.fetchone()
    
    if not char:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    char_level = char['level']
    
    cursor.execute(
        "SELECT * FROM store_items WHERE level_requirement <= ? ORDER BY level_requirement, slot",
        (char_level,)
    )
    items = cursor.fetchall()
    
    conn.close()
    
    items_list = []
    for item in items:
        # Calculate price with level scaling
        price = int(item['base_price'] * (1 + char_level * 0.1))
        items_list.append({
            'id': item['id'],
            'name': item['name'],
            'slot': item['slot'],
            'weapon_type': item['weapon_type'],
            'price': price,
            'level_requirement': item['level_requirement']
        })
    
    return {"success": True, "items": items_list}

@app.post("/api/store/buy")
async def buy_store_item(request: Dict = Body(...)):
    """Purchase item from store"""
    character_id = request.get('character_id')
    item_id = request.get('item_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get character
    cursor.execute("SELECT level, gold, inventory_json FROM characters WHERE id = ?", (character_id,))
    char = cursor.fetchone()
    
    if not char:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Get store item
    cursor.execute("SELECT * FROM store_items WHERE id = ?", (item_id,))
    store_item = cursor.fetchone()
    
    if not store_item:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check level requirement
    if char['level'] < store_item['level_requirement']:
        conn.close()
        raise HTTPException(status_code=400, detail="Level requirement not met")
    
    # Calculate price
    price = int(store_item['base_price'] * (1 + char['level'] * 0.1))
    
    # Check gold
    if char['gold'] < price:
        conn.close()
        raise HTTPException(status_code=400, detail="Not enough gold")
    
    # Check inventory limit (100 items)
    inventory = json.loads(char['inventory_json'])
    if len(inventory) >= 100:
        conn.close()
        raise HTTPException(status_code=400, detail="Inventory full (100 item limit)")
    
    # Generate item with random stats (1-3 stat points)
    num_stats = random.randint(1, 3)
    stats = {}
    for _ in range(num_stats):
        stat = random.choice(PRIMARY_STATS)
        stats[stat] = stats.get(stat, 0) + random.randint(1, 3)
    
    # Create equipment item
    equipment = {
        'id': f"eq_{random.randint(100000, 999999)}",
        'name': store_item['name'],
        'slot': store_item['slot'],
        'rarity': 'common',
        'level': char['level'],
        'weapon_type': store_item['weapon_type'],
        'stats': stats
    }
    
    # Add to inventory and deduct gold
    inventory.append(equipment)
    new_gold = char['gold'] - price
    
    cursor.execute(
        "UPDATE characters SET inventory_json = ?, gold = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (json.dumps(inventory), new_gold, character_id)
    )
    
    conn.commit()
    conn.close()
    
    return {"success": True, "equipment": equipment, "gold_remaining": new_gold}

@app.post("/api/store/sell")
async def sell_item(request: Dict = Body(...)):
    """Sell item from inventory"""
    character_id = request.get('character_id')
    item_id = request.get('item_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get character
    cursor.execute("SELECT gold, inventory_json FROM characters WHERE id = ?", (character_id,))
    char = cursor.fetchone()
    
    if not char:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    inventory = json.loads(char['inventory_json'])
    
    # Find item in inventory
    item = None
    item_index = None
    for i, inv_item in enumerate(inventory):
        if inv_item.get('id') == item_id:
            item = inv_item
            item_index = i
            break
    
    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found in inventory")
    
    # Calculate sell price
    rarity_multipliers = {
        'common': 1, 'uncommon': 2, 'rare': 3,
        'epic': 5, 'legendary': 10, 'mythic': 20
    }
    rarity_mult = rarity_multipliers.get(item.get('rarity', 'common'), 1)
    sell_price = (item.get('level', 1) * 5) + (rarity_mult * 10)
    
    # Remove item and add gold
    inventory.pop(item_index)
    new_gold = char['gold'] + sell_price
    
    cursor.execute(
        "UPDATE characters SET inventory_json = ?, gold = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (json.dumps(inventory), new_gold, character_id)
    )
    
    conn.commit()
    conn.close()
    
    return {"success": True, "gold_gained": sell_price, "gold_remaining": new_gold}

@app.post("/api/store/forge")
async def forge_item(request: Dict = Body(...)):
    """Forge random item (gold sink)"""
    character_id = request.get('character_id')
    rarity = request.get('rarity', 'common')
    
    if rarity not in RARITIES:
        raise HTTPException(status_code=400, detail="Invalid rarity")
    
    forge_costs = {
        'uncommon': 2000, 'rare': 5000
    }
    cost = forge_costs.get(rarity)
    if cost is None:
        raise HTTPException(status_code=400, detail="Invalid rarity for forging")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get character
    cursor.execute("SELECT level, gold, inventory_json FROM characters WHERE id = ?", (character_id,))
    char = cursor.fetchone()
    
    if not char:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Check gold
    if char['gold'] < cost:
        conn.close()
        raise HTTPException(status_code=400, detail="Not enough gold")
    
    # Check inventory limit
    inventory = json.loads(char['inventory_json'])
    if len(inventory) >= 100:
        conn.close()
        raise HTTPException(status_code=400, detail="Inventory full (100 item limit)")
    
    # Generate random item of specified rarity
    slot = random.choice(EQUIPMENT_SLOTS)
    equipment = generate_equipment(slot, rarity, char['level'])
    
    # Add to inventory and deduct gold
    inventory.append(equipment)
    new_gold = char['gold'] - cost
    
    cursor.execute(
        "UPDATE characters SET inventory_json = ?, gold = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (json.dumps(inventory), new_gold, character_id)
    )
    
    conn.commit()
    conn.close()
    
    return {"success": True, "equipment": equipment, "gold_remaining": new_gold, "cost": cost}

@app.post("/api/store/combine")
async def combine_items(request: Dict = Body(...)):
    """Combine items of same rarity to create higher rarity item"""
    character_id = request.get('character_id')
    item_ids = request.get('item_ids', [])  # List of item IDs to combine
    
    if not item_ids or len(item_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 items to combine")
    
    # Requirements: 2 Common → 1 Uncommon, 3 Uncommon → 1 Rare, 4 Rare → 1 Epic, 5 Epic → 1 Legendary, 6 Legendary → 1 Mythic
    combine_requirements = {
        'common': (2, 'uncommon'),
        'uncommon': (3, 'rare'),
        'rare': (4, 'epic'),
        'epic': (5, 'legendary'),
        'legendary': (6, 'mythic')
    }
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get character
    cursor.execute("SELECT level, inventory_json FROM characters WHERE id = ?", (character_id,))
    char = cursor.fetchone()
    
    if not char:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    inventory = json.loads(char['inventory_json'])
    
    # Find items and verify they're all the same rarity
    items_to_combine = []
    target_rarity = None
    
    for item_id in item_ids:
        found = False
        for i, inv_item in enumerate(inventory):
            if inv_item.get('id') == item_id:
                item_rarity = inv_item.get('rarity', 'common')
                if target_rarity is None:
                    target_rarity = item_rarity
                elif item_rarity != target_rarity:
                    conn.close()
                    raise HTTPException(status_code=400, detail="All items must be the same rarity")
                items_to_combine.append((i, inv_item))
                found = True
                break
        if not found:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Item {item_id} not found in inventory")
    
    # Check requirements
    if target_rarity not in combine_requirements:
        conn.close()
        raise HTTPException(status_code=400, detail="Cannot combine items of this rarity")
    
        required_count, result_rarity = combine_requirements[target_rarity]
        if len(items_to_combine) < required_count:
            conn.close()
            raise HTTPException(status_code=400, detail=f"Need {required_count} {target_rarity} items to create {result_rarity}")
    
    # Check inventory limit (if combining would exceed limit)
    if len(inventory) - len(items_to_combine) + 1 >= 100:
        conn.close()
        raise HTTPException(status_code=400, detail="Inventory would be full after combining")
    
    # Remove items (in reverse order to maintain indices)
    items_to_combine.sort(reverse=True, key=lambda x: x[0])
    for index, _ in items_to_combine:
        inventory.pop(index)
    
    # Create combined item
    slot = random.choice(EQUIPMENT_SLOTS)
    equipment = generate_equipment(slot, result_rarity, char['level'])
    inventory.append(equipment)
    
    cursor.execute(
        "UPDATE characters SET inventory_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (json.dumps(inventory), character_id)
    )
    
    conn.commit()
    conn.close()
    
    return {"success": True, "equipment": equipment, "rarity_created": result_rarity}

# Chat endpoints
@app.post("/api/chat/send")
async def send_chat_message(request: Dict = Body(...)):
    """Send a chat message"""
    character_id = request.get('character_id')
    message = request.get('message', '')
    
    if not character_id:
        raise HTTPException(status_code=400, detail="character_id required")
    
    if not message or len(message.strip()) == 0:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    if len(message) > 500:
        raise HTTPException(status_code=400, detail="Message too long (max 500 characters)")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM characters WHERE id = ?", (character_id,))
    character = cursor.fetchone()
    
    if not character:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    cursor.execute(
        "INSERT INTO chat_messages (character_id, character_name, message) VALUES (?, ?, ?)",
        (character_id, character['name'], message.strip())
    )
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Message sent"}

@app.get("/api/chat/get")
async def get_chat_messages(limit: int = 50):
    """Get recent chat messages"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT character_name, message, created_at 
           FROM chat_messages 
           ORDER BY created_at DESC 
           LIMIT ?""",
        (limit,)
    )
    
    messages = []
    for row in cursor.fetchall():
        messages.append({
            "character_name": row['character_name'],
            "message": row['message'],
            "timestamp": row['created_at']
        })
    
    conn.close()
    
    return {"success": True, "messages": list(reversed(messages))}  # Oldest first

# PVP Matchmaking endpoints
@app.post("/api/pvp/join-queue")
async def join_pvp_queue(request: Dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Join the PVP matchmaking queue"""
    user_id = current_user["user_id"]
    character_id = request.get('character_id')
    
    # Verify character belongs to user
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM characters WHERE id = ? AND user_id = ?", (character_id, user_id))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="Character not found or access denied")
    conn.close()
    
    if not character_id:
        raise HTTPException(status_code=400, detail="character_id required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify character exists and enable PVP
    cursor.execute("SELECT id, level FROM characters WHERE id = ?", (character_id,))
    character = cursor.fetchone()
    
    if not character:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Enable PVP for character
    cursor.execute(
        "UPDATE characters SET pvp_enabled = 1 WHERE id = ?",
        (character_id,)
    )
    
    # Add to queue
    pvp_queue[character_id] = datetime.now().timestamp()
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Joined PVP queue"}

@app.post("/api/pvp/leave-queue")
async def leave_pvp_queue(request: Dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Leave the PVP matchmaking queue"""
    user_id = current_user["user_id"]
    character_id = request.get('character_id')
    
    # Verify character belongs to user
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM characters WHERE id = ? AND user_id = ?", (character_id, user_id))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="Character not found or access denied")
    conn.close()
    
    if not character_id:
        raise HTTPException(status_code=400, detail="character_id required")
    
    delete_pvp_queue_entry(character_id)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE characters SET pvp_enabled = 0 WHERE id = ?",
        (character_id,)
    )
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Left PVP queue"}

@app.get("/api/pvp/opponents")
async def get_pvp_opponents(character_id: str, max_level_diff: int = 5, current_user: dict = Depends(get_current_user)):
    """Get list of available PVP opponents within level range"""
    user_id = current_user["user_id"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get character level and verify ownership
    cursor.execute("SELECT level FROM characters WHERE id = ? AND user_id = ?", (character_id, user_id))
    char = cursor.fetchone()
    
    if not char:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    char_level = char['level']
    
    # Find opponents within level range who have PVP enabled
    min_level = max(1, char_level - max_level_diff)
    max_level = min(100, char_level + max_level_diff)
    
    cursor.execute("""
        SELECT id, name, level, exp, pvp_enabled
        FROM characters
        WHERE id != ? 
        AND level BETWEEN ? AND ?
        AND pvp_enabled = 1
        ORDER BY ABS(level - ?) ASC, name ASC
        LIMIT 20
    """, (character_id, min_level, max_level, char_level))
    
    opponents = []
    for row in cursor.fetchall():
        opponents.append({
            'id': row['id'],
            'name': row['name'],
            'level': row['level'],
            'level_diff': abs(row['level'] - char_level)
        })
    
    conn.close()
    
    return {"success": True, "opponents": opponents}

@app.get("/api/pvp/leaderboard")
async def get_pvp_leaderboard(limit: int = 50):
    """Get PVP leaderboard (top players by level, exp, or wins)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get top players by level and exp (as a simple ranking)
    cursor.execute("""
        SELECT id, name, level, exp, gold
        FROM characters
        WHERE pvp_enabled = 1
        ORDER BY level DESC, exp DESC
        LIMIT ?
    """, (limit,))
    
    leaderboard = []
    rank = 1
    for row in cursor.fetchall():
        leaderboard.append({
            'rank': rank,
            'id': row['id'],
            'name': row['name'],
            'level': row['level'],
            'exp': row['exp'],
            'gold': row.get('gold', 0)
        })
        rank += 1
    
    conn.close()
    
    return {"success": True, "leaderboard": leaderboard}

@app.get("/api/pvp/queue-status")
async def get_pvp_queue_status(character_id: str):
    """Get PVP queue status and estimated wait time"""
    if not character_id:
        raise HTTPException(status_code=400, detail="character_id required")
    
    in_queue = character_id in pvp_queue
    
    queue = get_all_pvp_queue()
    queue_size = len(queue)
    
    # Estimate wait time (rough calculation)
    estimated_wait_seconds = queue_size * 30  # Rough estimate: 30 seconds per player ahead
    
    return {
        "success": True,
        "in_queue": in_queue,
        "queue_size": queue_size,
        "estimated_wait_seconds": estimated_wait_seconds if in_queue else 0
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    try:
        # Test database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Test Redis connection
    r = get_redis_client()
    redis_status = "connected" if r else "not_configured"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "redis": redis_status,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "version": "2.0.0"
    }

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()
    # Initialize Redis connection
    get_redis_client()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

