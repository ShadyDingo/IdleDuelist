#!/usr/bin/env python3
"""
Create PVP system tables
"""

import sqlite3

def create_pvp_tables():
    """Create PVP system tables"""
    conn = sqlite3.connect('idle_duelist.db')
    cursor = conn.cursor()
    
    # PVP Matchmaking and Queue System
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matchmaking_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            rating INTEGER DEFAULT 1200,
            faction TEXT DEFAULT 'order_of_the_silver_crusade',
            queue_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'waiting',
            FOREIGN KEY (player_id) REFERENCES players (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pvp_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player1_id TEXT NOT NULL,
            player2_id TEXT NOT NULL,
            winner_id TEXT,
            match_log TEXT,
            duration INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player1_id) REFERENCES players (id),
            FOREIGN KEY (player2_id) REFERENCES players (id)
        )
    ''')
    
    # Player Statistics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            total_duels INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            win_streak INTEGER DEFAULT 0,
            best_win_streak INTEGER DEFAULT 0,
            total_damage_dealt INTEGER DEFAULT 0,
            total_damage_taken INTEGER DEFAULT 0,
            favorite_ability TEXT,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ PVP system tables created successfully")

if __name__ == "__main__":
    create_pvp_tables()
