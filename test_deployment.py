#!/usr/bin/env python3
"""
Test deployment script to verify Railway is working
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="IdleDuelist Test", version="2.0")

@app.get("/")
async def root():
    return JSONResponse({
        "message": "IdleDuelist Full Game Test",
        "version": "2.0",
        "status": "Full game features should be here!"
    })

@app.get("/health")
async def health():
    return JSONResponse({
        "status": "healthy",
        "version": "2.0",
        "full_game": True,
        "message": "This should show the new version!"
    })

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8001))
    print(f"Starting test server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
