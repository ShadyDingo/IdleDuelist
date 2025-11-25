# UI Improvements: Persistent Chat, Online Count, Skills Tooltips, and Data Persistence

## Overview

This plan implements UI improvements for better user experience: persistent global chat, online player count, collapsible skill descriptions, and fixes for data persistence on Railway.

## Changes Required

### 1. Restructure Global Chat to be Persistent (`static/game.html`)

**Remove Chat tab from navigation:**
- Remove "Chat" button from nav-bar (line ~1145)
- Remove `chat-screen` div (lines ~1355-1362)

**Add persistent chat container:**
- Create fixed-position chat container at bottom 1/6th of viewport
- Position: `position: fixed; bottom: 0; left: 0; right: 0; height: 16.67vh;`
- Structure: chat messages area (scrollable) + input bar at bottom
- Ensure chat is visible on all screens (Character, Skills, Inventory, Combat, Store, Leaderboard)
- Adjust main content area to account for chat space (add bottom padding/margin)

**Location:** 
- Remove from navigation: `static/game.html` line ~1145
- Remove chat screen: `static/game.html` lines ~1355-1362
- Add persistent chat container: After closing `</div>` of screen-container, before closing `</div>` of container

### 2. Add Online Player Count Display (`static/game.html` and `server.py`)

**Frontend (`static/game.html`):**
- Add "Total Players Online: X" display in game-header
- Position next to character name/level info
- Update every 30 seconds via polling

**Backend (`server.py`):**
- Create endpoint `/api/players/online-count` that:
  - Tracks active players (users with valid JWT tokens issued in last 5 minutes)
  - Returns count of unique user_ids from recent tokens
  - Use in-memory tracking or Redis if available
- Store active user sessions with timestamp when tokens are created/refreshed

**Location:**
- Frontend: `static/game.html` game-header section (~line 1119)
- Backend: `server.py` add new endpoint after chat endpoints (~line 3400)

### 3. Convert Skills Descriptions to Toggleable Popups (`static/game.html`)

**Modify `updateSkillsScreen()` function:**
- Remove inline description paragraph from skill panels
- Add "More Info" button next to each skill name
- Create modal popup component for skill descriptions
- On "More Info" click: show modal with full description from `getStatDescription()`
- Modal should have close button and click-outside-to-close functionality
- Only one modal open at a time

**Location:** `static/game.html` function `updateSkillsScreen()` (~line 2085) and `getStatDescription()` (~line 2119)

### 4. Fix Data Persistence on Railway (`server.py`)

**Add diagnostic logging:**
- Log database connection type (SQLite vs PostgreSQL) on startup
- Log DATABASE_URL presence and format (without exposing password)
- Add warning if using SQLite in production environment

**Enhance health check endpoint:**
- Update `/health` endpoint to report:
  - Database type (SQLite/PostgreSQL)
  - Database connection status
  - DATABASE_URL configured (yes/no, without value)
  - Redis connection status

**Add startup verification:**
- In `init_database()`, verify PostgreSQL connection works
- Print clear error if PostgreSQL connection fails but DATABASE_URL is set
- Add instructions in error message for Railway PostgreSQL setup

**Location:**
- Logging: `server.py` startup section and `get_db_connection()` function (~line 60)
- Health check: `server.py` `/health` endpoint (find existing or create)
- Verification: `server.py` `init_database()` function (~line 188)

## Implementation Order

1. Fix data persistence diagnostics and logging
2. Restructure chat to be persistent (remove tab, add fixed container)
3. Add online player count (backend endpoint + frontend display)
4. Convert skills descriptions to toggleable popups

## Testing Considerations

- Verify chat is visible on all screens
- Test chat doesn't overlap with content
- Verify online count updates correctly
- Test skills modal opens/closes properly
- Verify database type is logged correctly on Railway
- Test health check endpoint reports correct database status

