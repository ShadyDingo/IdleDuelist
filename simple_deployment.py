#!/usr/bin/env python3
"""
Simplified deployment for Fly.io with minimal memory usage
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sqlite3
from contextlib import contextmanager

# Create minimal FastAPI app
app = FastAPI(title="IdleDuelist Simple Backend", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Simple players table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id TEXT PRIMARY KEY,
                    username TEXT,
                    rating INTEGER DEFAULT 1000,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0
                )
            """)
            
            conn.commit()
            print("✅ Simple database initialized")
    except Exception as e:
        print(f"❌ Database init failed: {e}")

# Initialize database
init_database()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "IdleDuelist Simple Backend is running!",
        "status": "healthy",
        "memory": "optimized"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "simple": True}

@app.post("/players/register")
async def register_player(player_data: dict):
    """Simple player registration"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO players (id, username, rating, wins, losses)
                VALUES (?, ?, ?, ?, ?)
            """, (
                player_data.get("id", "test"),
                player_data.get("username", "TestPlayer"),
                player_data.get("rating", 1000),
                player_data.get("wins", 0),
                player_data.get("losses", 0)
            ))
            conn.commit()
            return {"status": "success", "message": "Player registered"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/stats")
async def get_stats():
    """Get simple stats"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM players")
            player_count = cursor.fetchone()["count"]
            
            return {
                "total_players": player_count,
                "status": "online",
                "simple": True
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting simple IdleDuelist backend on port {port}")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
