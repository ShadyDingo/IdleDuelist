# IdleDuelist - New Stat System Implementation Guide

## 🎉 What We've Accomplished

### ✅ Phase 1: Design & Planning (COMPLETE)

**1. Created New 6-Stat System**
- **Might** - Physical power, HP, armor penetration, parry
- **Finesse** - Crit chance, dodge, attack speed, turn frequency
- **Fortitude** - HP tank, defense, regen, status resistance
- **Arcana** - Spell power, mana, ability damage
- **Insight** - Crit multiplier, cooldown reduction, accuracy
- **Presence** - Lifesteal, faction power, debuff strength, healing

**2. Designed Leveling System (1-100)**
- 3 stat points per level = 300 total points at max level
- Checkpoint system at levels 25, 50, 75, 100
- Balanced XP curve: 
  - Level 25: ~2 months casual play
  - Level 50: ~1 year casual play
  - Level 75: ~3 years casual play
  - Level 100: ~7 years casual (1.6 years hardcore)

**3. Created Build Archetypes**
- 10+ viable build paths documented
- Pure builds (300 in one stat)
- Hybrid builds (150/150, 100/100/100)
- Balanced builds (50 across all)

**4. Designed Breakpoint System**
- 4 breakpoints per stat (at 50, 100, 200, 300 points)
- Each breakpoint unlocks powerful passive effects
- Examples:
  - Might 100: 10% chance to stun on hit
  - Finesse 300: First attack each turn is guaranteed crit
  - Fortitude 300: Survive lethal blow once per duel

### ✅ Phase 2: Database & Backend (COMPLETE)

**1. Database Migration**
- Added 11 new columns to `players` table:
  - `might`, `finesse`, `fortitude`, `arcana`, `insight`, `presence`
  - `level`, `current_xp`, `total_xp`
  - `respecs_used`, `unspent_stat_points`

**2. XP Calculation System**
- Generated complete XP table (1-100) with checkpoint system
- Exported to `xp_table.json` for easy loading
- Created `calculate_xp_table.py` for regenerating table if needed

**3. Stat Calculation Module**
- Created `stat_calculations.py` with all stat formulas
- Functions for calculating derived stats from base stats
- Breakpoint detection system
- Equipment bonus integration

**4. Supporting Scripts**
- `migrate_to_new_stats.py` - Database migration script
- `calculate_xp_table.py` - XP table generator

---

## 🔧 Phase 3: Frontend Integration (IN PROGRESS)

### What Needs to Be Done

#### 1. **Stat Allocation Screen** (High Priority)
Create a new UI screen for allocating stat points:

```
┌─────────────────────────────────────────┐
│  Character Stats - Level 25 (3 points)  │
├─────────────────────────────────────────┤
│                                          │
│  ⚔️  MIGHT          [ 50 ]  [+] [-]     │
│      Physical power & HP                 │
│      Current: 150 HP, 100 Attack Power   │
│      Breakpoints: 🏆 100, 200, 300       │
│                                          │
│  🎯 FINESSE        [ 25 ]  [+] [-]      │
│      Crits & evasion                     │
│      Current: 3.75% Crit, 2.5% Dodge    │
│      Breakpoints: 🏆 50, 100, 200, 300   │
│                                          │
│  🛡️  FORTITUDE     [ 30 ]  [+] [-]      │
│      Tank & sustain                      │
│      Current: 240 HP, 15 Defense         │
│      Next Breakpoint: 50 (Second Wind)   │
│                                          │
│  ... (rest of stats)                     │
│                                          │
│  [Reset Stats (1000g)] [Save & Apply]   │
└─────────────────────────────────────────┘
```

**Features Needed:**
- Live preview of stat changes
- Show active breakpoints
- Show next breakpoint
- Highlight recommended stats for build
- Reset button with gold cost
- Save/cancel buttons

#### 2. **XP Bar & Level Display** (High Priority)
Add persistent XP/level display to main UI:

```
┌────────────────────────────────────┐
│  Player Name - Level 25            │
│  ▓▓▓▓▓▓░░░░ 45,000 / 89,832 XP    │
│  (50% to Level 26)                 │
└────────────────────────────────────┘
```

**Features Needed:**
- Animated XP bar
- Level-up notification
- Show XP gained after each duel
- Milestone indicators (checkpoints)

#### 3. **Character Sheet Overhaul** (Medium Priority)
Update character sheet to show:

**Base Stats:**
- Might: 50
- Finesse: 25
- Fortitude: 30
- Arcana: 15
- Insight: 20
- Presence: 10

**Derived Stats:**
- HP: 850 / 850
- Attack Power: 145
- Spell Power: 65
- Defense: 15
- Crit Chance: 5.5%
- Dodge Chance: 2.5%
- Parry Chance: 8.5%
- Armor Penetration: 5%
- HP Regen: 3% per turn
- Lifesteal: 2%
- Cooldown Reduction: 4%

**Active Breakpoints:**
- 🏆 Might: Heavy Weapons Master (+10% 2H damage)
- 🏆 Finesse: Lethal Precision (2.5x crit damage)
- 🏆 Fortitude: (None yet - need 50)

#### 4. **Combat Formula Updates** (High Priority)
Update combat system to use new stat calculations:

**Damage Formula (New):**
```python
from stat_calculations import calculate_all_stats

# Calculate attacker stats
attacker_stats = calculate_all_stats(attacker.get_base_stats())

# Base damage
base_damage = attacker_stats['attack_power']

# Apply armor penetration
effective_armor = defender.defense * (1 - attacker_stats['armor_penetration'])
damage_after_armor = base_damage - effective_armor

# Critical hit check
if random.random() < attacker_stats['crit_chance']:
    damage = damage_after_armor * attacker_stats['crit_damage_mult']
    is_crit = True
else:
    damage = damage_after_armor
    is_crit = False

# Apply breakpoints
if attacker.might >= 100 and random.random() < 0.1:
    apply_stun(defender)

if attacker.might >= 200 and attacker.current_hp / attacker.max_hp > 0.8:
    damage *= 1.2  # +20% damage at high HP

# Lifesteal
if attacker_stats['lifesteal'] > 0:
    heal_amount = damage * attacker_stats['lifesteal']
    attacker.current_hp += heal_amount

return damage, is_crit
```

**Turn Order System (New):**
```python
def calculate_turn_order(player1, player2):
    """Calculate who goes first based on turn meter"""
    p1_stats = calculate_all_stats(player1.get_base_stats())
    p2_stats = calculate_all_stats(player2.get_base_stats())
    
    p1_speed = 100 + p1_stats['turn_meter_bonus'] * 100
    p2_speed = 100 + p2_stats['turn_meter_bonus'] * 100
    
    # Higher speed goes first
    if p1_speed > p2_speed:
        return [player1, player2]
    else:
        return [player2, player1]
```

#### 5. **XP Gain System** (High Priority)
Implement XP rewards for all game activities:

```python
def calculate_xp_reward(duel_result, opponent_rating, player_rating):
    """Calculate XP gained from duel"""
    base_xp = 150
    
    # Rating difference modifier
    rating_diff = opponent_rating - player_rating
    if rating_diff > 0:
        multiplier = 1 + min(rating_diff / 200, 1.0)  # Up to 2x for +200 rating
    else:
        multiplier = max(0.5, 1 + rating_diff / 200)  # Down to 0.5x for -200 rating
    
    # Win/loss modifier
    if duel_result == 'win':
        win_multiplier = 1.0
    else:
        win_multiplier = 0.5  # Half XP for losses
    
    xp = int(base_xp * multiplier * win_multiplier)
    
    return xp

def award_xp(player, xp_amount):
    """Award XP and handle level-ups"""
    player.current_xp += xp_amount
    player.total_xp += xp_amount
    
    # Check for level up
    from stat_calculations import get_cumulative_xp_for_level
    
    current_level_xp = get_cumulative_xp_for_level(player.level)
    next_level_xp = get_cumulative_xp_for_level(player.level + 1)
    
    if player.total_xp >= next_level_xp and player.level < 100:
        # Level up!
        player.level += 1
        player.unspent_stat_points += 3
        
        # Check for checkpoint
        if player.level in [25, 50, 75, 100]:
            return {
                'leveled_up': True,
                'new_level': player.level,
                'checkpoint_reached': True,
                'stat_points_gained': 3
            }
        
        return {
            'leveled_up': True,
            'new_level': player.level,
            'stat_points_gained': 3
        }
    
    return {'leveled_up': False}
```

#### 6. **Daily/Weekly Quest System** (Medium Priority)
Add quests for consistent XP gain:

```python
DAILY_QUESTS = [
    {
        'name': 'Win 3 Duels',
        'requirement': {'type': 'wins', 'count': 3},
        'reward': {'xp': 300, 'gold': 100}
    },
    {
        'name': 'Deal 5000 Damage',
        'requirement': {'type': 'damage', 'count': 5000},
        'reward': {'xp': 250, 'gold': 75}
    },
    {
        'name': 'Use Your Faction Ability 10 Times',
        'requirement': {'type': 'abilities', 'count': 10},
        'reward': {'xp': 200, 'gold': 50}
    }
]

WEEKLY_QUESTS = [
    {
        'name': 'Win 20 Duels This Week',
        'requirement': {'type': 'wins', 'count': 20},
        'reward': {'xp': 1500, 'gold': 500}
    },
    {
        'name': 'Reach 10 Win Streak',
        'requirement': {'type': 'win_streak', 'count': 10},
        'reward': {'xp': 2000, 'gold': 1000}
    }
]
```

---

## 🚀 Implementation Priority

### Week 1: Core Stat System
- [ ] Create stat allocation UI
- [ ] Add XP bar to main interface
- [ ] Implement XP gain from duels
- [ ] Update character sheet to show new stats
- [ ] Add level-up notifications

### Week 2: Combat Integration
- [ ] Update combat formulas to use new stats
- [ ] Implement turn order system
- [ ] Add breakpoint effects to combat
- [ ] Test balance of different builds

### Week 3: Polish & Content
- [ ] Add daily/weekly quests
- [ ] Create first-time tutorial
- [ ] Add stat respec UI
- [ ] Implement checkpoint rewards
- [ ] Add build templates/recommendations

### Week 4: Balance & Testing
- [ ] Balance testing for all build archetypes
- [ ] Adjust XP curve if needed
- [ ] Fine-tune breakpoint values
- [ ] Community testing & feedback

---

## 📝 API Endpoints Needed

### Backend Endpoints to Add/Update

```python
@app.post("/api/allocate_stats")
async def allocate_stats(request: dict):
    """Allocate stat points"""
    # Validate unspent points
    # Apply stat changes
    # Recalculate derived stats
    # Save to database
    pass

@app.post("/api/respec_stats")
async def respec_stats(request: dict):
    """Reset all stat allocations (costs gold)"""
    # Check gold cost
    # Reset all stats to 0
    # Refund all stat points
    # Increment respecs_used
    pass

@app.get("/api/player_stats/{username}")
async def get_player_stats(username: str):
    """Get comprehensive player stats"""
    # Load player from DB
    # Calculate all derived stats
    # Get active breakpoints
    # Return full stat sheet
    pass

@app.post("/api/award_xp")
async def award_xp(request: dict):
    """Award XP and handle level-ups"""
    # Add XP to player
    # Check for level up
    # Award stat points
    # Check for checkpoint
    # Return level-up info
    pass
```

---

## 🎮 Frontend Components Needed

### 1. StatAllocationScreen.js
```javascript
class StatAllocationScreen {
    constructor() {
        this.tempStats = {...playerStats};
        this.unspentPoints = player.unspent_stat_points;
    }
    
    incrementStat(statName) {
        if (this.unspentPoints > 0) {
            this.tempStats[statName]++;
            this.unspentPoints--;
            this.updatePreview();
        }
    }
    
    decrementStat(statName) {
        if (this.tempStats[statName] > 0) {
            this.tempStats[statName]--;
            this.unspentPoints++;
            this.updatePreview();
        }
    }
    
    updatePreview() {
        // Recalculate derived stats
        const derivedStats = calculateDerivedStats(this.tempStats);
        // Update UI
        displayDerivedStats(derivedStats);
        displayBreakpoints(this.tempStats);
    }
    
    async saveStats() {
        const response = await fetch('/api/allocate_stats', {
            method: 'POST',
            body: JSON.stringify({
                username: player.username,
                stats: this.tempStats
            })
        });
        
        if (response.ok) {
            player.stats = {...this.tempStats};
            showNotification('Stats allocated successfully!');
        }
    }
}
```

### 2. XPBar.js
```javascript
class XPBar {
    update(currentXP, levelXP, nextLevelXP) {
        const xpInLevel = currentXP - levelXP;
        const xpNeeded = nextLevelXP - levelXP;
        const percentage = (xpInLevel / xpNeeded) * 100;
        
        this.bar.style.width = percentage + '%';
        this.text.textContent = `${xpInLevel} / ${xpNeeded} XP`;
    }
    
    animateGain(xpGained) {
        // Animate XP bar filling
        // Show floating "+XP" text
        // Play sound effect
    }
    
    onLevelUp(newLevel) {
        // Show level-up animation
        // Display stat points gained
        // Play level-up sound
        // Show checkpoint notification if applicable
    }
}
```

---

## 🧪 Testing Checklist

### Unit Tests
- [ ] XP table generation
- [ ] Stat calculation formulas
- [ ] Breakpoint detection
- [ ] Level-up logic
- [ ] Respec cost calculation

### Integration Tests
- [ ] Allocate stats and verify derived stats update
- [ ] Gain XP and verify level-up occurs
- [ ] Test combat with different stat builds
- [ ] Verify breakpoint effects activate in combat
- [ ] Test stat respec flow

### Balance Tests
- [ ] Pure Might build vs Pure Finesse
- [ ] Pure Fortitude vs Pure Arcana
- [ ] Hybrid builds vs pure builds
- [ ] Different faction synergies with stats
- [ ] XP gain rate at different levels

---

## 📊 Success Metrics

### Week 1
- ✅ Players can allocate stat points
- ✅ XP bar displays correctly
- ✅ Level-ups grant stat points
- ✅ Character sheet shows new stats

### Week 2
- ✅ Combat uses new stat system
- ✅ Breakpoints activate correctly
- ✅ At least 3 viable build archetypes
- ✅ Turn order works as expected

### Week 3
- ✅ Daily/weekly quests provide consistent XP
- ✅ Tutorial guides new players
- ✅ Stat respec available
- ✅ Players reach Level 10 within first week

### Week 4
- ✅ All 6 stats are viable in at least one build
- ✅ XP curve feels balanced
- ✅ Players understand stat system
- ✅ Positive community feedback

---

## 🎯 Next Immediate Steps

1. **Start with backend API endpoints** for stat allocation and XP gain
2. **Create stat allocation UI** in HTML/JavaScript
3. **Add XP bar** to main game interface
4. **Test with mock data** before integrating with live database
5. **Deploy to testing environment** for user feedback

---

## 📚 Documentation Links

- [NEW_STAT_SYSTEM_DESIGN.md](./NEW_STAT_SYSTEM_DESIGN.md) - Full system design
- [calculate_xp_table.py](./calculate_xp_table.py) - XP table generator
- [stat_calculations.py](./stat_calculations.py) - Stat calculation module
- [migrate_to_new_stats.py](./migrate_to_new_stats.py) - Database migration
- [xp_table.json](./xp_table.json) - XP requirements lookup table

---

**Status**: Backend complete ✅ | Frontend in progress 🔄 | Testing pending ⏳
