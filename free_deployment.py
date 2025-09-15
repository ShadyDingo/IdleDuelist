#!/usr/bin/env python3
"""
Free Deployment Configuration for IdleDuelist
Optimized for Railway, Render, or Fly.io free tiers
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
import uuid
import time
from datetime import datetime
import os

# Use SQLite for free deployment (no external database needed)
import sqlite3
from contextlib import contextmanager

# Initialize FastAPI app
app = FastAPI(title="IdleDuelist Free Backend", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (for mobile app assets) - optional
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Database setup (SQLite for free deployment)
DATABASE_URL = "sqlite:///./idle_duelist.db"

@contextmanager
def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect("idle_duelist.db")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize database tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Players table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE,
                rating INTEGER DEFAULT 1000,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                equipment TEXT,
                faction TEXT,
                abilities TEXT,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_online BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Duels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS duels (
                id TEXT PRIMARY KEY,
                player1_id TEXT,
                player2_id TEXT,
                winner_id TEXT,
                player1_loadout TEXT,
                player2_loadout TEXT,
                duel_log TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Offline duels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS offline_duels (
                id TEXT PRIMARY KEY,
                defender_id TEXT,
                attacker_id TEXT,
                winner_id TEXT,
                defender_loadout TEXT,
                attacker_loadout TEXT,
                duel_log TEXT,
                processed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()

# Initialize database on startup
init_database()

# Pydantic models
class PlayerData(BaseModel):
    id: str
    username: str
    rating: int = 1000
    wins: int = 0
    losses: int = 0
    equipment: Dict
    faction: str
    abilities: List[str]

class DuelRequest(BaseModel):
    player_id: str
    rating_range: int = 100

class DuelResult(BaseModel):
    winner_id: str
    loser_id: str
    duel_log: List[str]

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "IdleDuelist Backend is running!",
        "version": "1.0.0",
        "status": "online",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/players/register")
async def register_player(player_data: PlayerData):
    """Register a new player or update existing player data"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if player exists
        cursor.execute("SELECT id FROM players WHERE id = ?", (player_data.id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing player
            cursor.execute("""
                UPDATE players SET 
                    username = ?, equipment = ?, faction = ?, abilities = ?,
                    last_active = CURRENT_TIMESTAMP, is_online = TRUE
                WHERE id = ?
            """, (
                player_data.username,
                json.dumps(player_data.equipment),
                player_data.faction,
                json.dumps(player_data.abilities),
                player_data.id
            ))
        else:
            # Create new player
            cursor.execute("""
                INSERT INTO players (id, username, rating, wins, losses, equipment, faction, abilities, is_online)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, TRUE)
            """, (
                player_data.id,
                player_data.username,
                player_data.rating,
                player_data.wins,
                player_data.losses,
                json.dumps(player_data.equipment),
                player_data.faction,
                json.dumps(player_data.abilities)
            ))
        
        conn.commit()
        return {"status": "success", "message": "Player data synced"}

@app.get("/players/{player_id}")
async def get_player(player_id: str):
    """Get player data by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM players WHERE id = ?", (player_id,))
        player = cursor.fetchone()
        
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        return {
            "id": player["id"],
            "username": player["username"],
            "rating": player["rating"],
            "wins": player["wins"],
            "losses": player["losses"],
            "equipment": json.loads(player["equipment"]),
            "faction": player["faction"],
            "abilities": json.loads(player["abilities"]),
            "last_active": player["last_active"],
            "is_online": bool(player["is_online"])
        }

@app.post("/duels/request")
async def request_duel(duel_request: DuelRequest):
    """Request a duel with another player"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get player data
        cursor.execute("SELECT * FROM players WHERE id = ?", (duel_request.player_id,))
        player = cursor.fetchone()
        
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Find opponent with similar rating
        min_rating = player["rating"] - duel_request.rating_range
        max_rating = player["rating"] + duel_request.rating_range
        
        cursor.execute("""
            SELECT * FROM players 
            WHERE id != ? AND rating >= ? AND rating <= ? AND is_online = 1
            ORDER BY RANDOM() LIMIT 1
        """, (duel_request.player_id, min_rating, max_rating))
        
        opponent = cursor.fetchone()
        
        if not opponent:
            # No online opponent found, create offline duel
            duel_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO offline_duels (id, defender_id, attacker_id, defender_loadout, attacker_loadout)
                VALUES (?, ?, ?, ?, ?)
            """, (
                duel_id,
                duel_request.player_id,
                duel_request.player_id,
                player["equipment"],
                player["equipment"]
            ))
            conn.commit()
            
            return {
                "status": "offline",
                "message": "No online opponents found. Your character will duel others while you're offline.",
                "duel_id": duel_id
            }
        
        # Create duel
        duel_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO duels (id, player1_id, player2_id, player1_loadout, player2_loadout)
            VALUES (?, ?, ?, ?, ?)
        """, (
            duel_id,
            duel_request.player_id,
            opponent["id"],
            player["equipment"],
            opponent["equipment"]
        ))
        conn.commit()
        
        return {
            "status": "matched",
            "duel_id": duel_id,
            "opponent": {
                "id": opponent["id"],
                "username": opponent["username"],
                "rating": opponent["rating"],
                "loadout": json.loads(opponent["equipment"])
            }
        }

@app.post("/duels/{duel_id}/result")
async def submit_duel_result(duel_id: str, result: DuelResult):
    """Submit the result of a duel"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Update duel result
        cursor.execute("""
            UPDATE duels SET winner_id = ?, duel_log = ?
            WHERE id = ?
        """, (result.winner_id, json.dumps(result.duel_log), duel_id))
        
        # Update player stats
        cursor.execute("""
            UPDATE players SET wins = wins + 1, rating = rating + 20
            WHERE id = ?
        """, (result.winner_id,))
        
        cursor.execute("""
            UPDATE players SET losses = losses + 1, rating = MAX(800, rating - 15)
            WHERE id = ?
        """, (result.loser_id,))
        
        conn.commit()
        return {"status": "success", "message": "Duel result recorded"}

@app.get("/players/{player_id}/opponents")
async def get_available_opponents(player_id: str, limit: int = 10):
    """Get list of available opponents for dueling"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get player rating
        cursor.execute("SELECT rating FROM players WHERE id = ?", (player_id,))
        player = cursor.fetchone()
        
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Get opponents with similar rating
        min_rating = player["rating"] - 150
        max_rating = player["rating"] + 150
        
        cursor.execute("""
            SELECT * FROM players 
            WHERE id != ? AND rating >= ? AND rating <= ?
            ORDER BY RANDOM() LIMIT ?
        """, (player_id, min_rating, max_rating, limit))
        
        opponents = cursor.fetchall()
        
        return {
            "opponents": [
                {
                    "id": opp["id"],
                    "username": opp["username"],
                    "rating": opp["rating"],
                    "wins": opp["wins"],
                    "losses": opp["losses"],
                    "loadout": json.loads(opp["equipment"]),
                    "faction": opp["faction"]
                }
                for opp in opponents
            ]
        }

@app.get("/players/{player_id}/offline_duels")
async def get_offline_duels(player_id: str):
    """Get duels that happened while player was offline"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM offline_duels 
            WHERE defender_id = ? AND processed = 0
        """, (player_id,))
        
        duels = cursor.fetchall()
        
        results = []
        for duel in duels:
            results.append({
                "id": duel["id"],
                "attacker_id": duel["attacker_id"],
                "winner_id": duel["winner_id"],
                "duel_log": json.loads(duel["duel_log"]) if duel["duel_log"] else [],
                "created_at": duel["created_at"]
            })
            
            # Mark as processed
            cursor.execute("UPDATE offline_duels SET processed = 1 WHERE id = ?", (duel["id"],))
        
        conn.commit()
        return {"duels": results}

@app.get("/stats")
async def get_server_stats():
    """Get server statistics"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Count players
        cursor.execute("SELECT COUNT(*) as count FROM players")
        total_players = cursor.fetchone()["count"]
        
        # Count online players
        cursor.execute("SELECT COUNT(*) as count FROM players WHERE is_online = 1")
        online_players = cursor.fetchone()["count"]
        
        # Count total duels
        cursor.execute("SELECT COUNT(*) as count FROM duels")
        total_duels = cursor.fetchone()["count"]
        
        return {
            "total_players": total_players,
            "online_players": online_players,
            "total_duels": total_duels,
            "server_status": "online",
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting IdleDuelist backend on port {port}")
    print(f"Host: 0.0.0.0")
    print(f"Environment: {os.environ.get('FLY_REGION', 'local')}")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
