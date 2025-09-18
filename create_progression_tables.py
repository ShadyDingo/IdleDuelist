#!/usr/bin/env python3
"""
Create progression system tables
"""

import sqlite3

def create_progression_tables():
    """Create progression system tables"""
    conn = sqlite3.connect('idle_duelist.db')
    cursor = conn.cursor()
    
    # Character Progression System
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_progression (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            level INTEGER DEFAULT 1,
            experience INTEGER DEFAULT 0,
            experience_to_next INTEGER DEFAULT 100,
            skill_points INTEGER DEFAULT 0,
            total_skill_points_earned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            skill_name TEXT NOT NULL,
            skill_level INTEGER DEFAULT 0,
            skill_points_invested INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players (id),
            UNIQUE(player_id, skill_name)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            requirement_value INTEGER NOT NULL,
            reward_type TEXT NOT NULL,
            reward_value INTEGER NOT NULL,
            icon TEXT DEFAULT '🏆',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            achievement_id INTEGER NOT NULL,
            progress INTEGER DEFAULT 0,
            completed BOOLEAN DEFAULT FALSE,
            completed_at TIMESTAMP,
            claimed BOOLEAN DEFAULT FALSE,
            claimed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players (id),
            FOREIGN KEY (achievement_id) REFERENCES achievements (id),
            UNIQUE(player_id, achievement_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            quest_type TEXT NOT NULL,
            quest_description TEXT NOT NULL,
            target_value INTEGER NOT NULL,
            current_progress INTEGER DEFAULT 0,
            reward_type TEXT NOT NULL,
            reward_value INTEGER NOT NULL,
            completed BOOLEAN DEFAULT FALSE,
            claimed BOOLEAN DEFAULT FALSE,
            quest_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Progression system tables created successfully")

if __name__ == "__main__":
    create_progression_tables()
