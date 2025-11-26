#!/usr/bin/env python3
"""
Diagnostic script to check if everything is set up correctly
"""

import sys
import os

def check_python():
    """Check Python version"""
    print("🐍 Python Version:")
    print(f"   {sys.version}")
    print(f"   Executable: {sys.executable}")
    return True

def check_files():
    """Check if required files exist"""
    print("\n📁 Required Files:")
    files_to_check = [
        'full_web_server_simple.py',
        'static/full_game.html',
        'assets',
        'requirements.txt'
    ]
    
    all_exist = True
    for file_path in files_to_check:
        exists = os.path.exists(file_path)
        status = "✅" if exists else "❌"
        print(f"   {status} {file_path}")
        if not exists:
            all_exist = False
    
    return all_exist

def check_dependencies():
    """Check if dependencies are installed"""
    print("\n📦 Dependencies:")
    required = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'pydantic': 'Pydantic',
        'bcrypt': 'bcrypt'
    }
    
    all_installed = True
    for module, name in required.items():
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} - NOT INSTALLED")
            all_installed = False
    
    return all_installed

def main():
    print("=" * 60)
    print("🔍 IdleDuelist Setup Diagnostic")
    print("=" * 60)
    
    # Check Python
    try:
        check_python()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Check files
    files_ok = check_files()
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    print("\n" + "=" * 60)
    if files_ok and deps_ok:
        print("✅ All checks passed! You're ready to run the server.")
        print("\nTo start the server, run:")
        print("   python start_server.py")
    else:
        print("⚠️  Some issues detected:")
        if not files_ok:
            print("   - Missing required files")
        if not deps_ok:
            print("   - Missing dependencies. Run: pip install -r requirements.txt")
    print("=" * 60)
    
    return files_ok and deps_ok

if __name__ == "__main__":
    main()

