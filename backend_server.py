#!/usr/bin/env python3
"""
IdleDuelist Backend Server
Handles player data, loadouts, and real-time dueling
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
import json
import uuid
import time
from datetime import datetime, timedelta
import uvicorn
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

# Database setup
DATABASE_URL = "sqlite:///./idle_duelist.db"  # Change to PostgreSQL for production
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Player(Base):
    __tablename__ = "players"
    
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    rating = Column(Integer, default=1000)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    equipment = Column(JSON)
    faction = Column(String)
    abilities = Column(JSON)
    last_active = Column(DateTime, default=datetime.utcnow)
    is_online = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Duel(Base):
    __tablename__ = "duels"
    
    id = Column(String, primary_key=True, index=True)
    player1_id = Column(String)
    player2_id = Column(String)
    winner_id = Column(String)
    player1_loadout = Column(JSON)
    player2_loadout = Column(JSON)
    duel_log = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class OfflineDuel(Base):
    __tablename__ = "offline_duels"
    
    id = Column(String, primary_key=True, index=True)
    defender_id = Column(String)
    attacker_id = Column(String)
    winner_id = Column(String)
    defender_loadout = Column(JSON)
    attacker_loadout = Column(JSON)
    duel_log = Column(JSON)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

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
    last_active: Optional[datetime] = None
    is_online: bool = False

class DuelRequest(BaseModel):
    player_id: str
    rating_range: int = 100

class DuelResult(BaseModel):
    winner_id: str
    loser_id: str
    duel_log: List[str]

# FastAPI app
app = FastAPI(title="IdleDuelist Backend", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, player_id: str):
        await websocket.accept()
        self.active_connections[player_id] = websocket
    
    def disconnect(self, player_id: str):
        if player_id in self.active_connections:
            del self.active_connections[player_id]
    
    async def send_personal_message(self, message: str, player_id: str):
        if player_id in self.active_connections:
            await self.active_connections[player_id].send_text(message)

manager = ConnectionManager()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API Endpoints
@app.post("/players/register")
async def register_player(player_data: PlayerData):
    """Register a new player or update existing player data"""
    db = SessionLocal()
    try:
        # Check if player exists
        existing_player = db.query(Player).filter(Player.id == player_data.id).first()
        
        if existing_player:
            # Update existing player
            existing_player.username = player_data.username
            existing_player.equipment = player_data.equipment
            existing_player.faction = player_data.faction
            existing_player.abilities = player_data.abilities
            existing_player.last_active = datetime.utcnow()
            existing_player.is_online = True
        else:
            # Create new player
            new_player = Player(
                id=player_data.id,
                username=player_data.username,
                rating=player_data.rating,
                wins=player_data.wins,
                losses=player_data.losses,
                equipment=player_data.equipment,
                faction=player_data.faction,
                abilities=player_data.abilities,
                last_active=datetime.utcnow(),
                is_online=True
            )
            db.add(new_player)
        
        db.commit()
        return {"status": "success", "message": "Player data synced"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/players/{player_id}")
async def get_player(player_id: str):
    """Get player data by ID"""
    db = SessionLocal()
    try:
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        return PlayerData(
            id=player.id,
            username=player.username,
            rating=player.rating,
            wins=player.wins,
            losses=player.losses,
            equipment=player.equipment,
            faction=player.faction,
            abilities=player.abilities,
            last_active=player.last_active,
            is_online=player.is_online
        )
    finally:
        db.close()

@app.post("/duels/request")
async def request_duel(duel_request: DuelRequest):
    """Request a duel with another player"""
    db = SessionLocal()
    try:
        # Get player data
        player = db.query(Player).filter(Player.id == duel_request.player_id).first()
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Find opponent with similar rating
        min_rating = player.rating - duel_request.rating_range
        max_rating = player.rating + duel_request.rating_range
        
        opponent = db.query(Player).filter(
            Player.id != duel_request.player_id,
            Player.rating >= min_rating,
            Player.rating <= max_rating,
            Player.is_online == True
        ).first()
        
        if not opponent:
            # No online opponent found, create offline duel
            offline_duel = OfflineDuel(
                id=str(uuid.uuid4()),
                defender_id=duel_request.player_id,
                attacker_id=duel_request.player_id,
                defender_loadout=player.equipment,
                attacker_loadout=player.equipment,
                processed=False
            )
            db.add(offline_duel)
            db.commit()
            
            return {
                "status": "offline",
                "message": "No online opponents found. Your character will duel others while you're offline.",
                "duel_id": offline_duel.id
            }
        
        # Create duel
        duel = Duel(
            id=str(uuid.uuid4()),
            player1_id=duel_request.player_id,
            player2_id=opponent.id,
            player1_loadout=player.equipment,
            player2_loadout=opponent.equipment
        )
        db.add(duel)
        db.commit()
        
        return {
            "status": "matched",
            "duel_id": duel.id,
            "opponent": {
                "id": opponent.id,
                "username": opponent.username,
                "rating": opponent.rating,
                "loadout": opponent.equipment
            }
        }
    
    finally:
        db.close()

@app.post("/duels/{duel_id}/result")
async def submit_duel_result(duel_id: str, result: DuelResult):
    """Submit the result of a duel"""
    db = SessionLocal()
    try:
        duel = db.query(Duel).filter(Duel.id == duel_id).first()
        if not duel:
            raise HTTPException(status_code=404, detail="Duel not found")
        
        # Update duel result
        duel.winner_id = result.winner_id
        duel.duel_log = result.duel_log
        
        # Update player stats
        winner = db.query(Player).filter(Player.id == result.winner_id).first()
        loser = db.query(Player).filter(Player.id == result.loser_id).first()
        
        if winner:
            winner.wins += 1
            winner.rating += 20  # Simple rating system
        
        if loser:
            loser.losses += 1
            loser.rating = max(800, loser.rating - 15)
        
        db.commit()
        
        return {"status": "success", "message": "Duel result recorded"}
    
    finally:
        db.close()

@app.get("/players/{player_id}/offline_duels")
async def get_offline_duels(player_id: str):
    """Get duels that happened while player was offline"""
    db = SessionLocal()
    try:
        duels = db.query(OfflineDuel).filter(
            OfflineDuel.defender_id == player_id,
            OfflineDuel.processed == False
        ).all()
        
        results = []
        for duel in duels:
            results.append({
                "id": duel.id,
                "attacker_id": duel.attacker_id,
                "winner_id": duel.winner_id,
                "duel_log": duel.duel_log,
                "created_at": duel.created_at
            })
            
            # Mark as processed
            duel.processed = True
        
        db.commit()
        return {"duels": results}
    
    finally:
        db.close()

@app.get("/players/{player_id}/opponents")
async def get_available_opponents(player_id: str, limit: int = 10):
    """Get list of available opponents for dueling"""
    db = SessionLocal()
    try:
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Get opponents with similar rating
        min_rating = player.rating - 150
        max_rating = player.rating + 150
        
        opponents = db.query(Player).filter(
            Player.id != player_id,
            Player.rating >= min_rating,
            Player.rating <= max_rating
        ).limit(limit).all()
        
        return {
            "opponents": [
                {
                    "id": opp.id,
                    "username": opp.username,
                    "rating": opp.rating,
                    "wins": opp.wins,
                    "losses": opp.losses,
                    "loadout": opp.equipment,
                    "faction": opp.faction
                }
                for opp in opponents
            ]
        }
    
    finally:
        db.close()

@app.websocket("/ws/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: str):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket, player_id)
    
    # Update player online status
    db = SessionLocal()
    try:
        player = db.query(Player).filter(Player.id == player_id).first()
        if player:
            player.is_online = True
            player.last_active = datetime.utcnow()
            db.commit()
    finally:
        db.close()
    
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({"type": "ping"}))
    
    except WebSocketDisconnect:
        manager.disconnect(player_id)
        
        # Update player offline status
        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.id == player_id).first()
            if player:
                player.is_online = False
                player.last_active = datetime.utcnow()
                db.commit()
        finally:
            db.close()

# Background task for processing offline duels
@app.on_event("startup")
async def startup_event():
    """Start background task for processing offline duels"""
    asyncio.create_task(process_offline_duels())

async def process_offline_duels():
    """Process offline duels in the background"""
    while True:
        try:
            db = SessionLocal()
            try:
                # Get unprocessed offline duels
                duels = db.query(OfflineDuel).filter(
                    OfflineDuel.processed == False,
                    OfflineDuel.created_at < datetime.utcnow() - timedelta(minutes=1)
                ).all()
                
                for duel in duels:
                    # Simulate duel between defender and attacker
                    # This would use the same combat logic as the mobile app
                    winner_id = simulate_duel(duel.defender_id, duel.attacker_id, duel.defender_loadout, duel.attacker_loadout)
                    
                    duel.winner_id = winner_id
                    duel.processed = True
                    
                    # Update player stats
                    if winner_id == duel.defender_id:
                        loser_id = duel.attacker_id
                    else:
                        loser_id = duel.defender_id
                    
                    winner = db.query(Player).filter(Player.id == winner_id).first()
                    loser = db.query(Player).filter(Player.id == loser_id).first()
                    
                    if winner:
                        winner.wins += 1
                    if loser:
                        loser.losses += 1
                
                db.commit()
            
            finally:
                db.close()
        
        except Exception as e:
            logging.error(f"Error processing offline duels: {e}")
        
        await asyncio.sleep(60)  # Process every minute

def simulate_duel(defender_id: str, attacker_id: str, defender_loadout: dict, attacker_loadout: dict) -> str:
    """Simulate a duel between two players (simplified version)"""
    # This is a simplified simulation - in reality, you'd want to use the same combat logic
    # as the mobile app to ensure consistency
    
    # For now, return a random winner (50/50 chance)
    import random
    return defender_id if random.random() < 0.5 else attacker_id

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
