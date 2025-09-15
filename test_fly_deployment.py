#!/usr/bin/env python3
"""
Test script to verify Fly.io deployment will work
"""

import requests
import json
import time

def test_local_server():
    """Test the local server first"""
    print("🧪 Testing local server...")
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        # Test stats endpoint
        response = requests.get("http://localhost:8000/stats", timeout=5)
        if response.status_code == 200:
            print("✅ Stats endpoint working")
        else:
            print(f"❌ Stats endpoint failed: {response.status_code}")
            return False
        
        # Test player registration
        player_data = {
            "id": "test_player_fly",
            "username": "FlyTestPlayer",
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
            "http://localhost:8000/players/register",
            json=player_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Player registration working")
        else:
            print(f"❌ Player registration failed: {response.status_code}")
            return False
        
        # Test getting player data
        response = requests.get(
            "http://localhost:8000/players/test_player_fly",
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Player data retrieval working")
        else:
            print(f"❌ Player data retrieval failed: {response.status_code}")
            return False
        
        # Test duel request
        response = requests.post(
            "http://localhost:8000/duels/request",
            json={"player_id": "test_player_fly", "rating_range": 100},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Duel request working")
        else:
            print(f"❌ Duel request failed: {response.status_code}")
            return False
        
        print("\n🎉 All tests passed! Your server is ready for Fly.io deployment.")
        return True
        
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

def test_fly_deployment():
    """Test the deployed Fly.io app"""
    print("\n🌐 Testing Fly.io deployment...")
    
    # You'll need to replace this with your actual Fly.io URL
    fly_url = "https://your-app-name.fly.dev"
    
    try:
        # Test health endpoint
        response = requests.get(f"{fly_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Fly.io health endpoint working")
        else:
            print(f"❌ Fly.io health endpoint failed: {response.status_code}")
            return False
        
        # Test stats endpoint
        response = requests.get(f"{fly_url}/stats", timeout=10)
        if response.status_code == 200:
            print("✅ Fly.io stats endpoint working")
        else:
            print(f"❌ Fly.io stats endpoint failed: {response.status_code}")
            return False
        
        print("\n🎉 Fly.io deployment working! Your app is live.")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Fly.io deployment: {e}")
        print("Make sure to replace 'your-app-name' with your actual Fly.io URL")
        return False

def main():
    """Run all tests"""
    print("🚀 IdleDuelist Fly.io Deployment Test")
    print("=" * 50)
    
    # Test local server first
    if not test_local_server():
        print("\n❌ Local server tests failed. Fix issues before deploying to Fly.io.")
        return
    
    print("\n📋 Next steps:")
    print("1. Go to https://fly.io and sign up")
    print("2. Deploy your app using the web interface")
    print("3. Get your live URL")
    print("4. Update the fly_url in this script")
    print("5. Run this script again to test your deployment")
    
    # Uncomment this line after you deploy to Fly.io
    # test_fly_deployment()

if __name__ == "__main__":
    main()
