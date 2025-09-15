#!/usr/bin/env python3
"""
Test script to verify the app can start properly
"""

import os
import sys

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import fastapi
        print("✅ FastAPI imported")
    except Exception as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import uvicorn
        print("✅ Uvicorn imported")
    except Exception as e:
        print(f"❌ Uvicorn import failed: {e}")
        return False
    
    try:
        import sqlite3
        print("✅ SQLite3 imported")
    except Exception as e:
        print(f"❌ SQLite3 import failed: {e}")
        return False
    
    return True

def test_app_creation():
    """Test if the app can be created"""
    print("\nTesting app creation...")
    
    try:
        from free_deployment import app
        print("✅ App created successfully")
        return True
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_init():
    """Test if database can be initialized"""
    print("\nTesting database initialization...")
    
    try:
        from free_deployment import init_database
        init_database()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 IdleDuelist Startup Test")
    print("=" * 40)
    
    # Set environment variables
    os.environ['PORT'] = '8000'
    os.environ['FLY_REGION'] = 'test'
    
    success = True
    
    success &= test_imports()
    success &= test_app_creation()
    success &= test_database_init()
    
    if success:
        print("\n🎉 All tests passed! App should start successfully.")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
    
    return success

if __name__ == "__main__":
    main()
