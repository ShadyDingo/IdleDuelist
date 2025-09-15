#!/usr/bin/env python3
"""
Railway Deployment Entry Point
This file exists to satisfy Railway's deployment requirements
and redirects to the actual application.
"""

import os
import sys
import subprocess

def main():
    """Main entry point for Railway deployment"""
    print("🚀 Starting IdleDuelist deployment...")
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"📋 Files in directory: {os.listdir('.')}")
    
    # Check if our main application file exists
    if os.path.exists('full_web_server_simple.py'):
        print("✅ Found full_web_server_simple.py - starting application...")
        
        # Get port from environment
        port = os.environ.get('PORT', '8000')
        
        # Start the actual application
        cmd = [
            sys.executable, '-m', 'uvicorn', 
            'full_web_server_simple:app',
            '--host', '0.0.0.0',
            '--port', port
        ]
        
        print(f"🎯 Running command: {' '.join(cmd)}")
        subprocess.run(cmd)
    else:
        print("❌ full_web_server_simple.py not found!")
        print("📋 Available files:")
        for file in os.listdir('.'):
            print(f"  - {file}")
        sys.exit(1)

if __name__ == "__main__":
    main()
