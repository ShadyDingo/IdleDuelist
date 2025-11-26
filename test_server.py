#!/usr/bin/env python3
"""Quick test to verify server can start"""
import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    from full_web_server_simple import app, init_database
    import uvicorn
    
    print("Initializing database...")
    init_database()
    print("Database ready!")
    print("\nServer is ready to start!")
    print("Run: python start_server.py")
    print("Or: python full_web_server_simple.py")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

