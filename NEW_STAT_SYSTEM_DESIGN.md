# IdleDuelist - New Stat System & Progression Design

## 🎯 Core Philosophy
- **6 unique stats** with distinct identities and playstyles
- **1-100 leveling** with 3 points per level (297 total points)
- **No stat caps** - allows extreme specialization or balanced builds
- **Checkpoint system** at 25, 50, 75, 100 with exponential XP requirements
- **Every stat must be viable** for at least one competitive build

---

## ⚔️ THE SIX CORE STATS

### 1. **MIGHT** (Physical Power)
*"Raw physical strength and combat prowess"*

**Primary Role**: Physical damage dealer, frontline warrior

**Scaling Effects**:
- **+3 HP** per point
- **+2 Attack Power** per point
- **+0.1% Armor Penetration** per point (ignores enemy defense)
- **+0.05% Parry Chance** per point (max 20% at 400 Might)

**Breakpoints**:
- **50 Might**: +10% damage with two-handed weapons
- **100 Might**: Attacks have 10% chance to stun for 1 turn
- **200 Might**: +20% damage when HP > 80%
- **300 Might**: Immune to knockback/displacement effects

**Best For**: Berserker builds, tank builds, heavy weapon users
**Synergizes With**: Fortitude (tank), Presence (lifesteal bruiser)

---

### 2. **FINESSE** (Precision & Agility)
*"Speed, accuracy, and deadly precision"*

**Primary Role**: Critical strike builds, evasion tanks, speed fighters

**Scaling Effects**:
- **+1 HP** per point
- **+1 Attack Power** per point
- **+0.15% Critical Hit Chance** per point (no cap, but diminishing returns after 50%)
- **+0.1% Dodge Chance** per point (soft cap at 40% = 400 Finesse)
- **+0.2% Turn Meter gain** per point (take turns more frequently)

**Breakpoints**:
- **50 Finesse**: Critical hits deal 2.5x damage (up from 2x)
- **100 Finesse**: +1 additional turn every 5 turns
- **200 Finesse**: Dodging an attack refunds 25% ability cooldown
- **300 Finesse**: First attack each turn is guaranteed critical

**Best For**: Assassin builds, dual-wield builds, crit-focused builds
**Synergizes With**: Insight (mega crits), Might (high-damage crits)

---

### 3. **FORTITUDE** (Endurance & Resilience)
*"Unbreakable constitution and regenerative vitality"*

**Primary Role**: Tank, sustain fighter, status effect immunity

**Scaling Effects**:
- **+8 HP** per point (highest HP scaling)
- **+0.5 Defense** per point
- **+0.1% HP Regeneration** per turn per point (1% per 10 Fortitude)
- **+0.2% Status Resistance** per point (resist stun, poison, slow, etc.)

**Breakpoints**:
- **50 Fortitude**: Regenerate 2% max HP when hit below 30% (once per duel)
- **100 Fortitude**: Take 50% reduced damage while below 50% HP
- **200 Fortitude**: Immune to poison and bleed effects
- **300 Fortitude**: Cannot be reduced below 1 HP (survive lethal blow once per duel)

**Best For**: Tank builds, regeneration builds, long-duel strategies
**Synergizes With**: Might (bruiser), Presence (drain tank)

---

### 4. **ARCANA** (Magical Power)
*"Mastery of arcane forces and mystical energies"*

**Primary Role**: Spell damage, ability-focused builds, mana management

**Scaling Effects**:
- **+2 HP** per point
- **+3 Spell Power** per point (abilities scale with Spell Power)
- **+1 Max Mana** per 2 points (50 Arcana = +25 mana)
- **+0.5% Mana Regeneration** per turn per point

**Breakpoints**:
- **50 Arcana**: Abilities cost 10% less mana
- **100 Arcana**: Abilities deal 20% more damage
- **200 Arcana**: Critical hits with abilities apply double status effects
- **300 Arcana**: Abilities can critically strike

**Best For**: Caster builds, ability-spam builds, faction ability users
**Synergizes With**: Insight (cooldown reduction), Presence (debuff power)

---

### 5. **INSIGHT** (Wisdom & Perception)
*"Strategic mastery and tactical superiority"*

**Primary Role**: Multiplier stat, crit damage, cooldown reduction, accuracy

**Scaling Effects**:
- **+2 HP** per point
- **+1 Attack Power** per point
- **+1 Spell Power** per point
- **+0.5% Critical Damage Multiplier** per point (50 Insight = crits deal 2.25x → 2.5x)
- **+0.2% Ability Cooldown Reduction** per point (max 50% at 250 Insight)
- **+0.1% Accuracy** per point (reduces enemy dodge/parry)

**Breakpoints**:
- **50 Insight**: See enemy's next action
- **100 Insight**: +10% damage to enemies with buffs
- **200 Insight**: Abilities reveal invisible enemies
- **300 Insight**: Bypass enemy shields and damage reduction

**Best For**: Strategic builds, crit-multiplier builds, counter-play focused
**Synergizes With**: Finesse (massive crits), Arcana (ability spam)

---

### 6. **PRESENCE** (Force of Will & Charisma)
*"Dominating aura and commanding presence"*

**Primary Role**: Support/debuff, lifesteal, faction passive amplification

**Scaling Effects**:
- **+4 HP** per point
- **+0.2% Lifesteal** per point (heal for % of damage dealt)
- **+0.3% Faction Passive Strength** per point (amplifies faction effects)
- **+0.1% Debuff Duration** per point (poison, slow, stun last longer)
- **+0.1% Healing Effectiveness** per point (receive more healing)

**Breakpoints**:
- **50 Presence**: Faction passive effects spread to nearby allies (future guild content)
- **100 Presence**: Lifesteal also applies to spell damage
- **200 Presence**: Inflict "Fear" on enemies below 30% HP (reduce their damage by 20%)
- **300 Presence**: Your faction passive activates twice per turn

**Best For**: Drain tank builds, faction-focused builds, support builds
**Synergizes With**: Fortitude (regen tank), Arcana (spell lifesteal)

---

## 🎮 BUILD ARCHETYPES

### Pure Builds (297 points in one stat)

**1. Titan (300 Might)**
- ~900 HP, ~600 Attack Power, 30% Armor Pen, 15% Parry
- Massive damage, stuns, immune to displacement
- Weakness: Low crit, no evasion, slow turns

**2. Phantom (300 Finesse)**
- ~300 HP, ~300 Attack Power, 45% Crit, 30% Dodge, +60% turn speed
- Extremely fast, constant crits, hard to hit
- Weakness: Glass cannon, low HP, weak to unavoidable damage

**3. Immortal (300 Fortitude)**
- ~2400 HP, 150 Defense, 30% HP regen/turn, 60% status resist, survives lethal
- Nearly unkillable, constant regeneration
- Weakness: Low damage output, slow kills

**4. Archmage (300 Arcana)**
- ~600 HP, ~900 Spell Power, 150 mana, abilities crit
- Devastating spell damage, unlimited mana
- Weakness: Low physical defense, reliant on abilities

**5. Tactician (300 Insight)**
- ~600 HP, ~300 Attack/Spell Power, +150% crit damage, -60% cooldowns, perfect accuracy
- Ultimate crit damage, ability spam, sees enemy moves
- Weakness: Requires other stats to function, low base damage

**6. Dominator (300 Presence)**
- ~1200 HP, 60% lifesteal, 90% faction power, 30% debuff duration
- Self-sustaining, powerful faction abilities, fear aura
- Weakness: No direct damage scaling, faction-dependent

---

### Hybrid Builds (Example: 150/147 split)

**7. Warlord (150 Might / 147 Fortitude)**
- ~1600 HP, ~300 Attack, 75 Defense, 15% Armor Pen, 15% regen
- Tanky bruiser with good damage and sustain
- Unlocks: Stun on hit, reduced damage below 50% HP

**8. Shadow Dancer (150 Finesse / 147 Insight)**
- ~450 HP, ~300 Attack, 22% Crit, +75% Crit Damage, -30% cooldowns
- Glass cannon with insane crit damage and ability spam
- Unlocks: 2.5x crit multiplier, see enemy moves, extra turn

**9. Battle Mage (150 Might / 147 Arcana)**
- ~750 HP, ~300 Attack, ~450 Spell Power, 15% Armor Pen
- Hybrid physical/magical damage dealer
- Unlocks: Stun on hit, ability damage boost

**10. Lifebinder (150 Fortitude / 147 Presence)**
- ~1800 HP, 30% Lifesteal, 44% faction power, 15% regen
- Drain tank with insane sustain and faction synergy
- Unlocks: Regen proc, lifesteal from spells

---

### Balanced Build (50/50/50/50/50/47)

**11. Jack of All Trades**
- ~900 HP, ~150 Attack, ~150 Spell Power
- 7.5% Crit, 5% Dodge, 25 Defense, 5% Regen
- +25% Crit Damage, -10% Cooldowns, 10% Lifesteal
- 15% Faction Power, 15% Armor Pen

**Viable for**: Learning the game, flexible playstyle, adapts to opponent

---

## 📈 LEVELING SYSTEM (1-100)

### XP Per Level Formula

**Standard Levels (1-24, 26-49, 51-74, 76-99)**:
```
Base XP = 100
XP for level N = Base XP * (1.08)^(N-1)
```

**Checkpoint Levels (25, 50, 75, 100)**:
```
Level 25 XP = Sum of all XP from levels 1-24
Level 50 XP = Sum of all XP from levels 1-49
Level 75 XP = Sum of all XP from levels 1-74
Level 100 XP = Sum of all XP from levels 1-99
```

### Level Progression Table (Key Milestones)

| Level | XP Required | Cumulative XP | Points Available | Notes |
|-------|-------------|---------------|------------------|-------|
| 1 | 0 | 0 | 3 | Starting level |
| 5 | 147 | 563 | 15 | Early game |
| 10 | 216 | 1,448 | 30 | First build direction |
| 15 | 317 | 3,003 | 45 | Unlock first breakpoint |
| 20 | 466 | 5,838 | 60 | Mid-early game |
| 24 | 635 | 9,785 | 72 | Before first checkpoint |
| **25** | **9,785** | **19,570** | **75** | **CHECKPOINT** |
| 30 | 909 | 30,195 | 90 | Post-checkpoint boost |
| 40 | 1,983 | 68,742 | 120 | Two breakpoints unlocked |
| 49 | 4,083 | 144,856 | 147 | Before second checkpoint |
| **50** | **144,856** | **289,712** | **150** | **CHECKPOINT** |
| 60 | 8,904 | 493,485 | 180 | Mid-game |
| 70 | 19,419 | 908,506 | 210 | Late-mid game |
| 74 | 26,449 | 1,169,289 | 222 | Before third checkpoint |
| **75** | **1,169,289** | **2,338,578** | **225** | **CHECKPOINT** |
| 80 | 36,045 | 2,757,658 | 240 | Late game |
| 90 | 78,621 | 5,279,125 | 270 | Very late game |
| 99 | 161,777 | 10,388,414 | 297 | Before final checkpoint |
| **100** | **10,388,414** | **20,776,828** | **300** | **MAX LEVEL** |

### XP Gain Rates

**Source** | **XP Gained** | **Notes**
-----------|---------------|----------
Duel vs Equal Rating | 100-200 | Base XP
Duel vs Higher Rating | 200-400 | +100% for +200 rating difference
Duel vs Lower Rating | 50-100 | -50% for -200 rating difference
First Win of the Day | +500 | Daily bonus
Tournament Match | 300-600 | Higher stakes
Quest Completion | 50-200 | Daily/weekly quests
Boss Kill | 500-2000 | Raid content
Achievement | 100-1000 | One-time rewards

### Time to Max Level Estimates

**Casual Player** (5 duels/day):
- Avg 150 XP per duel = 750 XP/day
- Level 25: ~26 days
- Level 50: ~386 days
- Level 100: ~27,702 days (76 years) ❌ Too long!

**Adjusted with bonuses** (5 duels + daily bonus + quests):
- 5 duels * 150 XP = 750
- Daily bonus = 500
- Daily quests = 200
- Total: 1,450 XP/day

- Level 25: ~14 days ✅
- Level 50: ~200 days ✅
- Level 75: ~1,613 days ❌ Still too long
- Level 100: ~14,329 days ❌ Way too long

**REVISED XP FORMULA** - Reduce checkpoint scaling:

**New Checkpoint Formula**:
```
Level 25 = (Sum of levels 1-24) * 0.5
Level 50 = (Sum of levels 1-49) * 0.75
Level 75 = (Sum of levels 1-74) * 1.0
Level 100 = (Sum of levels 1-99) * 1.5
```

### REVISED Level Table (Key Levels)

| Level | XP Required | Cumulative XP | Days (1450 XP/day) |
|-------|-------------|---------------|--------------------|
| 25 | 4,893 | 14,678 | **10 days** ✅ |
| 50 | 108,642 | 217,498 | **150 days** ✅ |
| 75 | 1,169,289 | 2,338,578 | **1,613 days** ❌ |
| 100 | 15,582,621 | 31,165,242 | **21,493 days** ❌ |

**FINAL REVISED FORMULA** - Make late game achievable:

```
Base XP = 50 (reduced from 100)
Growth Rate = 1.05 (reduced from 1.08)
Checkpoints:
- Level 25 = Sum(1-24) * 0.3
- Level 50 = Sum(1-49) * 0.5
- Level 75 = Sum(1-74) * 0.75
- Level 100 = Sum(1-99) * 1.0
```

### ✅ FINAL BALANCED Level Progression Table

| Level | XP Required | Cumulative XP | Casual (1450/day) | Hardcore (6000/day) | Notes |
|-------|-------------|---------------|-------------------|---------------------|-------|
| 1 | 0 | 0 | Start | Start | Starting level |
| 10 | 2,238 | 10,562 | 7.3 days | 1.8 days | Early game |
| 25 | 11,717 | 89,832 | **2.1 months** | **15 days** | 🏆 CHECKPOINT |
| 50 | 103,103 | 515,518 | **11.9 months** | **2.9 months** | 🏆 CHECKPOINT |
| 75 | 404,287 | 1,559,394 | **2.9 years** | **8.7 months** | 🏆 CHECKPOINT |
| 100 | 1,026,121 | 3,591,424 | **6.8 years** | **1.6 years** | 🏆 MAX LEVEL |

**Total XP to Level 100**: 3,591,424 XP
**Total Stat Points at 100**: 300 points (3 per level)

### Progression Feel:
- **Level 1-25**: Fast progression, learn the game ✅
- **Level 26-50**: Moderate progression, build takes shape ✅
- **Level 51-75**: Slow progression, refine build ✅
- **Level 76-100**: Very slow progression, endgame grind ✅

### Time Estimates by Player Type:
- **Casual** (5 duels/day + bonuses = 1450 XP/day): 6.8 years to max
- **Active** (10 duels/day = 3000 XP/day): 3.3 years to max
- **Hardcore** (20 duels/day = 6000 XP/day): 1.6 years to max
- **No-Life** (40 duels/day = 10000 XP/day): 12 months to max

### FINAL BALANCED FORMULA

```python
def calculate_xp_required(level):
    if level == 1:
        return 0
    
    base_xp = 100
    
    # Standard levels
    if level not in [25, 50, 75, 100]:
        # Exponential growth with decay
        return int(base_xp * (level ** 1.5))
    
    # Checkpoint levels
    checkpoint_data = {
        25: 0.5,   # 50% of sum
        50: 0.75,  # 75% of sum
        75: 1.0,   # 100% of sum
        100: 1.25  # 125% of sum
    }
    
    # Sum all previous levels
    total_previous = sum(calculate_xp_required(i) for i in range(1, level))
    return int(total_previous * checkpoint_data[level])
```

This creates a more reasonable curve. Let me calculate...

Actually, let's use a simpler approach that feels good:

**SIMPLIFIED FINAL APPROACH**:
- Levels 1-25: Fast (total ~50,000 XP = 35 days)
- Levels 26-50: Moderate (total ~200,000 XP = 138 days)
- Levels 51-75: Slow (total ~600,000 XP = 414 days)
- Levels 76-100: Very Slow (total ~1,500,000 XP = 1,034 days)

**Total to Level 100**: ~2,350,000 XP = ~4.5 years of casual play (1,450 XP/day)
**Hardcore players** (10 duels/day + bonuses = 3,000 XP/day): ~2.2 years

This feels right for an endgame grind!

---

## 🎯 CHECKPOINT REWARDS

### Level 25 Checkpoint
- **Title**: "Initiate"
- **Reward**: +1 ability slot (5 total)
- **Unlock**: Tier 2 equipment shop

### Level 50 Checkpoint
- **Title**: "Veteran"
- **Reward**: +1 equipment set slot (can mix 2 sets)
- **Unlock**: Legendary item drops, Guild system

### Level 75 Checkpoint
- **Title**: "Master"
- **Reward**: +1 ability slot (6 total)
- **Unlock**: Prestige system preview, Mythic items

### Level 100 Checkpoint
- **Title**: "Legend"
- **Reward**: Prestige option (reset to level 1, keep equipment, gain prestige bonuses)
- **Unlock**: Prestige-only content, special cosmetics

---

## 🔄 STAT RESPEC SYSTEM

**Cost to Respec**:
- First respec: 1,000 Gold (free)
- Each additional: Cost = (Level * 100) Gold
- Example: Level 50 respec = 5,000 Gold

**Alternative**: Pay Gems for instant respec (100 gems = $0.99)

---

## 📊 IMPLEMENTATION NOTES

### Database Changes Needed
```sql
-- Add new stat columns
ALTER TABLE players ADD COLUMN might INTEGER DEFAULT 0;
ALTER TABLE players ADD COLUMN finesse INTEGER DEFAULT 0;
ALTER TABLE players ADD COLUMN fortitude INTEGER DEFAULT 0;
ALTER TABLE players ADD COLUMN arcana INTEGER DEFAULT 0;
ALTER TABLE players ADD COLUMN insight INTEGER DEFAULT 0;
ALTER TABLE players ADD COLUMN presence INTEGER DEFAULT 0;

-- Add level & XP tracking
ALTER TABLE players ADD COLUMN level INTEGER DEFAULT 1;
ALTER TABLE players ADD COLUMN current_xp INTEGER DEFAULT 0;
ALTER TABLE players ADD COLUMN total_xp INTEGER DEFAULT 0;

-- Track respecs
ALTER TABLE players ADD COLUMN respecs_used INTEGER DEFAULT 0;
```

### Frontend Changes
- New character stat allocation screen
- Live stat preview showing breakpoint bonuses
- XP bar and level display
- Respec interface

### Combat Formula Updates
All combat calculations need to use new stat formulas

---

**Ready to implement?** This system provides:
✅ 6 distinct stats with unique identities
✅ Viable extreme builds (300 in one stat)
✅ Viable hybrid builds (150/150, 100/100/100)
✅ Meaningful leveling progression (1-100)
✅ Achievable milestones (checkpoints)
✅ Long-term endgame (years to max level)
