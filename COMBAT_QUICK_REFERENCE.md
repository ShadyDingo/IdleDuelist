# Combat System - Quick Reference Guide

## 🎮 New Combat Controls

### Header Buttons (Top of Screen)
```
[Turn 1] [Speed: 1x] [Log: OFF] [Stats] [Info]
```

| Button | Function | States |
|--------|----------|--------|
| **Speed: 1x** | Toggle combat speed | 1x (Blue) → 2x (Green) → 3x (Red) |
| **Log: OFF** | Toggle combat log | OFF (Purple) ↔ ON (Green) |
| **Stats** | View damage breakdown | Shows popup with last attack details |
| **Info** | View abilities | Shows all abilities for both players |

---

## 📊 Status Effect Indicators

Located **above health bars**, shows active effects:

| Icon | Effect | Description |
|------|--------|-------------|
| ☠️3 | Poison | Taking damage over time (3 turns left) |
| 😵2 | Stun | Cannot attack (2 turns left) |
| 👻4 | Invisibility | Hidden, increased damage (4 turns left) |
| 🐌3 | Slow | Reduced speed (3 turns left) |
| 🛡️2 | Shield | Damage reduction (2 turns left) |

---

## 🔥 Combo System

**How it Works:**
- Land consecutive attacks to build combo
- Each combo hit adds **+5% damage** (max +25%)
- Combo resets on: miss, dodge, stun, or opponent's turn

**Visual Indicator:**
```
[COMBO x3!] ← Shown above your health bar
```

**Damage Bonus:**
- x1: No bonus (first hit)
- x2: +5% damage
- x3: +10% damage
- x4: +15% damage
- x5: +20% damage
- x6+: +25% damage (max)

---

## 📈 Damage Breakdown (Stats Button)

Shows detailed calculation of last attack:

```
Last Attack Breakdown

Attacker: PlayerName
Defender: OpponentName

Base Damage: 50
Critical Hit: x1.5
Damage Buffs: +20%
Combo Bonus: +10%
Armor Penetration: 15

Defense: -25
Damage Reduction: -10%

Final Damage: 68
```

---

## ℹ️ Abilities Info (Info Button)

Shows scrollable popup with:

**Your Abilities (Green)**
- ⚔️ Divine Strike
  - Deal 150% damage to target
  - Cooldown: 3 turns

**Opponent's Abilities (Red)**  
- 🗡️ Shadow Strike
  - Deal 120% damage with guaranteed crit
  - Cooldown: 4 turns

---

## 📝 Combat Log

Toggle with "Log" button. Shows detailed text of combat:

```
═══ TURN 1 ═══
✨ Player1 uses Divine Strike!
⚡ Player1 CRITS for 75 damage! (COMBO x2)
Player2's HP: 25/100

═══ TURN 2 ═══
💨 Player1 dodges the attack!
⚔️ Player2 attacks for 45 damage!
```

---

## ⚖️ Balance Changes Summary

### Critical Hit Chance (Speed Bonus)
- **Old**: 0.5% per speed point
- **New**: 0.25% per speed point (50% reduction)

### Dodge Chance (Speed Bonus)
- **Old**: 1.5% per speed (up to 20), 0.5% above
- **New**: 1.0% per speed (up to 20), 0.25% above
- **Max**: 40% (reduced from 50%)

**Impact**: Speed is still valuable but not overpowered. Other stats matter more.

---

## 🎯 Combat Flow with New Features

### During Combat:
1. **Watch the action** on screen
2. **Monitor status effects** (icons above health bars)
3. **Track combos** (counter appears at x2+)
4. **Toggle speed** if combat is too slow/fast
5. **Check log** for detailed play-by-play
6. **View stats** to understand damage
7. **Check info** to see what abilities are available

### Best Practices:
- Use **1x speed** to learn mechanics
- Use **2x speed** for normal play
- Use **3x speed** to grind quickly
- Enable **log** when analyzing strategies
- Check **stats** after big hits to learn
- Review **info** to plan counter-strategies

---

## 🐛 Bug Fixes

### Stun Effect Now Works Correctly
**Before**: Defender's stun was checked (wrong player)
**After**: Attacker's stun is checked (correct)
**Result**: Stunned players now properly skip their turn

---

## 💡 Tips & Tricks

### Maximize Combos:
- Build high accuracy/speed to avoid misses
- Avoid abilities that give opponent's turn
- Use consistent attacks rather than alternating

### Use Speed Control:
- 1x: Study enemy patterns
- 2x: Normal gameplay
- 3x: Fast farming

### Learn with Stats:
- Check damage breakdown after each attack type
- Compare critical vs normal hits
- Understand how buffs stack

### Plan with Info:
- Check opponent's abilities before they use them
- Know cooldowns to predict their moves
- Identify threats early

---

## 🎨 Visual Cues

| Visual | Meaning |
|--------|---------|
| Green health bar | >50% HP |
| Yellow health bar | 20-50% HP |
| Red health bar | <20% HP |
| Red damage number | Critical hit |
| White damage number | Normal hit |
| Green +number | Healing |
| Pulsing ability icon | Ability being used |
| Status icon + number | Effect active (# turns) |
| COMBO x# text | Current combo count |

---

## ⚡ Keyboard Shortcuts

*(Currently mouse/touch only, but could be added)*

**Suggested Future Shortcuts:**
- `1/2/3`: Set combat speed
- `L`: Toggle log
- `S`: Show stats
- `I`: Show info
- `Space`: Pause combat (if added)

---

This quick reference covers all new combat features. Happy dueling! ⚔️
