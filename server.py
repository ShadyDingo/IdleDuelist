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
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
from fastapi import FastAPI, HTTPException, Depends, Body, Header, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import JWTError, jwt
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.exceptions import RequestValidationError

from app.core.cache import redis_cache
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.state import game_state
from app.db import db_manager, execute_query, get_db_connection, get_db_cursor
from app.db.bootstrap import ensure_player_tracking_tables
from app.services.player_tracking import player_tracking_service
from app.services.state_service import (
    delete_auto_fight_session,
    delete_combat_state,
    delete_pvp_queue_entry,
    get_all_auto_fight_sessions,
    get_all_pvp_queue,
    get_auto_fight_session,
    get_combat_state,
    get_pvp_queue_entry,
    set_auto_fight_session,
    set_combat_state,
    set_pvp_queue_entry,
)

# Import error handlers
try:
    from error_handlers import (
        create_error_response,
        validation_exception_handler,
        rate_limit_handler,
        general_exception_handler
    )
except ImportError:
    # Fallback if error_handlers not available
    def create_error_response(message, status_code=500, error_type="error", details=None):
        return JSONResponse(status_code=status_code, content={"success": False, "error": message})
    validation_exception_handler = None
    rate_limit_handler = _rate_limit_exceeded_handler
    general_exception_handler = None

# Import game logic
from game_logic import (
    calculate_combat_stats, generate_equipment, roll_equipment_rarity,
    calculate_damage, check_hit, calculate_exp_gain, process_level_up,
    get_equipment_stats, get_weapon_type, get_weapon_attack_speed,
    get_weapon_damage_type, get_abilities_for_weapon, get_ability_by_id,
    PRIMARY_STATS, EQUIPMENT_SLOTS, WEAPON_TYPES, RARITIES
)

app = FastAPI(title="IdleDuelist", version="2.0.0")

# Configure logging
logger = configure_logging(settings)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address, default_limits=["1000/hour"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
if validation_exception_handler:
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
if general_exception_handler:
    app.add_exception_handler(Exception, general_exception_handler)

# Determine environment / CORS
IS_PRODUCTION = settings.is_production
cors_origins = settings.cors_origin_list

if IS_PRODUCTION:
    cors_raw = (settings.cors_origins or "").strip()
    if not cors_raw or cors_raw == "*" or not cors_origins:
        raise ValueError(
            "CORS_ORIGINS must be explicitly set in production environment. "
            "Set CORS_ORIGINS to a comma-separated list of allowed origins."
        )
else:
    cors_origins = cors_origins or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Database / cache configuration
DATABASE_URL = settings.database_url
USE_POSTGRES = db_manager.use_postgres
REDIS_URL = settings.redis_url


def get_redis_client():
    """Return shared Redis client if available."""
    return redis_cache.get_client()

def init_database():
    """Initialize database with all tables - compatible with both SQLite and PostgreSQL"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
    except Exception as e:
        logger.critical(r"Cannot initialize database: {e}")
        if USE_POSTGRES:
            print("⚠ PostgreSQL connection failed. Validate your managed PostgreSQL service (Fly Postgres or similar).")
        raise
    
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
    
    # Characters table - PostgreSQL uses different boolean defaults
    if USE_POSTGRES:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS characters (
                id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                name VARCHAR(255) UNIQUE NOT NULL,
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                skill_points INTEGER DEFAULT 3,
                stats_json TEXT NOT NULL,
                equipment_json TEXT NOT NULL,
                inventory_json TEXT NOT NULL,
                auto_combat BOOLEAN DEFAULT FALSE,
                gold INTEGER DEFAULT 0,
                pvp_enabled BOOLEAN DEFAULT FALSE,
                combat_stance VARCHAR(50) DEFAULT 'balanced',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
    else:
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
    
    # Commit initial table creation so subsequent ALTER statements see the tables
    if USE_POSTGRES:
        conn.commit()
    
    # Add gold and pvp_enabled columns if they don't exist (for existing databases)
    # For PostgreSQL, we need to handle transaction rollbacks on errors
    def table_exists(table_name: str) -> bool:
        """Check if a table exists in the current database"""
        try:
            if USE_POSTGRES:
                cursor.execute("SELECT to_regclass(%s)", (f'public.{table_name}',))
                result = cursor.fetchone()
                return result is not None and result[0] is not None
            else:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                return cursor.fetchone() is not None
        except Exception:
            if USE_POSTGRES:
                try:
                    conn.rollback()
                except:
                    pass
            return False
    
    def column_exists(table_name: str, column_name: str) -> bool:
        """Check if a column exists in the table"""
        try:
            if USE_POSTGRES:
                cursor.execute(
                    """
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = %s AND column_name = %s
                    """,
                    (table_name, column_name),
                )
                return cursor.fetchone() is not None
            else:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                return any(col[1] == column_name for col in columns)
        except Exception:
            if USE_POSTGRES:
                try:
                    conn.rollback()
                except:
                    pass
            return False
    
    def safe_alter_table(alter_sql):
        """Safely execute ALTER TABLE, handling duplicate column errors"""
        try:
            cursor.execute(alter_sql)
            if USE_POSTGRES:
                conn.commit()  # Commit after each successful ALTER
        except Exception as e:
            # For PostgreSQL, rollback on any error to clear failed transaction state
            if USE_POSTGRES:
                try:
                    conn.rollback()
                except:
                    pass  # Ignore rollback errors
            # Column already exists or other error - ignore
            pass
    
    if table_exists('characters'):
        safe_alter_table('ALTER TABLE characters ADD COLUMN gold INTEGER DEFAULT 0')
        
        if USE_POSTGRES:
            safe_alter_table('ALTER TABLE characters ADD COLUMN pvp_enabled BOOLEAN DEFAULT FALSE')
        else:
            safe_alter_table('ALTER TABLE characters ADD COLUMN pvp_enabled BOOLEAN DEFAULT 0')
        
        if USE_POSTGRES:
            safe_alter_table("ALTER TABLE characters ADD COLUMN combat_stance VARCHAR(50) DEFAULT 'balanced'")
        else:
            safe_alter_table('ALTER TABLE characters ADD COLUMN combat_stance TEXT DEFAULT "balanced"')
        
        # Add PvP stats columns if they don't exist
        safe_alter_table('ALTER TABLE characters ADD COLUMN pvp_wins INTEGER DEFAULT 0')
        safe_alter_table('ALTER TABLE characters ADD COLUMN pvp_losses INTEGER DEFAULT 0')
        safe_alter_table('ALTER TABLE characters ADD COLUMN pvp_mmr INTEGER DEFAULT 1000')
        safe_alter_table('ALTER TABLE characters ADD COLUMN pvp_last_week_rank INTEGER')
        
        if USE_POSTGRES:
            safe_alter_table('ALTER TABLE characters ADD COLUMN pvp_weekly_rewards_claimed BOOLEAN DEFAULT FALSE')
        else:
            safe_alter_table('ALTER TABLE characters ADD COLUMN pvp_weekly_rewards_claimed BOOLEAN DEFAULT 0')
    
    # Combat logs table
    if USE_POSTGRES:
        # Check if table exists first to avoid sequence conflicts
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'combat_logs'
            )
        """)
        result = cursor.fetchone()
        if USE_POSTGRES:
            # PostgreSQL RealDictCursor returns a dict with column name as key
            table_exists = result['exists'] if result and isinstance(result, dict) else (result[0] if result else False)
        else:
            # SQLite returns a tuple
            table_exists = result[0] if result else False
        
        if not table_exists:
            try:
                cursor.execute('''
                    CREATE TABLE combat_logs (
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
                conn.commit()
            except Exception as e:
                # If sequence conflict, table might be partially created - check again
                if "already exists" in str(e) or "duplicate key" in str(e):
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'combat_logs'
                        )
                    """)
                    result = cursor.fetchone()
                    if USE_POSTGRES:
                        table_exists = result['exists'] if result and isinstance(result, dict) else (result[0] if result else False)
                    else:
                        table_exists = result[0] if result else False
                    if not table_exists:
                        # Table doesn't exist, but sequence does - drop sequence and retry
                        try:
                            cursor.execute("DROP SEQUENCE IF EXISTS combat_logs_id_seq CASCADE")
                            cursor.execute('''
                                CREATE TABLE combat_logs (
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
                            conn.commit()
                        except Exception as e2:
                            logger.warning(r"Could not create combat_logs table: {e2}")
                            conn.rollback()
                else:
                    raise
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
    
    # Abilities table - PostgreSQL uses VARCHAR for consistency
    if USE_POSTGRES:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS abilities (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                cooldown_seconds INTEGER NOT NULL,
                damage_multiplier REAL NOT NULL,
                damage_type VARCHAR(50) NOT NULL,
                mana_cost INTEGER NOT NULL,
                weapon_type VARCHAR(50) NOT NULL,
                is_ultimate BOOLEAN DEFAULT FALSE
            )
        ''')
        # Commit after table creation to ensure it's visible
        conn.commit()
    else:
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
    if USE_POSTGRES:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pve_enemies (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                level INTEGER NOT NULL,
                stats_json TEXT NOT NULL,
                description TEXT,
                story_order INTEGER NOT NULL,
                unlocked_at_level INTEGER DEFAULT 1,
                gold_min INTEGER DEFAULT 1,
                gold_max INTEGER DEFAULT 1,
                drop_chance REAL DEFAULT 0.0,
                exp_reward INTEGER DEFAULT 50
            )
        ''')
        conn.commit()
    else:
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
                drop_chance REAL DEFAULT 0.0,
                exp_reward INTEGER DEFAULT 50
            )
        ''')
    
    if table_exists('pve_enemies'):
        if not column_exists('pve_enemies', 'description'):
            safe_alter_table('ALTER TABLE pve_enemies ADD COLUMN description TEXT')
        if not column_exists('pve_enemies', 'gold_min'):
            safe_alter_table('ALTER TABLE pve_enemies ADD COLUMN gold_min INTEGER DEFAULT 1')
        if not column_exists('pve_enemies', 'gold_max'):
            safe_alter_table('ALTER TABLE pve_enemies ADD COLUMN gold_max INTEGER DEFAULT 1')
        if not column_exists('pve_enemies', 'drop_chance'):
            safe_alter_table('ALTER TABLE pve_enemies ADD COLUMN drop_chance REAL DEFAULT 0.0')
        if not column_exists('pve_enemies', 'exp_reward'):
            safe_alter_table('ALTER TABLE pve_enemies ADD COLUMN exp_reward INTEGER DEFAULT 50')
    
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
    if USE_POSTGRES:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS store_items (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                slot VARCHAR(50) NOT NULL,
                weapon_type VARCHAR(50),
                base_price INTEGER NOT NULL,
                level_requirement INTEGER DEFAULT 1
            )
        ''')
        conn.commit()
    else:
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
    
    # Feedback table
    if USE_POSTGRES:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                character_name VARCHAR(255),
                content TEXT NOT NULL,
                upvotes INTEGER DEFAULT 0,
                downvotes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback_votes (
                id VARCHAR(255) PRIMARY KEY,
                feedback_id VARCHAR(255) NOT NULL,
                user_id VARCHAR(255) NOT NULL,
                vote_type VARCHAR(10) NOT NULL CHECK (vote_type IN ('upvote', 'downvote')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (feedback_id) REFERENCES feedback (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(feedback_id, user_id)
            )
        ''')
        conn.commit()
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                character_name TEXT,
                content TEXT NOT NULL,
                upvotes INTEGER DEFAULT 0,
                downvotes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback_votes (
                id TEXT PRIMARY KEY,
                feedback_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                vote_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (feedback_id) REFERENCES feedback (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(feedback_id, user_id)
            )
        ''')
    
    ensure_player_tracking_tables(conn, cursor, USE_POSTGRES)
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")
    
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
            if USE_POSTGRES:
                cursor.execute('''
                    INSERT INTO abilities 
                    (id, name, description, cooldown_seconds, damage_multiplier, damage_type, mana_cost, weapon_type, is_ultimate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                ''', (
                    ability['id'], ability['name'], ability['description'],
                    ability['cooldown_seconds'], ability['damage_multiplier'],
                    ability['damage_type'], ability['mana_cost'], weapon_type,
                    ability['is_ultimate']
                ))
            else:
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
    # Only clear if we need to update - check if enemies exist first
    cursor.execute("SELECT COUNT(*) as count FROM pve_enemies")
    enemy_count = cursor.fetchone()['count'] if USE_POSTGRES else cursor.fetchone()[0]
    # Only delete if we have enemies (means we're updating, not initializing)
    if enemy_count > 0:
        cursor.execute("DELETE FROM pve_enemies")
    
    # Balanced PvE enemies - roughly 2.5-3x level in total stats for appropriate challenge
    # Enemies should be beatable by similarly-leveled players with decent equipment
    # EXP reward formula: 50 + (level * 5) - fixed per enemy type
    pve_enemies_data = [
        {'id': 'chicken', 'name': 'Chicken', 'level': 1, 'stats': {'might': 1, 'agility': 2, 'vitality': 1, 'intellect': 0, 'wisdom': 0, 'charisma': 0}, 'description': 'Harmless barn birds that peck at ankles. More annoying than dangerous.', 'gold_min': 1, 'gold_max': 1, 'drop_chance': 0.0, 'exp_reward': 50},
        {'id': 'forest_rat', 'name': 'Forest Rat', 'level': 3, 'stats': {'might': 2, 'agility': 6, 'vitality': 3, 'intellect': 1, 'wisdom': 0, 'charisma': 0}, 'description': 'Oversized rodents twisted by wild magic. Quick and skittish.', 'gold_min': 1, 'gold_max': 2, 'drop_chance': 0.0, 'exp_reward': 65},
        {'id': 'goblin_scout', 'name': 'Goblin Scout', 'level': 5, 'stats': {'might': 4, 'agility': 9, 'vitality': 4, 'intellect': 1, 'wisdom': 1, 'charisma': 0}, 'description': 'Sneaky ambushers who dart from shadow to shadow.', 'gold_min': 1, 'gold_max': 3, 'drop_chance': 0.1, 'exp_reward': 75},
        {'id': 'cave_slime', 'name': 'Cave Slime', 'level': 8, 'stats': {'might': 3, 'agility': 2, 'vitality': 16, 'intellect': 2, 'wisdom': 3, 'charisma': 0}, 'description': 'Gelatinous blobs that digest anything organic.', 'gold_min': 2, 'gold_max': 4, 'drop_chance': 0.2, 'exp_reward': 90},
        {'id': 'ork_grunt', 'name': 'Ork Grunt', 'level': 10, 'stats': {'might': 18, 'agility': 4, 'vitality': 12, 'intellect': 1, 'wisdom': 0, 'charisma': 0}, 'description': 'Brutish frontline fighters serving stronger warlords.', 'gold_min': 2, 'gold_max': 5, 'drop_chance': 0.5, 'exp_reward': 100},
        {'id': 'bandit_cutpurse', 'name': 'Bandit Cutpurse', 'level': 12, 'stats': {'might': 8, 'agility': 22, 'vitality': 6, 'intellect': 2, 'wisdom': 2, 'charisma': 0}, 'description': 'High-speed thieves who rely on mobility to survive.', 'gold_min': 4, 'gold_max': 7, 'drop_chance': 0.5, 'exp_reward': 110},
        {'id': 'skeleton_warrior', 'name': 'Skeleton Warrior', 'level': 15, 'stats': {'might': 18, 'agility': 3, 'vitality': 25, 'intellect': 0, 'wisdom': 4, 'charisma': 0}, 'description': 'Reanimated bones that act on forgotten commands.', 'gold_min': 6, 'gold_max': 10, 'drop_chance': 0.7, 'exp_reward': 125},
        {'id': 'gnoll_raider', 'name': 'Gnoll Raider', 'level': 18, 'stats': {'might': 26, 'agility': 16, 'vitality': 16, 'intellect': 0, 'wisdom': 2, 'charisma': 0}, 'description': 'Savage hyena-folk who overwhelm caravans in packs.', 'gold_min': 8, 'gold_max': 12, 'drop_chance': 0.8, 'exp_reward': 140},
        {'id': 'cave_spider', 'name': 'Cave Spider', 'level': 20, 'stats': {'might': 7, 'agility': 30, 'vitality': 14, 'intellect': 13, 'wisdom': 4, 'charisma': 0}, 'description': 'Venomous hunters whose webs block entire tunnels.', 'gold_min': 10, 'gold_max': 15, 'drop_chance': 1.0, 'exp_reward': 150},
        {'id': 'bog_zombie', 'name': 'Bog Zombie', 'level': 23, 'stats': {'might': 16, 'agility': 1, 'vitality': 50, 'intellect': 4, 'wisdom': 5, 'charisma': 0}, 'description': 'Rotting corpses preserved by swamp sorcery.', 'gold_min': 12, 'gold_max': 18, 'drop_chance': 1.0, 'exp_reward': 165},
        {'id': 'lizardfolk_scout', 'name': 'Lizardfolk Scout', 'level': 26, 'stats': {'might': 22, 'agility': 33, 'vitality': 22, 'intellect': 5, 'wisdom': 4, 'charisma': 0}, 'description': 'Cold-blooded hunters defending marsh territory.', 'gold_min': 14, 'gold_max': 22, 'drop_chance': 1.2, 'exp_reward': 180},
        {'id': 'dire_wolf', 'name': 'Dire Wolf', 'level': 30, 'stats': {'might': 33, 'agility': 43, 'vitality': 20, 'intellect': 0, 'wisdom': 0, 'charisma': 0}, 'description': 'Moon-touched predators leading lesser wolf packs.', 'gold_min': 18, 'gold_max': 28, 'drop_chance': 1.5, 'exp_reward': 200},
        {'id': 'ogre_brute', 'name': 'Ogre Brute', 'level': 33, 'stats': {'might': 62, 'agility': 6, 'vitality': 37, 'intellect': 0, 'wisdom': 0, 'charisma': 0}, 'description': 'Massive simple monsters who smash everything.', 'gold_min': 22, 'gold_max': 32, 'drop_chance': 1.7, 'exp_reward': 215},
        {'id': 'wraithling', 'name': 'Wraithling', 'level': 36, 'stats': {'might': 6, 'agility': 24, 'vitality': 6, 'intellect': 35, 'wisdom': 46, 'charisma': 0}, 'description': 'Flickering spirits wandering ruins in search of warmth.', 'gold_min': 24, 'gold_max': 35, 'drop_chance': 1.8, 'exp_reward': 230},
        {'id': 'lizardfolk_shaman', 'name': 'Lizardfolk Shaman', 'level': 40, 'stats': {'might': 7, 'agility': 7, 'vitality': 20, 'intellect': 39, 'wisdom': 56, 'charisma': 0}, 'description': 'Mystics who summon storms and serpents.', 'gold_min': 28, 'gold_max': 40, 'drop_chance': 2.0, 'exp_reward': 250},
        {'id': 'stone_golem', 'name': 'Stone Golem', 'level': 44, 'stats': {'might': 28, 'agility': 1, 'vitality': 95, 'intellect': 0, 'wisdom': 16, 'charisma': 0}, 'description': 'Ancient guardians carved from enchanted rock.', 'gold_min': 40, 'gold_max': 60, 'drop_chance': 2.5, 'exp_reward': 270},
        {'id': 'frost_troll', 'name': 'Frost Troll', 'level': 48, 'stats': {'might': 45, 'agility': 8, 'vitality': 82, 'intellect': 0, 'wisdom': 15, 'charisma': 0}, 'description': 'Regenerating monsters of the frozen wastes.', 'gold_min': 45, 'gold_max': 70, 'drop_chance': 2.7, 'exp_reward': 290},
        {'id': 'vampire_thrall', 'name': 'Vampire Thrall', 'level': 52, 'stats': {'might': 33, 'agility': 65, 'vitality': 18, 'intellect': 41, 'wisdom': 0, 'charisma': 9}, 'description': 'Graceful undead servants with life-draining strikes.', 'gold_min': 50, 'gold_max': 80, 'drop_chance': 3.0, 'exp_reward': 310},
        {'id': 'flame_elemental', 'name': 'Flame Elemental', 'level': 56, 'stats': {'might': 1, 'agility': 27, 'vitality': 19, 'intellect': 79, 'wisdom': 52, 'charisma': 0}, 'description': 'Living firestorms born from volcanic vents.', 'gold_min': 55, 'gold_max': 90, 'drop_chance': 3.2, 'exp_reward': 330},
        {'id': 'arcane_sentinel', 'name': 'Arcane Sentinel', 'level': 60, 'stats': {'might': 10, 'agility': 1, 'vitality': 20, 'intellect': 93, 'wisdom': 65, 'charisma': 0}, 'description': 'Hovering constructs guarding forgotten libraries.', 'gold_min': 60, 'gold_max': 100, 'drop_chance': 3.5, 'exp_reward': 350},
        {'id': 'corrupted_druid', 'name': 'Corrupted Druid', 'level': 65, 'stats': {'might': 11, 'agility': 11, 'vitality': 31, 'intellect': 51, 'wisdom': 100, 'charisma': 0}, 'description': 'Once-kind wardens now twisted by blight magic.', 'gold_min': 70, 'gold_max': 120, 'drop_chance': 4.0, 'exp_reward': 375},
        {'id': 'blighted_treant', 'name': 'Blighted Treant', 'level': 70, 'stats': {'might': 23, 'agility': 1, 'vitality': 162, 'intellect': 1, 'wisdom': 33, 'charisma': 0}, 'description': 'Infected forest guardians dripping toxic sap.', 'gold_min': 80, 'gold_max': 130, 'drop_chance': 4.5, 'exp_reward': 400},
        {'id': 'aether_warden', 'name': 'Aether Warden', 'level': 74, 'stats': {'might': 1, 'agility': 24, 'vitality': 24, 'intellect': 81, 'wisdom': 103, 'charisma': 0}, 'description': 'Riftwalkers who bend space around them.', 'gold_min': 90, 'gold_max': 150, 'drop_chance': 5.0, 'exp_reward': 420},
        {'id': 'lich_adept', 'name': 'Lich Adept', 'level': 78, 'stats': {'might': 1, 'agility': 1, 'vitality': 25, 'intellect': 132, 'wisdom': 85, 'charisma': 0}, 'description': 'Apprentice necromancers wielding soul-draining magic.', 'gold_min': 100, 'gold_max': 160, 'drop_chance': 5.5, 'exp_reward': 440},
        {'id': 'wyvern_stalker', 'name': 'Wyvern Stalker', 'level': 82, 'stats': {'might': 77, 'agility': 114, 'vitality': 51, 'intellect': 13, 'wisdom': 1, 'charisma': 0}, 'description': 'Silent aerial hunters with venomous tails.', 'gold_min': 120, 'gold_max': 180, 'drop_chance': 6.0, 'exp_reward': 460},
        {'id': 'void_wraith', 'name': 'Void Wraith', 'level': 86, 'stats': {'might': 1, 'agility': 41, 'vitality': 15, 'intellect': 80, 'wisdom': 132, 'charisma': 0}, 'description': 'Entities from a lightless dimension whispering madness.', 'gold_min': 130, 'gold_max': 200, 'drop_chance': 7.0, 'exp_reward': 480},
        {'id': 'titan_construct', 'name': 'Titan Construct', 'level': 90, 'stats': {'might': 84, 'agility': 1, 'vitality': 167, 'intellect': 28, 'wisdom': 1, 'charisma': 0}, 'description': 'Colossal machines built by civilizations long gone.', 'gold_min': 150, 'gold_max': 230, 'drop_chance': 8.0, 'exp_reward': 500},
        {'id': 'demon_knight', 'name': 'Demon Knight', 'level': 94, 'stats': {'might': 145, 'agility': 30, 'vitality': 88, 'intellect': 1, 'wisdom': 30, 'charisma': 0}, 'description': 'Elite hellwarriors clad in cursed armor.', 'gold_min': 170, 'gold_max': 260, 'drop_chance': 9.0, 'exp_reward': 520},
        {'id': 'ancient_dragon', 'name': 'Ancient Dragon', 'level': 98, 'stats': {'might': 91, 'agility': 46, 'vitality': 91, 'intellect': 46, 'wisdom': 32, 'charisma': 0}, 'description': 'World-shaping titans whose breath shifts landscapes.', 'gold_min': 200, 'gold_max': 300, 'drop_chance': 10.0, 'exp_reward': 540},
        {'id': 'demon_lord_regent', 'name': 'Demon Lord Regent', 'level': 100, 'stats': {'might': 63, 'agility': 32, 'vitality': 47, 'intellect': 93, 'wisdom': 78, 'charisma': 0}, 'description': 'Infernal rulers capable of warping reality itself.', 'gold_min': 250, 'gold_max': 350, 'drop_chance': 12.0, 'exp_reward': 550}
    ]
    
    for i, enemy in enumerate(pve_enemies_data):
        if USE_POSTGRES:
            # PostgreSQL uses ON CONFLICT
            cursor.execute('''
                INSERT INTO pve_enemies 
                (id, name, level, stats_json, description, story_order, unlocked_at_level, gold_min, gold_max, drop_chance, exp_reward)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    level = EXCLUDED.level,
                    stats_json = EXCLUDED.stats_json,
                    description = EXCLUDED.description,
                    story_order = EXCLUDED.story_order,
                    unlocked_at_level = EXCLUDED.unlocked_at_level,
                    gold_min = EXCLUDED.gold_min,
                    gold_max = EXCLUDED.gold_max,
                    drop_chance = EXCLUDED.drop_chance,
                    exp_reward = EXCLUDED.exp_reward
            ''', (
                enemy['id'], enemy['name'], enemy['level'],
                json.dumps(enemy['stats']), enemy['description'],
                i + 1, enemy['level'],  # story_order and unlocked_at_level
                enemy['gold_min'], enemy['gold_max'], enemy['drop_chance'], enemy.get('exp_reward', 50)
            ))
        else:
            # SQLite uses INSERT OR REPLACE
            cursor.execute('''
                INSERT OR REPLACE INTO pve_enemies 
                (id, name, level, stats_json, description, story_order, unlocked_at_level, gold_min, gold_max, drop_chance, exp_reward)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                enemy['id'], enemy['name'], enemy['level'],
                json.dumps(enemy['stats']), enemy['description'],
                i + 1, enemy['level'],  # story_order and unlocked_at_level
                enemy['gold_min'], enemy['gold_max'], enemy['drop_chance'], enemy.get('exp_reward', 50)
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
            'base_price': 50,
            'level_requirement': 1
        })
    
    for item in store_items:
        if USE_POSTGRES:
            cursor.execute('''
                INSERT INTO store_items 
                (id, name, slot, weapon_type, base_price, level_requirement)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            ''', (
                item['id'], item['name'], item['slot'],
                item['weapon_type'], item['base_price'], item['level_requirement']
            ))
        else:
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
    logger.info("Default data initialized")

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-min-32-chars")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = 24
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Validate JWT_SECRET_KEY in production (warn but don't crash)
if IS_PRODUCTION:
    if not JWT_SECRET_KEY or JWT_SECRET_KEY == "your-secret-key-change-in-production-min-32-chars" or len(JWT_SECRET_KEY) < 32:
        logger.warning("JWT_SECRET_KEY is not set or is insecure in production! Authentication may be compromised.")
        logger.warning("Please set JWT_SECRET_KEY environment variable to a secure random string (minimum 32 characters)")
        # Don't raise - allow server to start but log the warning

# Security scheme for FastAPI
security = HTTPBearer(auto_error=False)

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
    
    # Track active session for online player count
    user_id = data.get("sub") or data.get("user_id")
    if user_id:
        game_state.touch_session(user_id)
    
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

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    """Dependency to get current authenticated user from JWT token"""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payload = verify_token(token, "access")
    
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Update active session timestamp for online player count
    user_id = payload.get("sub")
    if user_id:
        game_state.touch_session(user_id)
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

# Import Pydantic models from models.py if available, otherwise use simple definitions
try:
    from models import (
        RegisterRequest,
        LoginRequest,
        CreateCharacterRequest,
        StartCombatRequest,
        CombatActionRequest,
        EquipmentUpgradeRequest,
        EquipmentRerollRequest,
        AllocateSkillsRequest,
        CreateFeedbackRequest,
        BuyStoreItemRequest,
        SellItemRequest,
        UpdateStanceRequest
    )
except ImportError:
    # Fallback to simple models if models.py not available
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
    
    # Placeholder models for other endpoints
    StartCombatRequest = None
    CombatActionRequest = None
    EquipmentUpgradeRequest = None
    EquipmentRerollRequest = None
    AllocateSkillsRequest = None
    CreateFeedbackRequest = None
    BuyStoreItemRequest = None
    SellItemRequest = None
    UpdateStanceRequest = None

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
@limiter.limit("5/minute")
async def register(register_data: RegisterRequest, request: Request):
    """Register a new user"""
    conn = None
    try:
        # Validate input
        if not register_data.username or not register_data.password:
            raise HTTPException(status_code=400, detail="Username and password are required")
        
        if len(register_data.username) < 3:
            raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
        
        if len(register_data.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username exists
        if USE_POSTGRES:
            cursor.execute("SELECT id FROM users WHERE username = %s", (register_data.username,))
        else:
            cursor.execute("SELECT id FROM users WHERE username = ?", (register_data.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Create user
        try:
            user_id = generate_id()
            password_hash = hash_password(register_data.password)
        except Exception as e:
            logger.error(f"Error generating user ID or hashing password: {e}")
            raise HTTPException(status_code=500, detail="Failed to create user account")
        
        # Insert user into database
        try:
            if USE_POSTGRES:
                cursor.execute(
                    "INSERT INTO users (id, username, password_hash, email) VALUES (%s, %s, %s, %s)",
                    (user_id, register_data.username, password_hash, register_data.email)
                )
            else:
                cursor.execute(
                    "INSERT INTO users (id, username, password_hash, email) VALUES (?, ?, ?, ?)",
                    (user_id, register_data.username, password_hash, register_data.email)
                )
            conn.commit()
            player_tracking_service.ensure_profile(user_id, register_data.username, register_data.email)
        except Exception as e:
            logger.error(f"Database error during registration: {e}")
            if USE_POSTGRES:
                conn.rollback()
            raise HTTPException(status_code=500, detail="Failed to create user account. Please try again.")
        
        return {"success": True, "user_id": user_id, "message": "Account created successfully"}
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 400, 500)
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred during registration. Please try again.")
    finally:
        # Ensure database connection is closed
        if conn:
            try:
                conn.close()
            except:
                pass

@app.post("/api/login")
@limiter.limit("10/minute")
async def login(login_data: LoginRequest, request: Request):
    """Login and return JWT tokens and user data"""
    conn = None
    try:
        # Validate input
        if not login_data.username or not login_data.password:
            raise HTTPException(status_code=400, detail="Username and password are required")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query user
        if USE_POSTGRES:
            cursor.execute(
                "SELECT id, username, password_hash FROM users WHERE username = %s",
                (login_data.username,)
            )
        else:
            cursor.execute(
                "SELECT id, username, password_hash FROM users WHERE username = ?",
                (login_data.username,)
            )
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Verify password
        try:
            if not verify_password(login_data.password, user['password_hash']):
                raise HTTPException(status_code=401, detail="Invalid username or password")
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Get user's character
        if USE_POSTGRES:
            cursor.execute(
                "SELECT * FROM characters WHERE user_id = %s LIMIT 1",
                (user['id'],)
            )
        else:
            cursor.execute(
                "SELECT * FROM characters WHERE user_id = ? LIMIT 1",
                (user['id'],)
            )
        character = cursor.fetchone()
        
        # Create JWT tokens
        try:
            access_token = create_access_token(data={"sub": user['id'], "username": user['username']})
            refresh_token = create_refresh_token(data={"sub": user['id']})
        except Exception as e:
            logger.error(f"JWT token creation error: {e}")
            raise HTTPException(status_code=500, detail="Failed to create authentication tokens")
        
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

        try:
            ip_address = request.client.host if request and request.client else None
            player_tracking_service.record_login(user['id'], user['username'], ip_address)
        except Exception as tracking_error:
            logger.warning(f"Failed to record login analytics: {tracking_error}")
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 401, 400)
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred during login. Please try again.")
    finally:
        # Ensure database connection is closed
        if conn:
            try:
                conn.close()
            except:
                pass

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

def normalize_equipment_item(item: Dict, slot: str) -> Dict:
    """Ensure equipment items have required fields like weapon_type"""
    if not item:
        return item
    
    # If it's a weapon slot and missing weapon_type, try to infer from name
    if slot == 'main_hand' and 'weapon_type' not in item:
        item_name = item.get('name', '').lower()
        if 'bow' in item_name:
            item['weapon_type'] = 'bow'
        elif 'crossbow' in item_name:
            item['weapon_type'] = 'crossbow'
        elif 'mace' in item_name:
            item['weapon_type'] = 'mace'
        elif 'hammer' in item_name:
            item['weapon_type'] = 'hammer'
        elif 'axe' in item_name:
            item['weapon_type'] = 'axe'
        elif 'dagger' in item_name:
            item['weapon_type'] = 'dagger'
        elif 'wand' in item_name:
            item['weapon_type'] = 'wand'
        elif 'staff' in item_name:
            item['weapon_type'] = 'staff'
        elif 'sword' in item_name:
            item['weapon_type'] = 'sword'
        # If we can't infer, leave it as None - frontend will use default
    
    return item

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
    
    # Normalize equipment items to ensure they have weapon_type if missing
    for slot, item in equipment.items():
        if item:
            equipment[slot] = normalize_equipment_item(item, slot)
    
    # Normalize inventory items as well
    for item in inventory:
        if item and 'slot' in item:
            slot = item['slot']
            normalized = normalize_equipment_item(item, slot)
            # Update item in place
            for key, value in normalized.items():
                item[key] = value
    
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
    
    # Get PvP stats (handle missing columns gracefully)
    try:
        pvp_wins = character['pvp_wins'] if 'pvp_wins' in character.keys() and character['pvp_wins'] is not None else 0
    except (KeyError, AttributeError):
        pvp_wins = 0
    
    try:
        pvp_losses = character['pvp_losses'] if 'pvp_losses' in character.keys() and character['pvp_losses'] is not None else 0
    except (KeyError, AttributeError):
        pvp_losses = 0
    
    try:
        pvp_mmr = character['pvp_mmr'] if 'pvp_mmr' in character.keys() and character['pvp_mmr'] is not None else 1000
    except (KeyError, AttributeError):
        pvp_mmr = 1000
    
    # Calculate win rate
    total_games = pvp_wins + pvp_losses
    pvp_win_rate = (pvp_wins / total_games * 100) if total_games > 0 else 0.0
    
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
            "combat_stance": combat_stance,
            "pvp_wins": pvp_wins,
            "pvp_losses": pvp_losses,
            "pvp_mmr": pvp_mmr,
            "pvp_win_rate": round(pvp_win_rate, 2)
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
    try:
        user_id = current_user["user_id"]
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM characters WHERE id = ? AND user_id = ?", (character_id, user_id))
        character = cursor.fetchone()
        
        if not character:
            conn.close()
            raise HTTPException(status_code=404, detail="Character not found")
        
        current_stats = json.loads(character['stats_json'])
        # SQLite Row objects use dictionary-style access
        available_points = character['skill_points'] if character['skill_points'] is not None else 0
        
        # Ensure all stats are present in request
        for stat in PRIMARY_STATS:
            if stat not in request.stats:
                request.stats[stat] = current_stats.get(stat, 10)
        
        # Calculate total points being allocated
        total_new_points = sum(request.stats.values())
        total_current_points = sum(current_stats.values())
        base_points = len(PRIMARY_STATS) * 10  # Starting 10 in each
        
        points_used = total_current_points - base_points
        new_points_used = total_new_points - base_points
        
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
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in allocate_skills endpoint: {e}")
        print(traceback.format_exc())
        if 'conn' in locals():
            conn.close()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/character/respec")
async def reset_skill_points(request: Dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Reset all allocated skill points (respec) - refunds all skill points for reallocation"""
    user_id = current_user["user_id"]
    character_id = request.get('character_id')
    
    if not character_id:
        raise HTTPException(status_code=400, detail="character_id required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify character belongs to user
    cursor.execute("SELECT level, gold, stats_json, skill_points FROM characters WHERE id = ? AND user_id = ?", (character_id, user_id))
    char = cursor.fetchone()
    
    if not char:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    char_level = char['level']
    current_gold = char['gold'] if char['gold'] is not None else 0
    
    # Calculate cost: 5000 + (character_level * 200)
    cost = 5000 + (char_level * 200)
    
    if current_gold < cost:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Not enough gold. Required: {cost}, Have: {current_gold}")
    
    # Reset stats to base values (10 in each stat)
    base_stats = {stat: 10 for stat in PRIMARY_STATS}
    
    # Calculate refunded skill points: 3 per level (starting with 3 at level 1)
    # Level 1: 3 points, Level 2: 6 points, Level 3: 9 points, etc.
    refunded_skill_points = 3 + (char_level - 1) * 3
    
    # Deduct gold
    new_gold = current_gold - cost
    
    # Update character
    if USE_POSTGRES:
        cursor.execute(
            "UPDATE characters SET stats_json = %s, skill_points = %s, gold = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (json.dumps(base_stats), refunded_skill_points, new_gold, character_id)
        )
    else:
        cursor.execute(
            "UPDATE characters SET stats_json = ?, skill_points = ?, gold = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (json.dumps(base_stats), refunded_skill_points, new_gold, character_id)
        )
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": "Skill points reset successfully",
        "refunded_skill_points": refunded_skill_points,
        "gold_spent": cost,
        "gold_remaining": new_gold
    }

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
    rarity = roll_equipment_rarity(is_pvp, enemy_level=1, player_level=level)
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

@app.post("/api/equipment/upgrade")
async def upgrade_equipment(request: Dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Upgrade an equipment item's level (increases stats)"""
    user_id = current_user["user_id"]
    character_id = request.get('character_id')
    item_id = request.get('item_id')
    
    if not character_id or not item_id:
        raise HTTPException(status_code=400, detail="character_id and item_id required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify character belongs to user
    cursor.execute("SELECT level, gold, equipment_json, inventory_json FROM characters WHERE id = ? AND user_id = ?", (character_id, user_id))
    char = cursor.fetchone()
    
    if not char:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    char_level = char['level']
    current_gold = char['gold'] if char['gold'] is not None else 0
    equipment = json.loads(char['equipment_json'])
    inventory = json.loads(char['inventory_json'])
    
    # Find item in equipment or inventory
    item = None
    item_location = None
    item_index = None
    
    # Check equipped items
    for slot, eq_item in equipment.items():
        if eq_item and eq_item.get('id') == item_id:
            item = eq_item
            item_location = 'equipment'
            break
    
    # Check inventory
    if not item:
        for i, inv_item in enumerate(inventory):
            if inv_item.get('id') == item_id:
                item = inv_item
                item_location = 'inventory'
                item_index = i
                break
    
    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check if item can be upgraded (not already at character level)
    item_level = item.get('level', 1)
    if item_level >= char_level:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Item is already at maximum level ({char_level})")
    
    # Calculate cost: 500 * (item_level + 1)
    cost = 500 * (item_level + 1)
    
    if current_gold < cost:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Not enough gold. Required: {cost}, Have: {current_gold}")
    
    # Upgrade item level
    new_level = item_level + 1
    
    # Recalculate stats based on new level
    rarity = item.get('rarity', 'common')
    slot = item.get('slot')
    
    # Use the same logic as generate_equipment but preserve existing stat types
    from game_logic import RARITY_STAT_RANGES, PRIMARY_STATS
    ranges = RARITY_STAT_RANGES.get(rarity, RARITY_STAT_RANGES['common'])
    
    # Level scaling factor (1.0 at level 1, 2.0 at level 100)
    level_scale = 1.0 + ((new_level - 1) / 99.0)
    
    # Get existing stat keys to preserve stat types
    existing_stats = item.get('stats', {})
    existing_stat_keys = list(existing_stats.keys())
    
    # Recalculate stats with new level, preserving which stats the item has
    new_stats = {}
    stat_index = 0
    
    # Primary stat
    if ranges['primary'][1] > 0 and stat_index < len(existing_stat_keys):
        stat_name = existing_stat_keys[stat_index] if stat_index < len(existing_stat_keys) else random.choice(PRIMARY_STATS)
        base_value = random.randint(ranges['primary'][0], ranges['primary'][1])
        new_stats[stat_name] = int(base_value * level_scale)
        stat_index += 1
    
    # Secondary stat
    if ranges['secondary'][1] > 0 and stat_index < len(existing_stat_keys):
        stat_name = existing_stat_keys[stat_index] if stat_index < len(existing_stat_keys) else random.choice([s for s in PRIMARY_STATS if s not in new_stats])
        base_value = random.randint(ranges['secondary'][0], ranges['secondary'][1])
        new_stats[stat_name] = int(base_value * level_scale)
        stat_index += 1
    
    # Tertiary stat
    if ranges['tertiary'][1] > 0 and stat_index < len(existing_stat_keys):
        stat_name = existing_stat_keys[stat_index] if stat_index < len(existing_stat_keys) else random.choice([s for s in PRIMARY_STATS if s not in new_stats])
        base_value = random.randint(ranges['tertiary'][0], ranges['tertiary'][1])
        new_stats[stat_name] = int(base_value * level_scale)
        stat_index += 1
    
    # Quaternary stat (mythic only)
    if ranges['quaternary'][1] > 0 and stat_index < len(existing_stat_keys):
        stat_name = existing_stat_keys[stat_index] if stat_index < len(existing_stat_keys) else random.choice([s for s in PRIMARY_STATS if s not in new_stats])
        base_value = random.randint(ranges['quaternary'][0], ranges['quaternary'][1])
        new_stats[stat_name] = int(base_value * level_scale)
    
    # Update item
    item['level'] = new_level
    item['stats'] = new_stats
    
    # Update in appropriate location
    if item_location == 'equipment':
        for slot_key, eq_item in equipment.items():
            if eq_item and eq_item.get('id') == item_id:
                equipment[slot_key] = item
                break
    else:
        inventory[item_index] = item
    
    # Deduct gold and save
    new_gold = current_gold - cost
    
    if USE_POSTGRES:
        cursor.execute(
            "UPDATE characters SET equipment_json = %s, inventory_json = %s, gold = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (json.dumps(equipment), json.dumps(inventory), new_gold, character_id)
        )
    else:
        cursor.execute(
            "UPDATE characters SET equipment_json = ?, inventory_json = ?, gold = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (json.dumps(equipment), json.dumps(inventory), new_gold, character_id)
        )
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": f"Item upgraded to level {new_level}",
        "item": item,
        "gold_spent": cost,
        "gold_remaining": new_gold
    }

@app.post("/api/equipment/reroll")
async def reroll_equipment_stats(request: Dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Re-roll all stats on an equipment item (keep rarity, slot, level)"""
    user_id = current_user["user_id"]
    character_id = request.get('character_id')
    item_id = request.get('item_id')
    
    if not character_id or not item_id:
        raise HTTPException(status_code=400, detail="character_id and item_id required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify character belongs to user
    cursor.execute("SELECT gold, equipment_json, inventory_json FROM characters WHERE id = ? AND user_id = ?", (character_id, user_id))
    char = cursor.fetchone()
    
    if not char:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    current_gold = char['gold'] if char['gold'] is not None else 0
    equipment = json.loads(char['equipment_json'])
    inventory = json.loads(char['inventory_json'])
    
    # Find item in equipment or inventory
    item = None
    item_location = None
    item_index = None
    
    # Check equipped items
    for slot, eq_item in equipment.items():
        if eq_item and eq_item.get('id') == item_id:
            item = eq_item
            item_location = 'equipment'
            break
    
    # Check inventory
    if not item:
        for i, inv_item in enumerate(inventory):
            if inv_item.get('id') == item_id:
                item = inv_item
                item_location = 'inventory'
                item_index = i
                break
    
    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Calculate cost: 1000 * (1 + item_level * 0.1)
    item_level = item.get('level', 1)
    cost = int(1000 * (1 + item_level * 0.1))
    
    if current_gold < cost:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Not enough gold. Required: {cost}, Have: {current_gold}")
    
    # Re-roll stats (keep rarity, slot, level)
    rarity = item.get('rarity', 'common')
    slot = item.get('slot')
    
    from game_logic import RARITY_STAT_RANGES, PRIMARY_STATS
    ranges = RARITY_STAT_RANGES.get(rarity, RARITY_STAT_RANGES['common'])
    
    # Level scaling factor (1.0 at level 1, 2.0 at level 100)
    level_scale = 1.0 + ((item_level - 1) / 99.0)
    
    # Generate new stats
    new_stats = {}
    
    # Primary stat
    if ranges['primary'][1] > 0:
        primary_stat = random.choice(PRIMARY_STATS)
        base_value = random.randint(ranges['primary'][0], ranges['primary'][1])
        new_stats[primary_stat] = int(base_value * level_scale)
    
    # Secondary stat
    if ranges['secondary'][1] > 0:
        available_stats = [s for s in PRIMARY_STATS if s not in new_stats]
        if available_stats:
            secondary_stat = random.choice(available_stats)
            base_value = random.randint(ranges['secondary'][0], ranges['secondary'][1])
            new_stats[secondary_stat] = int(base_value * level_scale)
    
    # Tertiary stat
    if ranges['tertiary'][1] > 0:
        available_stats = [s for s in PRIMARY_STATS if s not in new_stats]
        if available_stats:
            tertiary_stat = random.choice(available_stats)
            base_value = random.randint(ranges['tertiary'][0], ranges['tertiary'][1])
            new_stats[tertiary_stat] = int(base_value * level_scale)
    
    # Quaternary stat (mythic only)
    if ranges['quaternary'][1] > 0:
        available_stats = [s for s in PRIMARY_STATS if s not in new_stats]
        if available_stats:
            quaternary_stat = random.choice(available_stats)
            base_value = random.randint(ranges['quaternary'][0], ranges['quaternary'][1])
            new_stats[quaternary_stat] = int(base_value * level_scale)
    
    # Update item stats
    item['stats'] = new_stats
    
    # Update in appropriate location
    if item_location == 'equipment':
        for slot_key, eq_item in equipment.items():
            if eq_item and eq_item.get('id') == item_id:
                equipment[slot_key] = item
                break
    else:
        inventory[item_index] = item
    
    # Deduct gold and save
    new_gold = current_gold - cost
    
    if USE_POSTGRES:
        cursor.execute(
            "UPDATE characters SET equipment_json = %s, inventory_json = %s, gold = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (json.dumps(equipment), json.dumps(inventory), new_gold, character_id)
        )
    else:
        cursor.execute(
            "UPDATE characters SET equipment_json = ?, inventory_json = ?, gold = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (json.dumps(equipment), json.dumps(inventory), new_gold, character_id)
        )
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": "Item stats re-rolled",
        "item": item,
        "gold_spent": cost,
        "gold_remaining": new_gold
    }

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
    char2_ability_loadout = {}  # Initialize for both cases
    if isinstance(character2_data, dict) and 'id' in character2_data:
        # AI or offline player
        char2_combat = character2_data.get('combat_stats', {})
        char2_name = character2_data.get('name', 'Enemy')
        char2_id = character2_data.get('id')
        char2_level = character2_data.get('level', 1)
        char2_equipment = character2_data.get('equipment', {})
        char2_weapon_type = get_weapon_type(char2_equipment)
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
        
        # For PvP, load opponent's ability loadout
        if is_pvp:
            cursor.execute("SELECT ability_id, slot_position FROM character_abilities WHERE character_id = ? ORDER BY slot_position", (char2_id,))
            char2_loadout_rows = cursor.fetchall()
            for row in char2_loadout_rows:
                char2_ability_loadout[row['slot_position']] = row['ability_id']
    
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
            'auto_ability_enabled': is_pvp,  # Enable abilities for PvP opponents (not ultimates)
            'ability_loadout': char2_ability_loadout if is_pvp else {},  # Load opponent's ability loadout in PvP
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
@limiter.limit("30/minute")
async def start_combat(request: Dict = Body(...), current_user: dict = Depends(get_current_user), req: Request = None):
    """Start a new combat encounter"""
    try:
        user_id = current_user["user_id"]
        character_id = request.get('character_id')
        
        if not character_id:
            raise HTTPException(status_code=400, detail="character_id required")
        
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
            enemy_combat = calculate_combat_stats(enemy_stats, enemy_equipment_stats, enemy_equipment)
            
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
    except HTTPException as e:
        # Re-raise HTTP exceptions as-is
        raise e
    except Exception as e:
        import traceback
        error_msg = f"Error starting combat: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        # Return JSON error instead of raising to ensure frontend gets proper response
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": error_msg}
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error starting combat: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/combat/state/{combat_id}")
async def get_combat_state_endpoint(combat_id: str):
    """Get current combat state (polling endpoint)"""
    try:
        state = get_combat_state(combat_id)
        if state is None:
            raise HTTPException(status_code=404, detail="Combat not found")
        
        # Process combat turns if active
        if state.get('is_active', False):
            process_combat_turns(combat_id)
            # Re-fetch state after processing (in case combat ended)
            state = get_combat_state(combat_id)
            if state is None:
                raise HTTPException(status_code=404, detail="Combat not found")
        
        # Get visual events and clear them (so frontend only gets new events)
        visual_events = state.get('visual_events', [])
        
        # Debug: log visual events being sent
        if visual_events:
            logger.debug(r"Sending {len(visual_events)} visual events for combat {combat_id}: {[e.get('type') for e in visual_events]}")
        
        response = {"success": True, "combat": state}
        # Always include visual_events array, even if empty
        response['visual_events'] = visual_events
        
        # Clear after sending (so frontend only gets new events)
        state['visual_events'] = []
        set_combat_state(combat_id, state)  # Save updated state
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in get_combat_state_endpoint: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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
        # State is saved inside end_combat, but ensure it's persisted
        final_state = get_combat_state(combat_id)
        if final_state:
            set_combat_state(combat_id, final_state)

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
    state = get_combat_state(combat_id)
    if state is None:
        return
    
    # Prevent multiple calls to end_combat for the same combat
    if not state.get('is_active', True):
        logger.info(f"[COMBAT] Combat {combat_id} already ended, skipping end_combat")
        return
    
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
    # Award rewards to the winner, regardless of whether it's player1 or player2
    # Calculate rewards
    if not state['is_pvp']:
        # PvE - get enemy data and use fixed exp_reward
        enemy_id = state['character2_id']
        enemy_conn = None
        try:
            enemy_conn = get_db_connection()
            cursor = enemy_conn.cursor()
            cursor.execute("SELECT gold_min, gold_max, drop_chance, level, exp_reward FROM pve_enemies WHERE id = ?", (enemy_id,))
            enemy_data = cursor.fetchone()
            
            if enemy_data:
                # SQLite Row objects don't support .get(), use bracket notation instead
                exp_gain = enemy_data['exp_reward'] if enemy_data['exp_reward'] is not None else 50  # Use fixed EXP reward from enemy
                exp_gain = max(1, exp_gain)  # Ensure never negative
                gold_gain = random.randint(enemy_data['gold_min'], enemy_data['gold_max'])
                drop_chance = enemy_data['drop_chance']
                enemy_level = enemy_data['level']
            else:
                exp_gain = 50  # Default fallback
                gold_gain = random.randint(1, 5)
                drop_chance = 0.0
                enemy_level = loser_level
        except Exception as e:
            import traceback
            logger.error(f"Failed to fetch enemy data for {enemy_id}: {e}")
            print(traceback.format_exc())
            # Use defaults if enemy data fetch fails
            exp_gain = 50
            gold_gain = random.randint(1, 5)
            drop_chance = 0.0
            enemy_level = loser_level
        finally:
            if enemy_conn:
                try:
                    enemy_conn.close()
                except:
                    pass
    else:
        # PvP - use variable EXP based on level difference
        exp_gain = calculate_exp_gain(winner_level, loser_level, True)
        exp_gain = max(1, exp_gain)  # Ensure never negative
        gold_gain = 100 + loser_level * 10
        drop_chance = 0.7  # 70% for PvP
        enemy_level = loser_level
    
    # Store rewards in combat state (for auto-fight extraction or display)
    rewards = {
        'exp_gained': exp_gain,
        'gold_gained': gold_gain,
        'equipment_dropped': False  # Will be calculated if not auto-fight
    }
    
    # For auto-fight, just store rewards in state (will be applied later)
    if is_auto_fight:
        state['rewards'] = rewards
    else:
        # Only update database if not auto-fight
        rewards_applied = False
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Update character
            cursor.execute("SELECT user_id, name, exp, level, gold, skill_points FROM characters WHERE id = ?", (winner_id,))
            char_data = cursor.fetchone()
            if not char_data:
                logger.error(f"Character {winner_id} not found when trying to award rewards")
                rewards['applied'] = False
                rewards['error'] = f"Character {winner_id} not found"
                state['rewards'] = rewards
                if conn:
                    conn.close()
                # Don't return early - save state with error flag
                set_combat_state(combat_id, state)
                return
            
            # Handle None values (SQLite returns None for missing/null values)
            owner_user_id = char_data['user_id']
            current_exp = char_data['exp'] if char_data['exp'] is not None else 0
            current_gold = char_data['gold'] if char_data['gold'] is not None else 0
            current_skill_points = char_data['skill_points'] if char_data['skill_points'] is not None else 0
            
            new_exp = current_exp + exp_gain
            new_level = char_data['level']
            new_gold = current_gold + gold_gain
            
            logger.info(f"[COMBAT] Awarding rewards to {winner_id}: EXP {current_exp} + {exp_gain} = {new_exp}, Gold {current_gold} + {gold_gain} = {new_gold}")
            
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

            try:
                player_tracking_service.record_progress(
                    character_id=winner_id,
                    user_id=owner_user_id,
                    level=char_dict['level'],
                    exp_gain=exp_gain,
                    gold_gain=gold_gain,
                    metadata={
                        "combat_id": combat_id,
                        "is_pvp": state.get('is_pvp', False),
                        "opponent_id": state.get('opponent_id'),
                    },
                )
            except Exception as tracking_error:
                logger.warning(f"Failed to record progress for {winner_id}: {tracking_error}")
            
            # Drop equipment based on drop chance
            equipment_dropped = False
            if random.random() * 100 < drop_chance:
                rarity = roll_equipment_rarity(state['is_pvp'], enemy_level, char_dict['level'])
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
            
            rewards['equipment_dropped'] = equipment_dropped
            
            # Update PvP stats if this is a PvP match
            if state['is_pvp'] and not is_auto_fight:
                try:
                    # Check if PvP columns exist first
                    existing_columns = set()
                    if USE_POSTGRES:
                        cursor.execute("""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = 'characters' AND column_name IN ('pvp_wins', 'pvp_losses', 'pvp_mmr')
                        """)
                        existing_columns = {row['column_name'] for row in cursor.fetchall()}
                        has_pvp_columns = len(existing_columns) == 3
                    else:
                        cursor.execute("PRAGMA table_info(characters)")
                        columns = [col[1] for col in cursor.fetchall()]
                        existing_columns = set(columns)
                        has_pvp_columns = all(col in columns for col in ['pvp_wins', 'pvp_losses', 'pvp_mmr'])
                    
                    if not has_pvp_columns:
                        print("[WARNING] PvP columns missing, attempting to add them...")
                        # Try to add missing columns
                        if USE_POSTGRES:
                            if 'pvp_wins' not in existing_columns:
                                cursor.execute('ALTER TABLE characters ADD COLUMN pvp_wins INTEGER DEFAULT 0')
                                conn.commit()
                            if 'pvp_losses' not in existing_columns:
                                cursor.execute('ALTER TABLE characters ADD COLUMN pvp_losses INTEGER DEFAULT 0')
                                conn.commit()
                            if 'pvp_mmr' not in existing_columns:
                                cursor.execute('ALTER TABLE characters ADD COLUMN pvp_mmr INTEGER DEFAULT 1000')
                                conn.commit()
                        else:
                            # For SQLite, try to add columns with error handling
                            for col_sql in [
                                'ALTER TABLE characters ADD COLUMN pvp_wins INTEGER DEFAULT 0',
                                'ALTER TABLE characters ADD COLUMN pvp_losses INTEGER DEFAULT 0',
                                'ALTER TABLE characters ADD COLUMN pvp_mmr INTEGER DEFAULT 1000'
                            ]:
                                try:
                                    cursor.execute(col_sql)
                                    conn.commit()
                                except Exception:
                                    pass  # Column already exists
                    
                    # Get current PvP stats for both players
                    cursor.execute("SELECT user_id, pvp_wins, pvp_losses, pvp_mmr FROM characters WHERE id = ?", (winner_id,))
                    winner_stats = cursor.fetchone()
                    cursor.execute("SELECT user_id, pvp_wins, pvp_losses, pvp_mmr FROM characters WHERE id = ?", (loser_id,))
                    loser_stats = cursor.fetchone()
                    
                    # Get MMR values (default to 1000 if not set)
                    # SQLite Row objects use dictionary-style access, not .get()
                    winner_mmr = winner_stats['pvp_mmr'] if winner_stats and winner_stats['pvp_mmr'] is not None else 1000
                    loser_mmr = loser_stats['pvp_mmr'] if loser_stats and loser_stats['pvp_mmr'] is not None else 1000
                    
                    # Calculate MMR change using ELO system
                    K = 32  # K-factor for competitive games
                    expected_winner = 1 / (1 + 10 ** ((loser_mmr - winner_mmr) / 400))
                    expected_loser = 1 / (1 + 10 ** ((winner_mmr - loser_mmr) / 400))
                    
                    # Winner gets 1 point, loser gets 0
                    winner_mmr_change = int(K * (1 - expected_winner))
                    loser_mmr_change = int(K * (0 - expected_loser))
                    
                    new_winner_mmr = max(0, winner_mmr + winner_mmr_change)
                    new_loser_mmr = max(0, loser_mmr + loser_mmr_change)
                    
                    # Update winner stats
                    # SQLite Row objects use dictionary-style access, not .get()
                    winner_wins = (winner_stats['pvp_wins'] if winner_stats and winner_stats['pvp_wins'] is not None else 0) + 1
                    cursor.execute(
                        "UPDATE characters SET pvp_wins = ?, pvp_mmr = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (winner_wins, new_winner_mmr, winner_id)
                    )
                    
                    # Update loser stats
                    loser_losses = (loser_stats['pvp_losses'] if loser_stats and loser_stats['pvp_losses'] is not None else 0) + 1
                    cursor.execute(
                        "UPDATE characters SET pvp_losses = ?, pvp_mmr = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (loser_losses, new_loser_mmr, loser_id)
                    )

                    if winner_stats and loser_stats:
                        try:
                            player_tracking_service.record_pvp_result(
                                winner_character_id=winner_id,
                                loser_character_id=loser_id,
                                winner_user_id=winner_stats['user_id'],
                                loser_user_id=loser_stats['user_id'],
                                winner_mmr_before=winner_mmr,
                                winner_mmr_after=new_winner_mmr,
                                loser_mmr_before=loser_mmr,
                                loser_mmr_after=new_loser_mmr,
                                metadata={"combat_id": combat_id},
                            )
                        except Exception as tracking_error:
                            logger.warning(f"Failed to persist PvP match analytics: {tracking_error}")
                except Exception as pvp_error:
                    import traceback
                    error_msg = f"Failed to update PvP stats: {pvp_error}"
                    logger.error(f"{error_msg}")
                    print(traceback.format_exc())
                    # Don't fail the entire reward process if PvP stats fail
                    # The EXP and gold should still be awarded
                    # Mark in rewards that PvP stats update failed
                    if 'rewards' in locals():
                        rewards['pvp_stats_error'] = str(pvp_error)
            
            conn.commit()
            
            # Verify the update was actually saved by reading it back
            cursor.execute("SELECT exp, level, gold FROM characters WHERE id = ?", (winner_id,))
            verify_data = cursor.fetchone()
            if verify_data:
                logger.info(f"[COMBAT] Successfully updated character {winner_id}: EXP {verify_data['exp']}, Level {verify_data['level']}, Gold {verify_data['gold']}")
                logger.info(f"[COMBAT] Expected: EXP {char_dict['exp']}, Level {char_dict['level']}, Gold {new_gold}")
                if verify_data['exp'] != char_dict['exp'] or verify_data['gold'] != new_gold:
                    logger.error(f"Database update verification failed! Expected EXP {char_dict['exp']}, got {verify_data['exp']}")
            else:
                logger.error(f"Could not verify database update - character not found after commit!")
            
            # Mark rewards as successfully applied and store in state
            rewards['applied'] = True
            state['rewards'] = rewards
            rewards_applied = True
        except Exception as e:
            import traceback
            error_msg = f"Failed to award combat rewards: {e}"
            logger.error(f"{error_msg}")
            print(traceback.format_exc())
            # Store rewards with error flag so frontend can show error
            rewards['applied'] = False
            rewards['error'] = str(e)
            state['rewards'] = rewards
            rewards_applied = False
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
                try:
                    conn.close()
                except:
                    pass
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    # Always save the state after updating (even if rewards failed to apply)
    try:
        set_combat_state(combat_id, state)
    except Exception as e:
        import traceback
        logger.error(f"Failed to save combat state: {e}")
        print(traceback.format_exc())

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
    
    if not is_pvp and isinstance(character2_id_or_data, dict) and 'id' in character2_id_or_data:
        # PvE - get enemy's fixed exp_reward
        enemy_id = character2_id_or_data.get('id')
        cursor.execute("SELECT exp_reward FROM pve_enemies WHERE id = ?", (enemy_id,))
        enemy_exp = cursor.fetchone()
        # SQLite Row objects don't support .get(), use bracket notation instead
        exp_gain = enemy_exp['exp_reward'] if enemy_exp and enemy_exp['exp_reward'] is not None else 50
        exp_gain = max(1, exp_gain)  # Ensure never negative
    else:
        # PvP - use variable EXP
        exp_gain = calculate_exp_gain(winner_level, loser_level, True)
        exp_gain = max(1, exp_gain)  # Ensure never negative
    
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
            rarity = roll_equipment_rarity(is_pvp, enemy_level=loser_level, player_level=char_dict['level'])
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
        if USE_POSTGRES:
            cursor.execute(
                "INSERT INTO character_pve_progress (character_id, enemies_unlocked_json) VALUES (%s, %s) ON CONFLICT (character_id) DO NOTHING",
                (character_id, json.dumps(unlocked_enemies))
            )
        else:
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
async def start_auto_fight(request: Dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Start an hour-long auto-fight session against a PvE enemy"""
    try:
        user_id = current_user["user_id"]
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
            for session_id, session in list(get_all_auto_fight_sessions().items()):
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
        
        # Verify character belongs to user
        cursor.execute("SELECT * FROM characters WHERE id = ? AND user_id = ?", (character_id, user_id))
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
        # Use simpler format without prefix to avoid FastAPI route matching issues
        session_id = f"{random.randint(100000, 999999)}{int(datetime.now().timestamp())}"
        
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
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error starting auto-fight: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/pve/auto-fight/{session_id}")
async def get_auto_fight_status(session_id: str):
    """Get status of auto-fight session"""
    logger.info(f"[AUTO-FIGHT] GET request for session_id: {session_id}")
    session = get_auto_fight_session(session_id)
    if session is None:
        logger.info(f"[AUTO-FIGHT] Session {session_id} not found")
        raise HTTPException(status_code=404, detail="Session not found")
    logger.info(f"[AUTO-FIGHT] Session {session_id} found, is_active: {session.get('is_active', False)}")
    
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

@app.post("/api/pve/auto-fight/extend")
async def extend_auto_fight(request: Dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Extend an active auto-fight session by adding hours"""
    user_id = current_user["user_id"]
    session_id = request.get('session_id')
    hours = request.get('hours', 1)  # 1, 2, or 4 hours
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    if hours not in [1, 2, 4]:
        raise HTTPException(status_code=400, detail="hours must be 1, 2, or 4")
    
    # Get session
    session = get_auto_fight_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session['is_active']:
        raise HTTPException(status_code=400, detail="Session is not active")
    
    # Verify character belongs to user
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT gold FROM characters WHERE id = ? AND user_id = ?", (session['character_id'], user_id))
    char = cursor.fetchone()
    
    if not char:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    current_gold = char['gold'] if char['gold'] is not None else 0
    
    # Calculate cost (flat pricing, no level scaling)
    costs = {
        1: 2000,
        2: 3500,
        4: 6000
    }
    cost = costs[hours]
    
    if current_gold < cost:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Not enough gold. Required: {cost}, Have: {current_gold}")
    
    # Add time to session
    seconds_to_add = hours * 3600
    session['end_time'] += seconds_to_add
    
    # Update session
    set_auto_fight_session(session_id, session)
    
    # Deduct gold
    new_gold = current_gold - cost
    
    if USE_POSTGRES:
        cursor.execute(
            "UPDATE characters SET gold = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (new_gold, session['character_id'])
        )
    else:
        cursor.execute(
            "UPDATE characters SET gold = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_gold, session['character_id'])
        )
    
    conn.commit()
    conn.close()
    
    # Calculate new time remaining
    current_time = datetime.now().timestamp()
    time_remaining = max(0, session['end_time'] - current_time)
    
    return {
        "success": True,
        "message": f"Auto-fight extended by {hours} hour(s)",
        "hours_added": hours,
        "time_remaining": int(time_remaining),
        "gold_spent": cost,
        "gold_remaining": new_gold
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
            exp_gain = max(1, rewards.get('exp_gained', 0))  # Ensure never negative
            gold_gain = rewards.get('gold_gained', 0)
            equipment_dropped = rewards.get('equipment_dropped', False)
            
            # If equipment was dropped, generate it
            if equipment_dropped:
                rarity = roll_equipment_rarity(False, session['enemy_level'], session['player_level'])
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
        enemy_combat = calculate_combat_stats(enemy_stats, enemy_equipment_stats, enemy_equipment)
        
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
    cursor.execute("SELECT user_id, exp, level, gold, skill_points, inventory_json FROM characters WHERE id = ?", (session['character_id'],))
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
        
        try:
            player_tracking_service.record_progress(
                character_id=session['character_id'],
                user_id=char['user_id'],
                level=char_dict['level'],
                exp_gain=session['total_exp_gained'],
                gold_gain=session['total_gold_gained'],
                metadata={
                    "auto_session_id": session_id,
                    "enemy_id": session['enemy_id'],
                    "wins": session['wins'],
                },
            )
        except Exception as tracking_error:
            logger.warning(f"Failed to record auto-fight progress: {tracking_error}")
        
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
    logger.info(f"[AUTO-FIGHT] STOP request for session_id: {session_id}")
    session = get_auto_fight_session(session_id)
    if session is None:
        logger.info(f"[AUTO-FIGHT] Session {session_id} not found for stop")
        raise HTTPException(status_code=404, detail="Session not found")
    
    end_auto_fight_session(session_id)
    logger.info(f"[AUTO-FIGHT] Session {session_id} stopped successfully")
    
    return {"success": True, "message": "Auto-fight session stopped"}

# PvP endpoints
@app.post("/api/pvp/queue")
async def pvp_queue(request: Dict = Body(...)):
    """Join or leave PvP queue"""
    character_id = request.get('character_id')
    action = request.get('action', 'join')  # 'join' or 'leave'
    
    if action == 'join':
        set_pvp_queue_entry(character_id, datetime.now().isoformat())
        return {"success": True, "message": "Joined PvP queue"}
    elif action == 'leave':
        if get_pvp_queue_entry(character_id):
            delete_pvp_queue_entry(character_id)
        return {"success": True, "message": "Left PvP queue"}
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

@app.get("/api/pvp/available")
async def get_pvp_available():
    """Get list of offline players with PvP enabled"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("SELECT id, name, level FROM characters WHERE pvp_enabled = TRUE ORDER BY level DESC LIMIT 20")
    else:
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
    
    if USE_POSTGRES:
        cursor.execute(
            "UPDATE characters SET pvp_enabled = %s WHERE id = %s",
            (enabled, character_id)
        )
    else:
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
    queue_list = [cid for cid in get_all_pvp_queue().keys() if cid != character_id]
    if queue_list:
        opponent_id = queue_list[0]
        delete_pvp_queue_entry(opponent_id)
        if get_pvp_queue_entry(character_id):
            delete_pvp_queue_entry(character_id)
        return {"success": True, "opponent_id": opponent_id, "matched_from": "queue"}
    
    # Fallback to offline players with PvP enabled
    conn = get_db_connection()
    cursor = conn.cursor()
    if USE_POSTGRES:
        cursor.execute(
            "SELECT id FROM characters WHERE pvp_enabled = TRUE AND id != %s ORDER BY RANDOM() LIMIT 1",
            (character_id,)
        )
    else:
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
        # Use base price directly - prices remain constant regardless of level
        price = item['base_price']
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
    
    # Use base price directly - prices remain constant regardless of level
    price = store_item['base_price']
    
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
    
    # Add armor_type for armor slots (randomly choose between cloth, leather, metal)
    armor_slots = ['helmet', 'chest', 'legs', 'boots', 'gloves']
    if store_item['slot'] in armor_slots:
        equipment['armor_type'] = random.choice(['cloth', 'leather', 'metal'])
    
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
        'uncommon': 1000, 'rare': 3000
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

# Feedback endpoints
def ensure_feedback_tables_exist():
    """Ensure feedback tables exist, create them if they don't"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if feedback table exists
        table_exists = False
        if USE_POSTGRES:
            cursor.execute("""
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'feedback'
            """)
            table_exists = cursor.fetchone() is not None
        else:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='feedback'
            """)
            table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            print("[INFO] Feedback table missing, creating it...")
            if USE_POSTGRES:
                # Check if users table exists first
                cursor.execute("""
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'users'
                """)
                users_exists = cursor.fetchone() is not None
                
                if users_exists:
                    cursor.execute('''
                        CREATE TABLE feedback (
                            id VARCHAR(255) PRIMARY KEY,
                            user_id VARCHAR(255) NOT NULL,
                            character_name VARCHAR(255),
                            content TEXT NOT NULL,
                            upvotes INTEGER DEFAULT 0,
                            downvotes INTEGER DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users (id)
                        )
                    ''')
                else:
                    # Create without foreign key if users table doesn't exist
                    print("[WARNING] Users table not found, creating feedback table without foreign key")
                    cursor.execute('''
                        CREATE TABLE feedback (
                            id VARCHAR(255) PRIMARY KEY,
                            user_id VARCHAR(255) NOT NULL,
                            character_name VARCHAR(255),
                            content TEXT NOT NULL,
                            upvotes INTEGER DEFAULT 0,
                            downvotes INTEGER DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS feedback_votes (
                        id VARCHAR(255) PRIMARY KEY,
                        feedback_id VARCHAR(255) NOT NULL,
                        user_id VARCHAR(255) NOT NULL,
                        vote_type VARCHAR(10) NOT NULL CHECK (vote_type IN ('upvote', 'downvote')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (feedback_id) REFERENCES feedback (id) ON DELETE CASCADE,
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        UNIQUE(feedback_id, user_id)
                    )
                ''')
            else:
                # Check if users table exists for SQLite
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                users_exists = cursor.fetchone() is not None
                
                if users_exists:
                    cursor.execute('''
                        CREATE TABLE feedback (
                            id TEXT PRIMARY KEY,
                            user_id TEXT NOT NULL,
                            character_name TEXT,
                            content TEXT NOT NULL,
                            upvotes INTEGER DEFAULT 0,
                            downvotes INTEGER DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users (id)
                        )
                    ''')
                else:
                    # Create without foreign key if users table doesn't exist
                    print("[WARNING] Users table not found, creating feedback table without foreign key")
                    cursor.execute('''
                        CREATE TABLE feedback (
                            id TEXT PRIMARY KEY,
                            user_id TEXT NOT NULL,
                            character_name TEXT,
                            content TEXT NOT NULL,
                            upvotes INTEGER DEFAULT 0,
                            downvotes INTEGER DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS feedback_votes (
                        id TEXT PRIMARY KEY,
                        feedback_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        vote_type TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (feedback_id) REFERENCES feedback (id) ON DELETE CASCADE,
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        UNIQUE(feedback_id, user_id)
                    )
                ''')
            conn.commit()
            print("[INFO] Feedback tables created successfully")
        if conn:
            conn.close()
    except Exception as e:
        import traceback
        logger.error(f"Failed to ensure feedback tables exist: {e}")
        print(traceback.format_exc())
        if conn:
            try:
                conn.rollback()
            except:
                pass
            try:
                conn.close()
            except:
                pass

@app.post("/api/feedback/create")
async def create_feedback(request: Dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a new feedback/suggestion post"""
    try:
        # Ensure tables exist before trying to use them
        ensure_feedback_tables_exist()
        
        user_id = current_user["user_id"]
        content = request.get('content', '').strip()
        character_id = request.get('character_id')
        
        if not content:
            raise HTTPException(status_code=400, detail="Feedback content cannot be empty")
        
        if len(content) > 1000:
            raise HTTPException(status_code=400, detail="Feedback too long (max 1000 characters)")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get character name if provided
        character_name = None
        if character_id:
            try:
                cursor.execute("SELECT name FROM characters WHERE id = ?", (character_id,))
                char = cursor.fetchone()
                if char:
                    character_name = char['name']
            except Exception as e:
                logger.warning(r"Could not fetch character name for feedback: {e}")
                # Continue without character name
        
        # Create feedback
        feedback_id = str(uuid.uuid4())
        try:
            cursor.execute(
                "INSERT INTO feedback (id, user_id, character_name, content) VALUES (?, ?, ?, ?)",
                (feedback_id, user_id, character_name, content)
            )
            conn.commit()
        except Exception as e:
            import traceback
            conn.rollback()
            error_msg = str(e)
            logger.error(f"Failed to create feedback: {error_msg}")
            print(traceback.format_exc())
            
            # If table doesn't exist error, try to create it and retry once
            if 'does not exist' in error_msg or 'no such table' in error_msg.lower():
                print("[INFO] Retrying after ensuring table exists...")
                conn.close()
                ensure_feedback_tables_exist()
                # Retry once
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO feedback (id, user_id, character_name, content) VALUES (?, ?, ?, ?)",
                    (feedback_id, user_id, character_name, content)
                )
                conn.commit()
            else:
                conn.close()
                raise HTTPException(status_code=500, detail=f"Failed to create feedback: {error_msg}")
        finally:
            if conn:
                conn.close()
        
        return {"success": True, "feedback_id": feedback_id, "message": "Feedback posted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Unexpected error in create_feedback: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/feedback/list")
async def list_feedback(limit: int = 50, offset: int = 0):
    """Get list of feedback posts with vote counts"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT id, character_name, content, upvotes, downvotes, created_at 
               FROM feedback 
               ORDER BY (upvotes - downvotes) DESC, created_at DESC 
               LIMIT ? OFFSET ?""",
            (limit, offset)
        )
        
        feedback_list = []
        for row in cursor.fetchall():
            feedback_list.append({
                'id': row['id'],
                'character_name': row['character_name'],
                'content': row['content'],
                'upvotes': row['upvotes'],
                'downvotes': row['downvotes'],
                'score': row['upvotes'] - row['downvotes'],
                'created_at': row['created_at']
            })
        
        conn.close()
        
        return {"success": True, "feedback": feedback_list}
    except Exception as e:
        import traceback
        print(f"Error in list_feedback: {e}")
        print(traceback.format_exc())
        # Return empty list on error instead of crashing
        return {"success": True, "feedback": []}

@app.post("/api/feedback/vote")
async def vote_feedback(request: Dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Vote on a feedback post (upvote or downvote)"""
    user_id = current_user["user_id"]
    feedback_id = request.get('feedback_id')
    vote_type = request.get('vote_type')  # 'upvote' or 'downvote'
    
    if not feedback_id:
        raise HTTPException(status_code=400, detail="feedback_id required")
    
    if vote_type not in ['upvote', 'downvote']:
        raise HTTPException(status_code=400, detail="vote_type must be 'upvote' or 'downvote'")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if feedback exists
    cursor.execute("SELECT id FROM feedback WHERE id = ?", (feedback_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    # Check if user already voted
    cursor.execute(
        "SELECT id, vote_type FROM feedback_votes WHERE feedback_id = ? AND user_id = ?",
        (feedback_id, user_id)
    )
    existing_vote = cursor.fetchone()
    
    vote_id = str(uuid.uuid4())
    
    if existing_vote:
        # User already voted - update or remove vote
        old_vote_type = existing_vote['vote_type']
        
        if old_vote_type == vote_type:
            # Same vote - remove it (toggle off)
            cursor.execute("DELETE FROM feedback_votes WHERE id = ?", (existing_vote['id'],))
            
            # Update feedback vote counts
            if vote_type == 'upvote':
                cursor.execute("UPDATE feedback SET upvotes = upvotes - 1 WHERE id = ?", (feedback_id,))
            else:
                cursor.execute("UPDATE feedback SET downvotes = downvotes - 1 WHERE id = ?", (feedback_id,))
        else:
            # Different vote - change it
            cursor.execute(
                "UPDATE feedback_votes SET vote_type = ? WHERE id = ?",
                (vote_type, existing_vote['id'])
            )
            
            # Update feedback vote counts
            if old_vote_type == 'upvote':
                cursor.execute("UPDATE feedback SET upvotes = upvotes - 1, downvotes = downvotes + 1 WHERE id = ?", (feedback_id,))
            else:
                cursor.execute("UPDATE feedback SET upvotes = upvotes + 1, downvotes = downvotes - 1 WHERE id = ?", (feedback_id,))
    else:
        # New vote
        cursor.execute(
            "INSERT INTO feedback_votes (id, feedback_id, user_id, vote_type) VALUES (?, ?, ?, ?)",
            (vote_id, feedback_id, user_id, vote_type)
        )
        
        # Update feedback vote counts
        if vote_type == 'upvote':
            cursor.execute("UPDATE feedback SET upvotes = upvotes + 1 WHERE id = ?", (feedback_id,))
        else:
            cursor.execute("UPDATE feedback SET downvotes = downvotes + 1 WHERE id = ?", (feedback_id,))
    
    # Get updated vote counts
    cursor.execute("SELECT upvotes, downvotes FROM feedback WHERE id = ?", (feedback_id,))
    result = cursor.fetchone()
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "upvotes": result['upvotes'],
        "downvotes": result['downvotes'],
        "score": result['upvotes'] - result['downvotes']
    }

@app.get("/api/feedback/my-votes")
async def get_my_votes(current_user: dict = Depends(get_current_user)):
    """Get all feedback IDs that the current user has voted on"""
    user_id = current_user["user_id"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT feedback_id, vote_type FROM feedback_votes WHERE user_id = ?",
        (user_id,)
    )
    
    votes = {}
    for row in cursor.fetchall():
        votes[row['feedback_id']] = row['vote_type']
    
    conn.close()
    
    return {"success": True, "votes": votes}

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
    if USE_POSTGRES:
        cursor.execute(
            "UPDATE characters SET pvp_enabled = TRUE WHERE id = %s",
            (character_id,)
        )
    else:
        cursor.execute(
            "UPDATE characters SET pvp_enabled = 1 WHERE id = ?",
            (character_id,)
        )
    
    # Add to queue
    set_pvp_queue_entry(character_id, str(datetime.now().timestamp()))
    
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
    if USE_POSTGRES:
        cursor.execute(
            "UPDATE characters SET pvp_enabled = FALSE WHERE id = %s",
            (character_id,)
        )
    else:
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
    
    if USE_POSTGRES:
        cursor.execute("""
            SELECT id, name, level, exp, pvp_enabled
            FROM characters
            WHERE id != %s 
            AND level BETWEEN %s AND %s
            AND pvp_enabled = TRUE
            ORDER BY ABS(level - %s) ASC, name ASC
            LIMIT 20
        """, (character_id, min_level, max_level, char_level))
    else:
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
async def get_pvp_leaderboard(limit: int = 50, offset: int = 0):
    """Get PVP leaderboard (ranked by MMR) using persistent tracking data."""
    try:
        rows = player_tracking_service.get_leaderboard(limit=limit, offset=offset)
    except Exception as exc:
        logger.error(f"Failed to load leaderboard: {exc}")
        raise HTTPException(status_code=500, detail="Unable to load leaderboard")

    leaderboard = []
    rank = offset + 1
    for row in rows:
        wins = row.get("wins", 0) or 0
        losses = row.get("losses", 0) or 0
        total_games = wins + losses
        win_rate = (wins / total_games * 100) if total_games else 0.0
        leaderboard.append(
            {
                "rank": rank,
                "id": row.get("id"),
                "name": row.get("name"),
                "username": row.get("username"),
                "level": row.get("level"),
                "mmr": row.get("mmr", 1000),
                "wins": wins,
                "losses": losses,
                "win_rate": round(win_rate, 2),
                "best_mmr": row.get("best_mmr", row.get("mmr", 1000)),
            }
        )
        rank += 1

    return {"success": True, "leaderboard": leaderboard}


@app.get("/api/pvp/queue-status")
async def get_pvp_queue_status(character_id: str):
    """Get PVP queue status and estimated wait time"""
    if not character_id:
        raise HTTPException(status_code=400, detail="character_id required")
    
    in_queue = get_pvp_queue_entry(character_id) is not None
    
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

@app.get("/api/players/online-count")
async def get_online_player_count():
    """Get count of currently online players (active in last 5 minutes)"""
    current_time = datetime.utcnow().timestamp()
    five_minutes_ago = current_time - (5 * 60)  # 5 minutes in seconds
    
    # Prune stale sessions and count recent ones
    game_state.prune_sessions(settings.active_session_ttl)
    online_count = sum(
        1
        for session in game_state.active_sessions.values()
        if session.get("last_seen", 0) >= five_minutes_ago
    )
    
    return {"success": True, "online_count": online_count}

@app.get("/api/player/profile")
async def get_player_profile(current_user: dict = Depends(get_current_user)):
    """Return aggregated profile + character summary for the current user."""
    data = player_tracking_service.get_profile(current_user["user_id"])
    return {"success": True, **data}

@app.get("/api/player/progress/{character_id}")
async def get_character_progress(character_id: str, current_user: dict = Depends(get_current_user), limit: int = 25):
    """Return recent progress logs for a specific character."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM characters WHERE id = ? AND user_id = ?", (character_id, current_user["user_id"]))
    owned = cursor.fetchone()
    conn.close()
    if not owned:
        raise HTTPException(status_code=404, detail="Character not found or access denied")
    
    entries = player_tracking_service.get_recent_progress(character_id, limit=limit)
    return {"success": True, "entries": entries}

@app.get("/api/player/matches")
async def get_recent_matches(limit: int = 20, current_user: dict = Depends(get_current_user)):
    """Return recent PvP matches for the authenticated user."""
    matches = player_tracking_service.get_recent_matches(current_user["user_id"], limit=limit)
    return {"success": True, "matches": matches}

# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint - returns detailed status of all dependencies"""
    db_type = "PostgreSQL" if USE_POSTGRES else "SQLite"
    db_configured = "yes" if DATABASE_URL else "no"
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "environment": settings.environment,
        "checks": {}
    }
    
    # Test database connection
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        start_time = datetime.utcnow()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        health_status["checks"]["database"] = {
            "status": "healthy",
            "type": db_type,
            "configured": db_configured,
            "response_time_ms": round(response_time, 2)
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "type": db_type,
            "configured": db_configured,
            "error": str(e) if not IS_PRODUCTION else "Connection failed"
        }
        health_status["status"] = "degraded"
    
    # Test Redis connection
    try:
        r = get_redis_client()
        if r:
            start_time = datetime.utcnow()
            r.ping()
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            health_status["checks"]["redis"] = {
                "status": "healthy",
                "configured": "yes" if REDIS_URL else "no",
                "response_time_ms": round(response_time, 2)
            }
        else:
            health_status["checks"]["redis"] = {
                "status": "not_configured",
                "configured": "no",
                "message": "Using in-memory storage"
            }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "configured": "yes" if REDIS_URL else "no",
            "error": str(e) if not IS_PRODUCTION else "Connection failed"
        }
        if REDIS_URL:  # Only degrade if Redis is expected
            health_status["status"] = "degraded"
    
    return health_status

@app.get("/health/live")
async def liveness_check():
    """Liveness probe - simple check that server is responding"""
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness_check():
    """Readiness probe - check if server is ready to serve traffic"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return {"status": "ready"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e) if not IS_PRODUCTION else "Database unavailable"}
        )

# Metrics tracking
request_count = 0
error_count = 0
request_times = []

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Track request metrics"""
    global request_count, error_count
    import time
    start_time = time.time()
    
    try:
        response = await call_next(request)
        request_count += 1
        if response.status_code >= 400:
            error_count += 1
        return response
    except Exception as e:
        error_count += 1
        raise
    finally:
        duration = time.time() - start_time
        request_times.append(duration)
        # Keep only last 1000 request times
        if len(request_times) > 1000:
            request_times.pop(0)

@app.get("/metrics")
async def metrics():
    """Metrics endpoint for monitoring"""
    global request_count, error_count, request_times
    
    avg_response_time = sum(request_times) / len(request_times) if request_times else 0
    p95_response_time = sorted(request_times)[int(len(request_times) * 0.95)] if len(request_times) > 20 else 0
    
    # Get database stats
    db_connection_count = 0
    try:
        conn = get_db_connection()
        if USE_POSTGRES:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()")
            db_connection_count = cursor.fetchone()['count']
        conn.close()
    except:
        pass
    
    # Get Redis stats
    redis_info = {}
    try:
        r = get_redis_client()
        if r:
            redis_info = r.info()
    except:
        pass
    
    return {
        "requests": {
            "total": request_count,
            "errors": error_count,
            "success_rate": ((request_count - error_count) / request_count * 100) if request_count > 0 else 100
        },
        "response_times": {
            "average_ms": round(avg_response_time * 1000, 2),
            "p95_ms": round(p95_response_time * 1000, 2) if p95_response_time > 0 else 0
        },
        "database": {
            "active_connections": db_connection_count
        },
        "redis": {
            "connected": redis_info.get("connected_clients", 0) > 0 if redis_info else False,
            "used_memory_mb": round(redis_info.get("used_memory", 0) / 1024 / 1024, 2) if redis_info else 0
        },
        "uptime_seconds": (datetime.utcnow() - app.state.start_time).total_seconds() if hasattr(app.state, 'start_time') else 0
    }

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    # Set startup time for metrics
    app.state.start_time = datetime.utcnow()
    
    # Validate environment variables
    try:
        from env_validation import validate_environment
        validate_environment()
    except ImportError:
        logger.warning("env_validation module not found, skipping environment validation")
    except Exception as e:
        logger.error(f"Environment validation failed: {e}")
        if IS_PRODUCTION:
            raise
    
    # Log database configuration
    logger.info("=" * 60)
    logger.info("Database Configuration:")
    if DATABASE_URL:
        # Mask password in URL for logging
        url_parts = DATABASE_URL.split("@")
        if len(url_parts) > 1:
            safe_url = "postgresql://***@" + "@".join(url_parts[1:])
        else:
            safe_url = "postgresql://***"
        logger.info(f"  DATABASE_URL: {safe_url}")
        logger.info(f"  Database Type: PostgreSQL")
    else:
        logger.info(f"  DATABASE_URL: Not set")
        logger.info(f"  Database Type: SQLite (fallback)")
    
    # Test database connection
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        if USE_POSTGRES:
            logger.info("✓ PostgreSQL connection successful (data will persist)")
        else:
            logger.warning("Using SQLite (data will NOT persist in production environments)")
            logger.warning("To fix: Provision a managed PostgreSQL instance (e.g., Fly Postgres) and set the DATABASE_URL environment variable")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        if USE_POSTGRES:
            logger.error("PostgreSQL connection failed but DATABASE_URL is set!")
            logger.error("Check the managed PostgreSQL service status and connection string (Fly Postgres or equivalent)")
    
    # Log Redis configuration
    if REDIS_URL:
        logger.info(f"  REDIS_URL: Configured")
        r = get_redis_client()
        if r:
            logger.info("✓ Redis connection successful")
        else:
            logger.warning("Redis connection failed (using in-memory storage)")
    else:
        logger.info("  REDIS_URL: Not set (using in-memory storage)")
    
    logger.info("=" * 60)
    
    # Initialize database tables
    try:
        init_database()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.warning("Server will continue but some features may not work")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

