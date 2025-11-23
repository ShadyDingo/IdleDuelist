# Menu System Overview - IdleDuelist

## Current Implementation Status

### 🎮 Desktop Version (idle_duelist.py - Kivy-based)

#### **Main Menu** ✅ Implemented
Located in: `MainMenu` class (line 1031)

**Current Buttons:**
1. **Loadout** - Equipment management (weapons, armor)
2. **Faction** - Choose between 3 factions (Order/Shadow/Wilderness)
3. **Abilities** - Select 5 abilities from faction-specific pool
4. **Duel** - Start combat immediately
5. **Leaderboard** - View player rankings
6. **Audio Controls** - Volume slider and mute button

#### **Character Management Screens** ✅ Implemented

**LoadoutScreen** (line 1189):
- Weapon selection (Primary & Secondary)
- Armor piece selection (Head, Chest, Legs, Hands, Feet)
- Visual equipment display
- Equipment stats preview

**FactionScreen** (line 1830):
- Three faction choices with unique bonuses
- Faction-specific abilities display
- Passive ability information
- Faction change confirmation

**AbilitiesScreen** (line 1986):
- 5 ability slots (player can only bring 4 into combat based on your requirements)
- Ability selection from faction pool
- Visual ability icons
- Cooldown and description display
- Ability slot management (assign/clear)

### 🌐 Web Version (index.html + full_web_server_simple.py)

#### **Login/Registration** ✅ Implemented
- Login form for existing players
- Character creation form
- LocalStorage persistence

#### **Character Creation** ✅ Implemented
**Options:**
- Character name
- Faction selection (auto-assigns 4 abilities)
- Armor type (Cloth/Leather/Metal)
- Primary weapon
- Secondary weapon

#### **Game Interface** ✅ Implemented
**Stats Display:**
- Rating, Wins, Losses
- Damage, Speed, Crit Chance

**Navigation Buttons:**
- ⚔️ Find Duel
- 🏆 Leaderboard
- 👤 Character Info (view-only)
- 🚪 Logout

**Duel Log:**
- Real-time combat results
- Damage dealt/received
- Victory/defeat notifications
- Rating changes

---

## 🚨 Current Gaps & Missing Features

### ❌ **Skill Point System** (Database exists, NO UI)
**Database Schema Present:**
- `player_progression` table has `skill_points` column
- `player_skills` table exists for tracking investments
- Players earn 2 skill points per level
- Achievements grant skill points

**MISSING:**
- ❌ No UI to view available skill points
- ❌ No UI to allocate/reallocate skill points
- ❌ No stat allocation screen
- ❌ No respec functionality

### ❌ **Matchmaking Queue System** (Mentioned but not fully implemented)
**What exists:**
- `matchmaking_queue` table in database
- `/duel` endpoint creates immediate matches
- Randomly selects opponents from existing players or creates bot

**MISSING:**
- ❌ No real queue system (instant matching only)
- ❌ No "searching for opponent" state
- ❌ No queue position tracking
- ❌ No ability to cancel queue
- ❌ No preference for real players vs bots

### ⚠️ **Web Version Limitations**
**Missing from web version:**
- ❌ Equipment management (locked to creation choices)
- ❌ Ability selection/customization
- ❌ Faction switching
- ❌ Skill point allocation
- ❌ Detailed character management

### ⚠️ **Ability Selection Confusion**
**Current System:**
- Desktop: 5 ability slots
- **Your requirement:** Players can only bring 4 abilities into duels
- Web: Auto-assigns 4 abilities at creation

**Needs Clarification:**
- Should we change to 4 slots everywhere?
- Or keep 5 slots but only 4 active in combat?

---

## 📋 Recommended Improvements for Text-Based Game

### 🎯 **Priority 1: Core Menu Structure**

#### **MAIN MENU** (Refined)
```
┌─────────────────────────────────┐
│     ⚔️  IDLE DUELIST  ⚔️        │
│                                 │
│  [⚔️  DUEL]                     │ ← Primary action
│  [👤  CHARACTER]                │ ← All character management
│  [🏆  LEADERBOARD]              │
│  [⚙️  SETTINGS]                 │
│  [🚪  LOGOUT]                   │
└─────────────────────────────────┘
```

#### **CHARACTER MENU** (Sub-menu)
```
┌─────────────────────────────────┐
│       CHARACTER PROFILE         │
│                                 │
│  Name: [Player Name]            │
│  Level: 15 | XP: 1250/2000     │
│  Rating: 1450                   │
│                                 │
│  [📊 STATS & SKILLS]            │ ← NEW: Skill point allocation
│  [⚔️  EQUIPMENT]                │ ← Existing Loadout
│  [✨ ABILITIES]                 │ ← Existing Abilities (4 slots)
│  [🎭 FACTION]                   │ ← Existing Faction
│  [🏆 ACHIEVEMENTS]              │ ← NEW: Achievement tracking
│                                 │
│  [← BACK]                       │
└─────────────────────────────────┘
```

#### **STATS & SKILLS MENU** (NEW - Priority)
```
┌─────────────────────────────────┐
│       STATS & SKILLS            │
│                                 │
│  Available Skill Points: 15     │
│                                 │
│  ⚔️  Attack Power:  45  [+]     │
│  🛡️  Defense:      32  [+]      │
│  ⚡ Speed:        28  [+]      │
│  💚 Health:       150  [+]      │
│  ✨ Spell Power:  38  [+]      │
│  🎯 Crit Chance:  15% [+]      │
│                                 │
│  [♻️  RESET ALL] [💾 SAVE]      │
│  [← BACK]                       │
└─────────────────────────────────┘
```

#### **DUEL MENU** (Enhanced Queue System)
```
┌─────────────────────────────────┐
│           DUEL ARENA            │
│                                 │
│  [⚔️  RANKED DUEL]              │ ← Queue for PvP
│  [🤖 PRACTICE (vs AI)]          │
│  [🏟️  TOURNAMENT]               │ ← If tournaments active
│                                 │
│  Recent Matches:                │
│  ✓ vs PlayerX (+20) [3m ago]   │
│  ✗ vs PlayerY (-15) [5m ago]   │
│                                 │
│  [← BACK]                       │
└─────────────────────────────────┘
```

**When in Queue:**
```
┌─────────────────────────────────┐
│      SEARCHING FOR DUEL...      │
│                                 │
│  Time in Queue: 0:15            │
│  🔄 Searching...                │
│                                 │
│  Preferences:                   │
│  ✓ Real players preferred       │
│  ✓ Similar rating (±100)        │
│                                 │
│  [❌ CANCEL QUEUE]              │
└─────────────────────────────────┘
```

---

## 🔧 Implementation Tasks

### **Phase 1: Skill Point System (HIGH PRIORITY)**
- [ ] Create Stats & Skills screen UI
- [ ] Display available skill points
- [ ] Add +/- buttons for each stat
- [ ] Implement stat allocation logic
- [ ] Add "Reset All" functionality (free or cost?)
- [ ] Update combat system to use allocated stats
- [ ] Show stat changes in real-time

### **Phase 2: Queue System (HIGH PRIORITY)**
- [ ] Create proper queue manager
- [ ] Add "Searching..." state
- [ ] Implement queue timeout (fallback to bot/loadout)
- [ ] Add queue cancellation
- [ ] Show queue time
- [ ] Prioritize real players over bots
- [ ] Add rating-based matchmaking

### **Phase 3: Character Menu Consolidation**
- [ ] Create unified Character submenu
- [ ] Move all character management under one menu
- [ ] Add achievements display
- [ ] Add character stats overview
- [ ] Improve navigation flow

### **Phase 4: Web Version Parity**
- [ ] Add equipment management to web
- [ ] Add ability selection to web
- [ ] Add skill point allocation to web
- [ ] Add faction changing to web
- [ ] Sync all features with desktop version

### **Phase 5: Polish & UX**
- [ ] Add loading states for all actions
- [ ] Add confirmation dialogs for important actions
- [ ] Add tooltips for stats/abilities
- [ ] Improve error messaging
- [ ] Add keyboard shortcuts (desktop)
- [ ] Optimize response times

---

## 💡 Design Recommendations

### **Text-Based Focus**
Since you're building text-first, here's what to prioritize:

1. **Clear hierarchy** - Main Menu → Sub-menus → Actions
2. **Minimal clicks** - 2-3 clicks max to any feature
3. **Fast response** - All actions under 200ms
4. **Clear feedback** - Immediate visual confirmation
5. **Text readability** - High contrast, clear fonts
6. **Information density** - Show relevant info without clutter

### **Button Styling (Text-Based)**
```
Primary Actions:   Large, bright colors, top position
Secondary Actions: Medium, muted colors, middle position
Dangerous Actions: Red/warning colors, confirmation required
Navigation:        Small, neutral colors, consistent position
```

### **Loading States**
```
Before: [⚔️  DUEL]
During: [⏳ SEARCHING...]
After:  [✓ MATCH FOUND!]
```

---

## 📊 Current Database Schema (Relevant to Menus)

### **player_progression** (EXISTS)
- `skill_points` - Available to spend
- `total_skill_points_earned` - Lifetime total
- `level`, `experience` - Progression tracking

### **player_skills** (EXISTS)
- `skill_points_invested` - Per skill tracking
- Ready for stat allocation system

### **matchmaking_queue** (EXISTS but UNUSED)
- Table exists but no real queue logic
- Can be used for proper queue system

### **achievements** (EXISTS)
- Achievement definitions with skill point rewards
- Player tracking in `player_achievements`
- Not displayed in UI yet

---

## ❓ Questions to Clarify

1. **Ability Slots**: Should we standardize on 4 slots everywhere?
2. **Skill Points**: Should reallocation be free or cost gold/resources?
3. **Queue Timeout**: How long before matching with bot/loadout?
4. **Queue Preferences**: Allow players to choose PvP-only or accept bots?
5. **Character Screen**: Should this be a submenu or keep separate buttons?
6. **Web vs Desktop**: Should web version have full parity with desktop?

---

## 🎯 Suggested Next Steps

For your **text-based game priority**, I recommend:

1. ✅ **Keep current main menu structure** (clean, functional)
2. 🔥 **Add Skill Point allocation UI** (data exists, UI missing)
3. 🔥 **Implement proper queue system** (requested feature)
4. ✅ **Consolidate Character menu** (better organization)
5. ⭐ **Polish existing features** (fast, snappy, responsive)

**Focus Areas:**
- ⚔️ Duel system (queue + matchmaking)
- 📊 Character management (skills + equipment + abilities)
- 🎮 Quick, responsive UI (text-based priority)

Let me know which areas you'd like me to implement or improve first!
