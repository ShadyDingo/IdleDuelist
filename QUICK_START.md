# Quick Start Guide - IdleDuelist

## Running the Game Locally

### Option 1: Using the Startup Script (Recommended)

**Windows:**
```bash
start_server.bat
```

**Mac/Linux:**
```bash
python start_server.py
```

### Option 2: Manual Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the server:**
   ```bash
   python full_web_server_simple.py
   ```

3. **Open your browser:**
   Navigate to: **http://localhost:8000**

## What to Expect

- The server will start on `http://localhost:8000`
- The database will be automatically initialized on first run
- You can create an account and start playing immediately
- All game assets are served from the `assets/` directory

## Troubleshooting

### Port Already in Use
If port 8000 is already in use, you can change it by setting the `PORT` environment variable:
```bash
set PORT=8001
python full_web_server_simple.py
```

### Missing Dependencies
If you get import errors, install dependencies:
```bash
pip install -r requirements.txt
```

### Database Issues
The database (`web_duelist.db`) will be created automatically. If you need to reset it, delete the file and restart the server.

## Game Features

- Create an account and customize your character
- Choose from 3 factions with unique abilities
- Equip weapons and armor with different rarities
- Battle other players in turn-based combat
- Participate in tournaments and climb the leaderboard

Enjoy playing IdleDuelist! 🎮

