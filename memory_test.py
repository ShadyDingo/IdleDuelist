#!/usr/bin/env python3
"""
Memory usage test for Fly.io deployment
"""

import psutil
import sys
import os

def check_memory_usage():
    """Check current memory usage"""
    print("🧠 Memory Usage Analysis")
    print("=" * 40)
    
    # Get memory info
    memory = psutil.virtual_memory()
    print(f"Total Memory: {memory.total / (1024**3):.2f} GB")
    print(f"Available Memory: {memory.available / (1024**3):.2f} GB")
    print(f"Used Memory: {memory.used / (1024**3):.2f} GB")
    print(f"Memory Usage: {memory.percent}%")
    
    # Check if we're on Fly.io
    if os.environ.get('FLY_REGION'):
        print(f"\n🌍 Running on Fly.io in region: {os.environ.get('FLY_REGION')}")
        print(f"Machine ID: {os.environ.get('FLY_MACHINE_ID', 'Unknown')}")
    else:
        print("\n💻 Running locally")
    
    # Test imports
    print("\n📦 Testing imports:")
    try:
        import fastapi
        print("✅ FastAPI imported")
    except Exception as e:
        print(f"❌ FastAPI failed: {e}")
    
    try:
        import uvicorn
        print("✅ Uvicorn imported")
    except Exception as e:
        print(f"❌ Uvicorn failed: {e}")
    
    try:
        import sqlite3
        print("✅ SQLite3 imported")
    except Exception as e:
        print(f"❌ SQLite3 failed: {e}")
    
    # Test app creation
    print("\n🚀 Testing app creation:")
    try:
        from free_deployment import app
        print("✅ App created successfully")
        
        # Check if we can start the server (but don't actually start it)
        print("✅ Server should be able to start")
        
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Memory after imports
    memory_after = psutil.virtual_memory()
    print(f"\n📊 Memory after imports: {memory_after.used / (1024**3):.2f} GB")
    print(f"Memory increase: {(memory_after.used - memory.used) / (1024**2):.2f} MB")

if __name__ == "__main__":
    check_memory_usage()
