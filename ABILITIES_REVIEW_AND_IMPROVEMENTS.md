# Abilities Review & Improvements - Idle Duelist

## 📊 **Current Ability Analysis**

### **Total Abilities**: 15 (5 per faction)

---

## ✅ **FULLY IMPLEMENTED ABILITIES** (11/15)

### **Order of the Silver Crusade** (5/5 Working)
1. ✅ **Divine Strike** - Deals 1.5x damage, ignores all armor
2. ✅ **Shield of Faith** - 100% damage reduction for 2 turns
3. ✅ **Healing Light** - Heals 25 HP immediately
4. ✅ **Righteous Fury** - +50% damage, +30% crit for 4 turns
5. ✅ **Purification** - Heals 40 HP + removes all debuffs

### **Shadow Covenant** (3/5 Working)
1. ✅ **Shadow Strike** - 2x damage guaranteed crit (immediate)
2. ✅ **Vanish** - Invisibility for 2 turns
3. ✅ **Poison Blade** - 8 damage/turn for 4 turns
4. ❌ **Assassinate** - NOT IMPLEMENTED (execute mechanic missing)
5. ❌ **Shadow Clone** - NOT IMPLEMENTED (clone mechanic missing)

### **Wilderness Tribe** (3/5 Working)
1. ❌ **Nature's Wrath** - PARTIALLY IMPLEMENTED (slow not applied)
2. ✅ **Thorn Barrier** - Reflects 50% damage for 4 turns
3. ✅ **Wild Growth** - +30% to all stats for 5 turns
4. ✅ **Earthquake** - 20 damage + stuns for 1 turn
5. ✅ **Spirit Form** - 80% damage reduction for 3 turns

---

## 🐛 **ABILITIES NEEDING FIXES**

### **1. Nature's Wrath** (CRITICAL - Missing Slow Application)

**Problem**: Slow amount is calculated but never applied to defender

**Current Code**:
```python
if 'slow_amount' in ability:
    effects['slow_amount'] = ability['slow_amount']
# But never applies to defender.status_effects['slow']!
```

**Fix Needed**:
```python
if 'slow_amount' in effects and 'duration' in effects:
    defender.status_effects['slow']['amount'] = effects['slow_amount']
    defender.status_effects['slow']['duration'] = effects['duration']
```

**Impact**: Medium - Ability does 15 damage but the slow effect never works

---

### **2. Assassinate** (CRITICAL - Missing Execute Mechanic)

**Problem**: Execute threshold is extracted but never checked

**Current**: Just deals 3x damage multiplier (stored as buff for next attack)
**Expected**: Instant kill if target below 25% HP, otherwise 3x damage

**Fix Needed**:
```python
if 'execute_threshold' in effects:
    defender_hp_percent = defender.hp / defender.max_hp
    if defender_hp_percent <= effects['execute_threshold']:
        # Execute! Deal massive damage (99999)
        execute_damage = 99999
        self.combat_status.text = f"💀 {attacker.username} EXECUTES {defender.username}!"
        self._apply_damage(defender, execute_damage, attacker_type, "execute")
        return  # Don't apply other effects
    else:
        # Failed execute, just do normal damage multiplier
        if 'damage_multiplier' in effects:
            base_damage = attacker.get_total_damage()
            damage = int(base_damage * effects['damage_multiplier'])
            self._apply_damage(defender, damage, attacker_type, ability['name'])
```

**Impact**: High - Cool ability is completely broken

---

### **3. Shadow Clone** (CRITICAL - Missing Clone Mechanic)

**Problem**: Clone damage is extracted but clone never attacks

**Current**: Nothing happens with the clone_damage value
**Expected**: Clone should attack independently for 75% damage for 3 turns

**Fix Needed**: Need to implement a clone system that:
1. Stores active clone status
2. On each turn attacker acts, clone also acts
3. Clone deals 75% of attacker's damage
4. Clone lasts 3 turns

**Implementation**:
```python
if 'clone_damage' in effects and 'duration' in effects:
    attacker.active_buffs['shadow_clone'] = {
        'value': effects['clone_damage'],
        'duration': effects['duration']
    }
    self.combat_status.text = f"👥 {attacker.username} creates a shadow clone!"

# Then in _execute_attack, after main attack:
if 'shadow_clone' in attacker.active_buffs and attacker.active_buffs['shadow_clone']['duration'] > 0:
    clone_mult = attacker.active_buffs['shadow_clone']['value']
    clone_damage = int(attacker.get_total_damage() * clone_mult)
    # Apply clone damage
    self._apply_damage(defender, clone_damage, attacker_type, "clone")
    self.combat_status.text += f" (Clone attacks for {clone_damage}!)"
```

**Impact**: High - Unique ability completely missing

---

## 🎯 **ABILITY BALANCE ISSUES**

### **Overpowered Abilities:**

1. **Shield of Faith** - 100% damage reduction for 2 turns is VERY strong
   - **Suggestion**: Reduce to 80% reduction or 1 turn duration
   
2. **Divine Strike** - 999 armor pen + 1.5x damage is excessive
   - **Suggestion**: Reduce armor pen to 50 or 100 (still very high)

3. **Spirit Form** - 80% reduction for 3 turns is nearly invincible
   - **Suggestion**: Reduce to 70% or 2 turns

### **Underpowered Abilities:**

1. **Vanish** - Invisibility for 2 turns but no clear benefit
   - **Current**: Can still be hit by most attacks
   - **Suggestion**: Add +50% damage on next attack from invisibility

2. **Poison Blade** - Only 8 damage/turn for 4 turns (32 total)
   - **Suggestion**: Increase to 12 damage/turn (48 total)

3. **Nature's Wrath** - Only 15 damage + slow (if fixed)
   - **Suggestion**: Increase to 20 damage

---

## 💡 **NEW ABILITY SUGGESTIONS**

### **Order of the Silver Crusade** (More variety needed)

6. **🛡️ Divine Intervention** (NEW)
   - *"Resurrect with 50% HP when taking fatal damage"*
   - Duration: 1 time use per combat
   - Cooldown: 10 turns
   - Auto-triggers when HP would reach 0

7. **⚔️ Smite** (NEW)
   - *"Deal massive damage to stunned or debuffed enemies"*
   - 2.5x damage if target has any debuff
   - Cooldown: 5 turns

8. **✨ Consecrate** (NEW)
   - *"Create holy ground that heals 10 HP per turn"*
   - Duration: 4 turns
   - Cooldown: 7 turns

---

### **Shadow Covenant** (Needs more stealth/trickery)

6. **🗡️ Backstab** (NEW)
   - *"Deal 2.5x damage if attacking from invisibility"*
   - Only works when invisible
   - Cooldown: 4 turns
   - Breaks invisibility after use

7. **💨 Smoke Bomb** (NEW)
   - *"Dodge the next 2 attacks completely"*
   - Duration: 2 attacks (not turns)
   - Cooldown: 6 turns

8. **🎭 Deception** (NEW)
   - *"Swap HP percentages with opponent"*
   - If you're low HP, becomes very strong
   - Cooldown: 12 turns (ultimate ability)

9. **🔪 Hemorrhage** (NEW)
   - *"Inflict bleed: damage increases each turn"*
   - Turn 1: 5 damage
   - Turn 2: 10 damage
   - Turn 3: 15 damage
   - Turn 4: 20 damage
   - Cooldown: 8 turns

---

### **Wilderness Tribe** (Needs more nature/survival theme)

6. **🌿 Entangle** (NEW)
   - *"Root enemy in place: Can't dodge for 2 turns"*
   - Sets dodge chance to 0%
   - Duration: 2 turns
   - Cooldown: 5 turns

7. **🦅 Wild Shape** (NEW)
   - *"Transform into beast: +50% speed, +30% damage"*
   - Duration: 4 turns
   - Cooldown: 8 turns

8. **🌊 Tidal Wave** (NEW)
   - *"Massive damage + push back (delays opponent's next turn)"*
   - 25 damage
   - Opponent loses next turn
   - Cooldown: 10 turns

9. **🌙 Moonfire** (NEW)
   - *"Deal damage based on missing HP"*
   - More damage when you're low HP
   - Formula: base_damage * (1 - current_hp_percent)
   - Cooldown: 6 turns

---

## 🔧 **IMPLEMENTATION PRIORITY**

### **CRITICAL (Fix Broken Abilities)**
1. Fix Nature's Wrath slow application
2. Implement Assassinate execute mechanic
3. Implement Shadow Clone attacks

### **HIGH (Balance Issues)**
4. Nerf Shield of Faith (100% → 80% or 2→1 turn)
5. Nerf Divine Strike armor pen (999 → 50)
6. Buff Poison Blade (8→12 damage/turn)
7. Buff Vanish (add damage bonus)

### **MEDIUM (New Abilities - Pick 2-3 per faction)**
8. Add 2 new abilities for Order
9. Add 2 new abilities for Shadow
10. Add 2 new abilities for Wilderness

### **LOW (Polish)**
11. Add more visual effects for abilities
12. Add ability upgrade system
13. Add faction-specific combos

---

## 📋 **DETAILED IMPLEMENTATION PLAN**

### **Phase 1: Fix Broken Abilities** (30 min)
- [ ] Fix Nature's Wrath slow
- [ ] Implement Assassinate execute
- [ ] Implement Shadow Clone

### **Phase 2: Balance Pass** (20 min)
- [ ] Adjust overpowered abilities
- [ ] Buff underpowered abilities
- [ ] Test balance changes

### **Phase 3: Add New Abilities** (1-2 hours)
- [ ] Design 6-9 new abilities (2-3 per faction)
- [ ] Implement new ability mechanics
- [ ] Create ability data entries
- [ ] Test new abilities

### **Phase 4: Polish** (30 min)
- [ ] Add missing ability assets (if needed)
- [ ] Update ability tooltips
- [ ] Test all abilities in combat
- [ ] Document changes

---

## 🎮 **TESTING CHECKLIST**

After implementing fixes/changes, test:
- [ ] Nature's Wrath applies slow correctly
- [ ] Assassinate executes at <25% HP
- [ ] Assassinate deals normal damage at >25% HP
- [ ] Shadow Clone attacks for 3 turns
- [ ] Shadow Clone damage is 75% of main attack
- [ ] All buffs/debuffs show in status indicators
- [ ] Cooldowns work correctly
- [ ] Ability tooltips are accurate
- [ ] No crashes or errors

---

## 💬 **QUESTIONS FOR USER**

1. **Priority**: Should I focus on fixing broken abilities first, or add new ones?
2. **Balance**: Are you happy with current ability power levels?
3. **New Abilities**: Which faction needs more abilities most urgently?
4. **Complexity**: Do you want more complex mechanics (like execute, clone) or simpler ones?

---

**Current Status**: 11/15 abilities fully working, 3 critically broken, 1 partially working
**Recommendation**: Fix the 4 broken/partial abilities first, then add 2 new abilities per faction
