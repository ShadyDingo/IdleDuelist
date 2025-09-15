#!/usr/bin/env python3
"""
Railway Deployment Script for IdleDuelist
This script helps prepare and deploy the application to Railway
"""

import os
import subprocess
import sys
import json
from pathlib import Path

def check_requirements():
    """Check if all required files exist"""
    required_files = [
        'full_web_server_simple.py',
        'requirements.txt',
        'Dockerfile',
        'railway.json',
        'Procfile',
        'static/full_game.html'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    print("✅ All required files present")
    return True

def check_database():
    """Check if database file exists and is accessible"""
    db_files = ['full_game.db', 'idle_duelist.db']
    
    for db_file in db_files:
        if Path(db_file).exists():
            print(f"✅ Database file found: {db_file}")
            return True
    
    print("⚠️  No database file found - will be created on first run")
    return True

def validate_config():
    """Validate configuration files"""
    try:
        # Check requirements.txt
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
            if 'fastapi' in requirements and 'uvicorn' in requirements:
                print("✅ Requirements.txt looks good")
            else:
                print("❌ Requirements.txt missing essential packages")
                return False
        
        # Check Dockerfile
        with open('Dockerfile', 'r') as f:
            dockerfile = f.read()
            if 'python:3.11' in dockerfile and 'full_web_server_simple' in dockerfile:
                print("✅ Dockerfile looks good")
            else:
                print("❌ Dockerfile needs updates")
                return False
        
        # Check railway.json
        with open('railway.json', 'r') as f:
            railway_config = json.load(f)
            if railway_config.get('build', {}).get('builder') == 'DOCKERFILE':
                print("✅ Railway.json looks good")
            else:
                print("❌ Railway.json needs updates")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error validating config: {e}")
        return False

def prepare_deployment():
    """Prepare files for deployment"""
    print("🚀 Preparing deployment...")
    
    # Ensure static directory exists
    Path('static').mkdir(exist_ok=True)
    
    # Check if HTML file exists
    if not Path('static/full_game.html').exists():
        print("❌ HTML file missing from static directory")
        return False
    
    print("✅ Deployment files prepared")
    return True

def test_local_server():
    """Test if the server starts locally"""
    print("🧪 Testing local server startup...")
    
    try:
        # Try to import the main module
        import full_web_server_simple
        print("✅ Server module imports successfully")
        
        # Check if database initialization works
        full_web_server_simple.init_database()
        print("✅ Database initialization works")
        
        return True
        
    except Exception as e:
        print(f"❌ Local server test failed: {e}")
        return False

def main():
    """Main deployment preparation"""
    print("🎮 IdleDuelist Railway Deployment Preparation")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("❌ Deployment preparation failed - missing files")
        return False
    
    # Check database
    if not check_database():
        print("❌ Deployment preparation failed - database issues")
        return False
    
    # Validate config
    if not validate_config():
        print("❌ Deployment preparation failed - config issues")
        return False
    
    # Prepare deployment
    if not prepare_deployment():
        print("❌ Deployment preparation failed - preparation issues")
        return False
    
    # Test local server
    if not test_local_server():
        print("❌ Deployment preparation failed - server test failed")
        return False
    
    print("\n🎉 Deployment preparation completed successfully!")
    print("\n📋 Next steps:")
    print("1. Commit your changes: git add . && git commit -m 'Fix deployment issues'")
    print("2. Push to Railway: git push railway main")
    print("3. Monitor deployment in Railway dashboard")
    print("4. Test the deployed application")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
