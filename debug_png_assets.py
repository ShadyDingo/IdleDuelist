#!/usr/bin/env python3
"""
Comprehensive PNG asset debugging script
"""

import requests
import json
import os

def test_asset_endpoints():
    """Test all asset-related endpoints"""
    base_url = "https://idleduelist.up.railway.app"
    
    print("🔍 Testing PNG Asset Endpoints")
    print("=" * 50)
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Test 2: Test asset listing
    try:
        response = requests.get(f"{base_url}/test-assets", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Asset endpoint working: {data.get('message', 'No message')}")
            print(f"📊 Found {data.get('asset_count', 0)} assets")
            if 'sample_assets' in data:
                print("📝 Sample assets:")
                for asset in data['sample_assets'][:3]:
                    print(f"  - {asset}")
        else:
            print(f"❌ Asset endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Asset endpoint error: {e}")
    
    # Test 3: Test HTML rendering
    try:
        response = requests.get(f"{base_url}/test-html", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ HTML test endpoint working")
            print(f"📝 Ability icon: {data.get('ability_icon', 'None')}")
            print(f"📝 Weapon icon: {data.get('weapon_icon', 'None')}")
            print(f"📝 Raw HTML: {data.get('raw_html', 'None')}")
        else:
            print(f"❌ HTML test endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ HTML test endpoint error: {e}")
    
    # Test 4: Test combat log
    try:
        response = requests.get(f"{base_url}/test-combat-log", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Combat log test endpoint working")
            print(f"📝 Ability log: {data.get('ability_log', [])}")
            print(f"📝 Attack log: {data.get('attack_log', [])}")
            print(f"📝 Ability icon path: {data.get('ability_icon_path', 'None')}")
            print(f"📝 Weapon icon path: {data.get('weapon_icon_path', 'None')}")
        else:
            print(f"❌ Combat log test endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Combat log test endpoint error: {e}")
    
    # Test 5: Test direct asset access
    test_assets = [
        "/assets/abilities/ability_divine_strike.PNG",
        "/assets/abilities/ability_divine_strike.png", 
        "/assets/weapons/weapon_sword.PNG",
        "/assets/weapons/weapon_sword.png"
    ]
    
    print("\n🔍 Testing Direct Asset Access")
    print("-" * 30)
    
    for asset_path in test_assets:
        try:
            response = requests.get(f"{base_url}{asset_path}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {asset_path} - Accessible ({len(response.content)} bytes)")
            elif response.status_code == 404:
                print(f"❌ {asset_path} - Not found")
            else:
                print(f"⚠️ {asset_path} - Status {response.status_code}")
        except Exception as e:
            print(f"❌ {asset_path} - Error: {e}")

def test_local_assets():
    """Test local asset files"""
    print("\n🔍 Testing Local Asset Files")
    print("-" * 30)
    
    asset_dirs = [
        "assets/abilities",
        "assets/weapons", 
        "assets/armor",
        "assets/factions"
    ]
    
    for asset_dir in asset_dirs:
        if os.path.exists(asset_dir):
            files = [f for f in os.listdir(asset_dir) if f.endswith(('.png', '.PNG'))]
            print(f"📁 {asset_dir}: {len(files)} PNG files")
            if files:
                for file in files[:3]:  # Show first 3 files
                    print(f"  - {file}")
        else:
            print(f"❌ {asset_dir}: Directory not found")

if __name__ == "__main__":
    print("🎮 IdleDuelist PNG Asset Debugger")
    print("=" * 50)
    
    test_local_assets()
    test_asset_endpoints()
    
    print("\n✅ Debugging complete!")
