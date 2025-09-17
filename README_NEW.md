# Idle Duelist - Complete Rewrite

## Overview
A turn-based combat game with equipment management, ranking system, and matchmaking. This is a complete rewrite from scratch with all the requested features.

## Features

### Main Menu
- **Loadout**: Manage equipment and edit username
- **Duel**: Start a match against another player
- **Leaderboard**: View top 10 players and your current ranking

### Loadout System
- Equip different armor pieces (helmet, chest, gloves, pants, boots)
- Choose mainhand and offhand weapons
- Edit your username (random username assigned on first play)
- Real-time stat calculation (speed, defense, damage)

### Combat System
- Turn-based combat with speed determining turn order
- Higher speed = goes first
- Attack or Defend actions each turn
- Combat log showing all actions
- Victory/defeat tracking with rating updates

### Ranking & Matchmaking
- ELO rating system (starts at 1000)
- Matchmaking based on similar ratings (±200 points)
- Bot opponents when no suitable players found
- Win/loss tracking

### Leaderboard
- Top 10 players by rating
- Shows rank, username, rating, and win/loss record
- Current player position highlighted in yellow
- Refresh button to update rankings

## Equipment Stats

### Armor Types
- **Cloth**: High speed, low defense (lightweight)
- **Leather**: Balanced speed and defense
- **Metal**: Low speed, high defense (heavy)

### Weapons
- Various damage values from 8-20
- Mainhand and offhand slots
- Shield available as offhand option

## How to Play

1. **First Time**: You'll get a random username and basic cloth equipment
2. **Loadout**: Customize your equipment to optimize speed vs defense
3. **Duel**: Click Duel to find an opponent and fight
4. **Strategy**: Balance speed (turn order) vs defense (survivability) vs damage (offense)
5. **Climb**: Win matches to increase your rating and climb the leaderboard

## File Structure
- `idle_duelist.py` - Main game application
- `player_data.json` - Player data persistence (created automatically)
- `assets/` - Equipment images (kept from previous version)

## Running the Game
```bash
python idle_duelist.py
```

## Technical Details
- Built with Kivy for cross-platform UI
- JSON-based data persistence
- ELO rating system for fair matchmaking
- Modular design with separate screens for each feature
- Automatic bot generation for opponents when needed

The game is now completely functional with all requested features implemented from scratch!






