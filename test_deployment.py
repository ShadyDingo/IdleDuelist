#!/usr/bin/env python3
"""
Railway Deployment Test Script
Tests all critical functionality on the deployed application
"""

import requests
import json
import time
import sys

def test_deployment(base_url):
    """Test all critical functionality on deployed app"""
    print(f"🧪 Testing deployment at: {base_url}")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Health Check
    tests_total += 1
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check: {data.get('status', 'Unknown')}")
            print(f"   Players: {data.get('players', 'Unknown')}")
            tests_passed += 1
        else:
            print(f"❌ Health Check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health Check error: {e}")
    
    # Test 2: Leaderboard
    tests_total += 1
    try:
        response = requests.get(f"{base_url}/leaderboard", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and len(data.get('leaderboard', [])) > 0:
                print(f"✅ Leaderboard: {len(data.get('leaderboard', []))} players")
                tests_passed += 1
            else:
                print(f"❌ Leaderboard: No players found")
        else:
            print(f"❌ Leaderboard failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Leaderboard error: {e}")
    
    # Test 3: Character Creation
    tests_total += 1
    try:
        test_username = f"DeployTest_{int(time.time())}"
        player_data = {
            "username": test_username,
            "password": "testpass123",
            "faction": "order_of_the_silver_crusade"
        }
        
        response = requests.post(f"{base_url}/create-player", json=player_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Character Creation: {test_username}")
                tests_passed += 1
                
                # Test 4: Loadout Update
                tests_total += 1
                loadout_data = {
                    "username": test_username,
                    "equipment": {
                        "helmet": {"name": "Leather Helmet", "slot": "helmet", "rarity": "rare"},
                        "armor": {"name": "Leather Armor", "slot": "armor", "rarity": "rare"}
                    },
                    "weapon1": "sword",
                    "weapon2": "shield",
                    "armor_type": "leather"
                }
                
                response = requests.post(f"{base_url}/update-loadout", json=loadout_data, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        print(f"✅ Loadout Update: Equipment saved")
                        tests_passed += 1
                    else:
                        print(f"❌ Loadout Update: {data.get('error')}")
                else:
                    print(f"❌ Loadout Update failed: {response.status_code}")
            else:
                print(f"❌ Character Creation: {data.get('error')}")
        else:
            print(f"❌ Character Creation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Character Creation error: {e}")
    
    # Test 5: Duel System
    tests_total += 1
    try:
        duel_data = {
            "username": test_username,
            "opponent_type": "bot"
        }
        
        response = requests.post(f"{base_url}/duel", json=duel_data, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Duel System: Combat completed")
                tests_passed += 1
            else:
                print(f"❌ Duel System: {data.get('error')}")
        else:
            print(f"❌ Duel System failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Duel System error: {e}")
    
    # Test 6: Static Files
    tests_total += 1
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            if "IdleDuelist" in response.text:
                print(f"✅ Static Files: HTML served correctly")
                tests_passed += 1
            else:
                print(f"❌ Static Files: HTML content incorrect")
        else:
            print(f"❌ Static Files failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Static Files error: {e}")
    
    # Summary
    print("=" * 60)
    print(f"📊 Test Results: {tests_passed}/{tests_total} tests passed")
    
    if tests_passed == tests_total:
        print("🎉 All tests passed! Deployment is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the deployment logs.")
        return False

def main():
    """Main function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        # Default Railway URL - replace with your actual URL
        base_url = "https://idleduelist-production.up.railway.app"
    
    print("🚀 Railway Deployment Test Suite")
    print(f"🎯 Testing: {base_url}")
    print()
    
    success = test_deployment(base_url)
    
    if success:
        print("\n✅ Deployment verification complete!")
        print("🔗 Your Railway deployment is working correctly.")
    else:
        print("\n❌ Deployment verification failed!")
        print("🔍 Check Railway logs for issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()

