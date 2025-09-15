#!/usr/bin/env python3
"""
Network Manager for IdleDuelist Mobile App
Handles online/offline states, player sync, and real-time dueling
"""

import json
import requests
import websocket
import threading
import time
from typing import Dict, List, Optional, Callable
from datetime import datetime
import uuid
import logging

class NetworkManager:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http", "ws")
        self.player_id: Optional[str] = None
        self.is_online = False
        self.websocket = None
        self.ws_thread = None
        self.offline_queue = []
        self.sync_callbacks: List[Callable] = []
        self.duel_callbacks: List[Callable] = []
        
        # Load offline queue from local storage
        self.load_offline_queue()
    
    def set_player_id(self, player_id: str):
        """Set the current player ID"""
        self.player_id = player_id
    
    def register_sync_callback(self, callback: Callable):
        """Register callback for when data is synced"""
        self.sync_callbacks.append(callback)
    
    def register_duel_callback(self, callback: Callable):
        """Register callback for duel events"""
        self.duel_callbacks.append(callback)
    
    def check_connection(self) -> bool:
        """Check if we can connect to the server"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def sync_player_data(self, player_data: Dict) -> bool:
        """Sync player data with server"""
        try:
            if not self.player_id:
                return False
            
            # Add player ID to data
            player_data["id"] = self.player_id
            
            response = requests.post(
                f"{self.base_url}/players/register",
                json=player_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.is_online = True
                self.process_offline_queue()
                self.notify_sync_callbacks(True)
                return True
            else:
                self.queue_for_offline_sync(player_data)
                return False
        
        except Exception as e:
            logging.error(f"Error syncing player data: {e}")
            self.queue_for_offline_sync(player_data)
            return False
    
    def get_player_data(self) -> Optional[Dict]:
        """Get player data from server"""
        try:
            if not self.player_id:
                return None
            
            response = requests.get(
                f"{self.base_url}/players/{self.player_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        
        except Exception as e:
            logging.error(f"Error getting player data: {e}")
            return None
    
    def get_available_opponents(self, limit: int = 10) -> List[Dict]:
        """Get list of available opponents"""
        try:
            if not self.player_id:
                return []
            
            response = requests.get(
                f"{self.base_url}/players/{self.player_id}/opponents",
                params={"limit": limit},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("opponents", [])
            else:
                return []
        
        except Exception as e:
            logging.error(f"Error getting opponents: {e}")
            return []
    
    def request_duel(self, rating_range: int = 100) -> Dict:
        """Request a duel with another player"""
        try:
            if not self.player_id:
                return {"status": "error", "message": "No player ID"}
            
            response = requests.post(
                f"{self.base_url}/duels/request",
                json={"player_id": self.player_id, "rating_range": rating_range},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "message": "Failed to request duel"}
        
        except Exception as e:
            logging.error(f"Error requesting duel: {e}")
            return {"status": "error", "message": "Network error"}
    
    def submit_duel_result(self, duel_id: str, winner_id: str, loser_id: str, duel_log: List[str]) -> bool:
        """Submit the result of a duel"""
        try:
            response = requests.post(
                f"{self.base_url}/duels/{duel_id}/result",
                json={
                    "winner_id": winner_id,
                    "loser_id": loser_id,
                    "duel_log": duel_log
                },
                timeout=10
            )
            
            return response.status_code == 200
        
        except Exception as e:
            logging.error(f"Error submitting duel result: {e}")
            return False
    
    def get_offline_duels(self) -> List[Dict]:
        """Get duels that happened while offline"""
        try:
            if not self.player_id:
                return []
            
            response = requests.get(
                f"{self.base_url}/players/{self.player_id}/offline_duels",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("duels", [])
            else:
                return []
        
        except Exception as e:
            logging.error(f"Error getting offline duels: {e}")
            return []
    
    def connect_websocket(self):
        """Connect to WebSocket for real-time updates"""
        try:
            if not self.player_id:
                return False
            
            ws_url = f"{self.ws_url}/ws/{self.player_id}"
            self.websocket = websocket.WebSocketApp(
                ws_url,
                on_message=self.on_websocket_message,
                on_error=self.on_websocket_error,
                on_close=self.on_websocket_close
            )
            
            self.ws_thread = threading.Thread(target=self.websocket.run_forever)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            
            return True
        
        except Exception as e:
            logging.error(f"Error connecting WebSocket: {e}")
            return False
    
    def disconnect_websocket(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            self.websocket.close()
            self.websocket = None
        
        if self.ws_thread:
            self.ws_thread.join(timeout=1)
            self.ws_thread = None
    
    def on_websocket_message(self, ws, message):
        """Handle WebSocket messages"""
        try:
            data = json.loads(message)
            
            if data.get("type") == "duel_request":
                self.notify_duel_callbacks("duel_request", data)
            elif data.get("type") == "duel_result":
                self.notify_duel_callbacks("duel_result", data)
            elif data.get("type") == "ping":
                # Respond to ping
                ws.send(json.dumps({"type": "pong"}))
        
        except Exception as e:
            logging.error(f"Error handling WebSocket message: {e}")
    
    def on_websocket_error(self, ws, error):
        """Handle WebSocket errors"""
        logging.error(f"WebSocket error: {error}")
        self.is_online = False
    
    def on_websocket_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        logging.info("WebSocket connection closed")
        self.is_online = False
    
    def queue_for_offline_sync(self, data: Dict):
        """Queue data for sync when back online"""
        self.offline_queue.append({
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "type": "player_sync"
        })
        self.save_offline_queue()
    
    def process_offline_queue(self):
        """Process queued operations when back online"""
        for item in self.offline_queue:
            try:
                if item["type"] == "player_sync":
                    self.sync_player_data(item["data"])
            except Exception as e:
                logging.error(f"Error processing offline queue item: {e}")
        
        # Clear processed queue
        self.offline_queue = []
        self.save_offline_queue()
    
    def load_offline_queue(self):
        """Load offline queue from local storage"""
        try:
            with open("offline_queue.json", "r") as f:
                self.offline_queue = json.load(f)
        except FileNotFoundError:
            self.offline_queue = []
        except Exception as e:
            logging.error(f"Error loading offline queue: {e}")
            self.offline_queue = []
    
    def save_offline_queue(self):
        """Save offline queue to local storage"""
        try:
            with open("offline_queue.json", "w") as f:
                json.dump(self.offline_queue, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving offline queue: {e}")
    
    def notify_sync_callbacks(self, success: bool):
        """Notify sync callbacks"""
        for callback in self.sync_callbacks:
            try:
                callback(success)
            except Exception as e:
                logging.error(f"Error in sync callback: {e}")
    
    def notify_duel_callbacks(self, event_type: str, data: Dict):
        """Notify duel callbacks"""
        for callback in self.duel_callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                logging.error(f"Error in duel callback: {e}")
    
    def start_offline_duel_simulation(self):
        """Start simulating duels while offline"""
        # This would run in a background thread
        # and periodically check for offline duels
        pass
    
    def stop_offline_duel_simulation(self):
        """Stop simulating duels while offline"""
        pass
