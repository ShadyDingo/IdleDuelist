#!/usr/bin/env python3
"""
Simple startup script for IdleDuelist web server
Run this to start the game on localhost
"""

import sys
import subprocess
import os

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass  # If it fails, continue anyway

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['fastapi', 'uvicorn', 'pydantic', 'bcrypt']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print("⚠️  Missing dependencies detected!")
        print(f"   Missing: {', '.join(missing)}")
        print("\n📦 Installing dependencies...")
        print("   (Using pre-built packages to avoid Rust compilation)")
        
        # Try installing with --only-binary to use pre-built wheels (avoids Rust)
        try:
            print("   Attempting installation with pre-built packages...")
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', 
                '--upgrade', 'pip',
                '--only-binary', ':all:',
                '-r', 'requirements.txt'
            ])
            print("✅ Dependencies installed successfully!")
        except subprocess.CalledProcessError:
            print("   First attempt failed, trying alternative method...")
            try:
                # Try without --only-binary but with --prefer-binary
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install',
                    '--upgrade', 'pip',
                    '--prefer-binary',
                    '-r', 'requirements.txt'
                ])
                print("✅ Dependencies installed successfully!")
            except subprocess.CalledProcessError:
                print("   Alternative method failed, trying individual packages...")
                try:
                    # Install bcrypt first with special flag
                    print("   Installing bcrypt...")
                    subprocess.check_call([
                        sys.executable, '-m', 'pip', 'install',
                        'bcrypt', '--no-build-isolation'
                    ])
                    # Install remaining packages with latest versions (better Python 3.14 support)
                    print("   Installing remaining packages...")
                    subprocess.check_call([
                        sys.executable, '-m', 'pip', 'install',
                        'fastapi', 'uvicorn[standard]', 'pydantic', 
                        'python-multipart', 'pytz', '--upgrade'
                    ])
                    print("✅ Dependencies installed successfully!")
                except subprocess.CalledProcessError:
                    print("\n❌ Failed to install dependencies automatically.")
                    print("\n💡 Try installing manually:")
                    print("   1. First, upgrade pip:")
                    print("      python -m pip install --upgrade pip")
                    print("   2. Then install bcrypt separately:")
                    print("      python -m pip install bcrypt --no-build-isolation")
                    print("   3. Finally install the rest (using latest versions for Python 3.14):")
                    print("      python -m pip install fastapi uvicorn[standard] pydantic python-multipart pytz --upgrade")
                    print("\n   Or install Rust from https://rustup.rs/ if you want to build from source.")
                    return False
    
    return True

def main():
    """Start the web server"""
    print("🎮 Starting IdleDuelist Web Server...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check if static files exist
    if not os.path.exists('static/game.html'):
        print("❌ Error: static/game.html not found!")
        sys.exit(1)
    
    if not os.path.exists('static/index.html'):
        print("❌ Error: static/index.html not found!")
        sys.exit(1)
    
    if not os.path.exists('assets'):
        print("⚠️  Warning: assets directory not found!")
    
    print("\n✅ All checks passed!")
    print("\n🌐 Starting server on http://localhost:8000")
    print("📝 Press Ctrl+C to stop the server\n")
    print("=" * 50)
    
    # Import and run the server
    try:
        import uvicorn
        import server
        
        # Database is initialized on startup event in server.py
        print("🔧 Server starting...")
        
        # Start server
        uvicorn.run(server.app, host="127.0.0.1", port=8000, log_level="info")
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

