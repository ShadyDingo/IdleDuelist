#!/usr/bin/env python3
"""
Railway Deployment Entry Point
This file exists to satisfy Railway's deployment requirements
and redirects to the actual application.
"""

import os
import sys
import socket
import subprocess
from contextlib import closing


def _is_running_on_railway() -> bool:
    """Best-effort detection for Railway environment."""
    return any(key.startswith("RAILWAY_") for key in os.environ.keys())


def _is_port_available(port: int) -> bool:
    """Return True if no service is currently listening on the given port."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(0.25)
        try:
            result = sock.connect_ex(("127.0.0.1", port))
        except OSError:
            return True
    return result != 0


def _find_fallback_port(avoid: set[int] | None = None) -> int:
    """Find a fallback port for local development."""
    avoid = avoid or set()
    for candidate in (8000, 8080, 3000):
        if candidate in avoid:
            continue
        if _is_port_available(candidate):
            return candidate
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("0.0.0.0", 0))
        return sock.getsockname()[1]


def resolve_port() -> str:
    """Determine which port the server should bind to."""
    raw_port = os.environ.get('PORT')
    default_port = 8000
    port = default_port

    if raw_port:
        try:
            port = int(raw_port)
        except ValueError:
            print(f"⚠️  Invalid PORT value '{raw_port}'. Falling back to {default_port}.", flush=True)
            port = default_port

    if _is_port_available(port):
        return str(port)

    if _is_running_on_railway():
        print(f"❌ The provided Railway port {port} is already in use. Please check the service configuration.", flush=True)
        sys.exit(1)

    print(f"⚠️  Port {port} is busy. Searching for an open port for local testing…", flush=True)
    fallback_port = _find_fallback_port({port})
    print(f"🔄 Using fallback port {fallback_port} for this session. Set PORT explicitly to override.", flush=True)
    return str(fallback_port)


def main():
    """Main entry point for Railway deployment"""
    print("🚀 Starting IdleDuelist deployment...", flush=True)
    print(f"📁 Current directory: {os.getcwd()}", flush=True)
    print(f"📋 Files in directory: {os.listdir('.')}", flush=True)
    
    # Check if our main application file exists
    if os.path.exists('full_web_server_simple.py'):
        print("✅ Found full_web_server_simple.py - starting application...", flush=True)
        
        # Determine the port we should bind to
        port = resolve_port()
        
        # Start the actual application
        cmd = [
            sys.executable, '-m', 'uvicorn', 
            'full_web_server_simple:app',
            '--host', '0.0.0.0',
            '--port', port
        ]
        
        print(f"🎯 Running command: {' '.join(cmd)}", flush=True)
        subprocess.run(cmd)
    else:
        print("❌ full_web_server_simple.py not found!")
        print("📋 Available files:")
        for file in os.listdir('.'):
            print(f"  - {file}")
        sys.exit(1)

if __name__ == "__main__":
    main()
