#!/usr/bin/env python3
"""
Debug script for Fly.io deployment issues
"""

import os
import sys

def check_environment():
    """Check environment variables and setup"""
    print("🔍 Fly.io Environment Debug")
    print("=" * 50)
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check if we're in the right directory
    print(f"Current directory: {os.getcwd()}")
    
    # Check for required files
    required_files = [
        'free_deployment.py',
        'requirements_free.txt',
        'fly.toml'
    ]
    
    print("\n📁 Required files:")
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} - Found")
        else:
            print(f"❌ {file} - Missing")
    
    # Check environment variables
    print("\n🌍 Environment variables:")
    port = os.environ.get('PORT', 'Not set')
    print(f"PORT: {port}")
    
    # Check if we can import required modules
    print("\n📦 Module imports:")
    try:
        import fastapi
        print("✅ FastAPI - Available")
    except ImportError as e:
        print(f"❌ FastAPI - Error: {e}")
    
    try:
        import uvicorn
        print("✅ Uvicorn - Available")
    except ImportError as e:
        print(f"❌ Uvicorn - Error: {e}")
    
    try:
        import sqlite3
        print("✅ SQLite3 - Available")
    except ImportError as e:
        print(f"❌ SQLite3 - Error: {e}")

def test_server_start():
    """Test if the server can start"""
    print("\n🚀 Testing server startup:")
    
    try:
        # Try to import the server
        import free_deployment
        print("✅ Server module imported successfully")
        
        # Check if the app is defined
        if hasattr(free_deployment, 'app'):
            print("✅ FastAPI app defined")
        else:
            print("❌ FastAPI app not found")
        
        # Check database initialization
        try:
            free_deployment.init_database()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
        
    except Exception as e:
        print(f"❌ Server import failed: {e}")

def main():
    """Run all diagnostic checks"""
    check_environment()
    test_server_start()
    
    print("\n🔧 Common fixes for 502 errors:")
    print("1. Check that PORT environment variable is set")
    print("2. Verify all dependencies are in requirements_free.txt")
    print("3. Make sure free_deployment.py is in the root directory")
    print("4. Check Fly.io logs for specific error messages")
    print("5. Ensure the app starts on the correct port")

if __name__ == "__main__":
    main()
