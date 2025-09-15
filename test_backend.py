#!/usr/bin/env python3
"""
Test script for IdleDuelist Backend Server
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_server_health():
    """Test if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Server health check: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Server health check failed: {e}")
        return False

def test_player_registration():
    """Test player registration"""
    try:
        player_data = {
            "id": "test_player_123",
            "username": "TestPlayer",
            "rating": 1000,
            "wins": 0,
            "losses": 0,
            "equipment": {
                "helmet": "cloth_helmet",
                "armor": "cloth_armor",
                "gloves": "cloth_gloves",
                "pants": "cloth_pants",
                "boots": "cloth_boots",
                "mainhand": "weapon_knife",
                "offhand": "weapon_knife"
            },
            "faction": "shadow_covenant",
            "abilities": ["shadow_strike", "vanish", "poison_blade"]
        }
        
        response = requests.post(
            f"{BASE_URL}/players/register",
            json=player_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Player registration successful")
            return True
        else:
            print(f"❌ Player registration failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Player registration error: {e}")
        return False

def test_get_player():
    """Test getting player data"""
    try:
        response = requests.get(
            f"{BASE_URL}/players/test_player_123",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Player data retrieved: {data['username']} (Rating: {data['rating']})")
            return True
        else:
            print(f"❌ Get player failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Get player error: {e}")
        return False

def test_duel_request():
    """Test duel request"""
    try:
        response = requests.post(
            f"{BASE_URL}/duels/request",
            json={"player_id": "test_player_123", "rating_range": 100},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Duel request: {data['status']}")
            return data.get("duel_id")
        else:
            print(f"❌ Duel request failed: {response.status_code}")
            return None
    
    except Exception as e:
        print(f"❌ Duel request error: {e}")
        return None

def test_get_opponents():
    """Test getting available opponents"""
    try:
        response = requests.get(
            f"{BASE_URL}/players/test_player_123/opponents",
            params={"limit": 5},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            opponents = data.get("opponents", [])
            print(f"✅ Found {len(opponents)} opponents")
            return True
        else:
            print(f"❌ Get opponents failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Get opponents error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing IdleDuelist Backend Server")
    print("=" * 50)
    
    # Test server health
    if not test_server_health():
        print("❌ Server is not running. Please start the backend server first.")
        return
    
    # Test player registration
    if not test_player_registration():
        print("❌ Player registration failed. Stopping tests.")
        return
    
    # Test getting player data
    if not test_get_player():
        print("❌ Get player failed. Stopping tests.")
        return
    
    # Test duel request
    duel_id = test_duel_request()
    if not duel_id:
        print("❌ Duel request failed. Stopping tests.")
        return
    
    # Test getting opponents
    if not test_get_opponents():
        print("❌ Get opponents failed. Stopping tests.")
        return
    
    print("\n🎉 All tests passed! Backend server is working correctly.")
    print("\n📋 Next steps:")
    print("1. Start the backend server: python backend_server.py")
    print("2. Integrate NetworkManager into your mobile app")
    print("3. Test the complete online multiplayer experience")

if __name__ == "__main__":
    main()
