#!/usr/bin/env python3
"""
Startup script for Fly.io deployment
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

# Import and run the server
if __name__ == "__main__":
    try:
        import uvicorn
        from free_deployment import app
        
        # Get port from environment or default to 8000
        port = int(os.environ.get("PORT", 8000))
        
        print(f"Starting server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
        
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)
