# The Math Behind Build Success/Failure

## 🧮 **UNDERSTANDING THE COMBAT FORMULA**

### **Core Combat Equation**

```
Winner = Player with HP > 0 when opponent reaches HP ≤ 0

Time to Kill (TTK) = Enemy Effective HP / Your DPS
Your Survival = Your Effective HP / Enemy DPS

If Your TTK < Enemy TTK → You Win
```

### **Key Formulas**

```python
# Effective HP (EHP)
EHP = HP / (1 - Damage Reduction)
Damage Reduction = min(Defense * 0.5 / Enemy_Attack, 0.75)

# Damage Per Second (DPS)
DPS = Attack * (1 + Crit_Rate * Crit_Multiplier) * (1 - Enemy_Dodge)

# Win Condition
Player_EHP / Enemy_DPS > Enemy_EHP / Player_DPS → Player Wins
```

---

## 🔍 **CASE STUDY: WHY BRUISER WINS EVERYTHING**

### **Bruiser Build (99.8% WR)**
```
Stat Allocation:
- 20 points → Attack Power (+40 attack)
- 10 points → Defense (+10 defense)
- 10 points → Max HP (+100 HP)
- 10 points → Crit Chance (+10% crit)

Final Stats:
- HP: 200
- Attack: 55 (base 15 + 40)
- Defense: 15 (base 5 + 10)
- Crit: 17.5% (base 7.5% + 10%)
```

### **vs Pure Attack (65 attack, 100 HP, 5 def)**

**Step 1: Calculate Effective HP**
```
Bruiser EHP:
Damage Reduction = 15 * 0.5 / 65 = 0.115 (11.5%)
EHP = 200 / (1 - 0.115) = 226 EHP

Pure Attack EHP:
Damage Reduction = 5 * 0.5 / 55 = 0.045 (4.5%)
EHP = 100 / (1 - 0.045) = 104.7 EHP
```

**Step 2: Calculate DPS**
```
Bruiser DPS:
Base = 55
Crit Bonus = 55 * 0.175 * 0.5 = 4.8
Total DPS = 59.8

Pure Attack DPS:
Base = 65
Crit Bonus = 65 * 0.075 * 0.5 = 2.4
Total DPS = 67.4
```

**Step 3: Calculate Time to Kill**
```
Bruiser kills Pure Attack in:
TTK = 104.7 / 59.8 = 1.75 turns

Pure Attack kills Bruiser in:
TTK = 226 / 67.4 = 3.35 turns
```

**Result:** Bruiser wins by **1.6 turns** (almost twice as fast!)

**Why?**
- Bruiser has 2.16x more effective HP (226 vs 104.7)
- Pure Attack only has 1.13x more DPS (67.4 vs 59.8)
- **EHP advantage > DPS disadvantage**

---

## 💔 **CASE STUDY: WHY SPELL CASTER FAILS**

### **Spell Caster Build (0.1% WR)**
```
Stat Allocation:
- 25 points → Spell Power (+50 spell power)
- 5 points → Attack Power (+10 attack)
- 5 points → Defense (+5 defense)
- 10 points → Max HP (+100 HP)
- 5 points → Speed (+5 speed)
- 5 points → Crit Chance (+5% crit)

Final Stats:
- HP: 200
- Attack: 25 (15 base + 10)
- Spell Power: 50 (DOES NOTHING!)
- Defense: 10
- Speed: 10
```

### **vs Bruiser**

**Step 1: Calculate Effective HP**
```
Spell Caster EHP:
Damage Reduction = 10 * 0.5 / 55 = 0.091 (9.1%)
EHP = 200 / (1 - 0.091) = 220 EHP

Bruiser EHP:
Damage Reduction = 15 * 0.5 / 25 = 0.30 (30%!)
EHP = 200 / (1 - 0.30) = 286 EHP
```

**Step 2: Calculate DPS**
```
Spell Caster DPS:
Base = 25 (spell power doesn't count!)
Crit Bonus = 25 * 0.125 * 0.5 = 1.6
Total DPS = 26.6

Bruiser DPS:
Base = 55
Crit Bonus = 55 * 0.175 * 0.5 = 4.8
Total DPS = 59.8
```

**Step 3: Calculate Time to Kill**
```
Spell Caster kills Bruiser in:
TTK = 286 / 26.6 = 10.75 turns

Bruiser kills Spell Caster in:
TTK = 220 / 59.8 = 3.68 turns
```

**Result:** Bruiser wins by **7 turns** (3x faster!)

**Why?**
- 50 spell power contributes **ZERO damage**
- Spell Caster only has 26.6 DPS vs Bruiser's 59.8 DPS
- **Wasted 25 stat points = auto-lose**

**After Fix (50% conversion):**
```
Fixed DPS:
Base = 25 + (50 * 0.5) = 50
Crit Bonus = 50 * 0.125 * 0.5 = 3.1
Total DPS = 53.1

New TTK = 286 / 53.1 = 5.39 turns

Still loses but much closer! (5.39 vs 3.68)
With other changes, becomes viable!
```

---

## 🏃 **CASE STUDY: WHY SPEED DEMON FAILS**

### **Speed Demon Build (23.8% WR)**
```
Stat Allocation:
- 10 points → Attack Power (+20 attack)
- 20 points → Speed (+20 speed)
- 20 points → Crit Chance (+20% crit)

Final Stats:
- HP: 100
- Attack: 35
- Speed: 25 (base 5 + 20)
- Crit: 37.5% (base 7.5% + 20% + 10% from speed)
- Dodge: 32.5%
```

### **vs Bruiser**

**Step 1: Calculate Effective HP**
```
Speed Demon EHP (with dodge):
Base Reduction = 5 * 0.5 / 55 = 0.045 (4.5%)
Dodge Reduction = 32.5% * 50% = 16.25% extra
Total Reduction = ~20%
EHP = 100 / (1 - 0.20) = 125 EHP

Bruiser EHP (no dodge):
Damage Reduction = 15 * 0.5 / 35 = 0.214 (21.4%)
EHP = 200 / (1 - 0.214) = 254 EHP
```

**Step 2: Calculate DPS**
```
Speed Demon DPS:
Base = 35
Crit Bonus = 35 * 0.375 * 0.5 = 6.6
Total DPS = 41.6

Bruiser DPS (vs dodge):
Base = 55
Crit Bonus = 55 * 0.175 * 0.5 = 4.8
Dodge Penalty = (55 + 4.8) * 0.325 * 0.5 = 9.7
Effective DPS = 59.8 - 9.7 = 50.1
```

**Step 3: Calculate Time to Kill**
```
Speed Demon kills Bruiser in:
TTK = 254 / 41.6 = 6.11 turns

Bruiser kills Speed Demon in:
TTK = 125 / 50.1 = 2.50 turns
```

**Result:** Bruiser wins by **3.6 turns** (2.4x faster!)

**Why?**
- Speed Demon invested 40 points in speed/crit
- Only got 41.6 DPS (vs Bruiser's 59.8)
- 100 HP is too fragile even with 32.5% dodge
- **Speed doesn't increase damage → loses DPS race**

**After Speed Buff (+1% damage per speed):**
```
Fixed DPS:
Base = 35 * 1.25 (25% speed bonus) = 43.75
Crit Bonus = 43.75 * 0.375 * 0.5 = 8.2
Total DPS = 51.95

New TTK = 254 / 51.95 = 4.89 turns

Still loses but much better! (4.89 vs 2.50)
With HP nerf to Bruiser, becomes competitive!
```

---

## 💰 **STAT EFFICIENCY ANALYSIS**

### **Cost-Benefit per Stat Point**

| Stat | Per Point | vs 50 Attack | vs 10 Defense | Efficiency |
|------|-----------|--------------|---------------|------------|
| **Attack** | +2 damage | +2 DPS | +2 DPS | ⭐⭐⭐⭐⭐ |
| **HP** (current) | +10 HP | +10 survivability | +10 survivability | ⭐⭐⭐⭐⭐ |
| **HP** (nerfed) | +8 HP | +8 survivability | +8 survivability | ⭐⭐⭐⭐ |
| **Defense** (current) | +1 def | +0.5 reduction | +1% reduction | ⭐⭐⭐ |
| **Defense** (buffed) | +1 def | +0.6 reduction | +1.2% reduction | ⭐⭐⭐⭐ |
| **Crit** | +1% | +0.5% DPS | +0.5% DPS | ⭐⭐⭐ |
| **Speed** (current) | +1 speed | +0% DPS | +0% DPS | ⭐ |
| **Speed** (buffed) | +1 speed | +1% DPS | +1% DPS | ⭐⭐⭐⭐ |
| **Spell** (current) | +2 spell | +0 DPS | +0 DPS | ☆ |
| **Spell** (fixed) | +2 spell | +1 DPS | +1 DPS | ⭐⭐⭐⭐ |

### **Efficiency Calculation Example**

**Attack Power:**
```
1 point = +2 attack
Against 100 HP, 10 def target:
Damage per hit = 2
Kills in 50 hits (unchanged)
Efficiency: Direct damage increase
```

**HP (Current - 10 per point):**
```
1 point = +10 HP
Against 50 attack opponent:
Survives 0.2 extra hits
Efficiency: Very high survivability
```

**HP (Nerfed - 8 per point):**
```
1 point = +8 HP
Against 50 attack opponent:
Survives 0.16 extra hits
Efficiency: Still good, more balanced
```

**Defense (Current - 1 per point, 0.5x multiplier):**
```
1 point = +1 defense
Against 50 attack:
Reduction = 1 * 0.5 / 50 = 1%
With 100 HP = 101 EHP
Efficiency: Low (1 EHP per point)
```

**Defense (Buffed - 1 per point, 0.6x multiplier):**
```
1 point = +1 defense
Against 50 attack:
Reduction = 1 * 0.6 / 50 = 1.2%
With 100 HP = 101.2 EHP
Efficiency: Better but still lower than HP
```

**Speed (Current - 0% damage bonus):**
```
1 point = +1 speed
Combat benefit = Turn order only
DPS increase = 0%
Efficiency: Near zero for DPS
```

**Speed (Buffed - 1% damage bonus):**
```
1 point = +1 speed
Combat benefit = +1% damage
With 50 attack = +0.5 DPS
Efficiency: Comparable to attack!
```

---

## 📊 **WHY HP IS BETTER THAN DEFENSE**

### **Scenario: 25 Points to Invest**

**Option A: All in Defense**
```
Stats:
- 100 HP (base)
- 30 Defense (5 base + 25)

vs 55 Attack opponent:
Reduction = 30 * 0.5 / 55 = 27.3%
EHP = 100 / (1 - 0.273) = 137.5

Result: 137.5 effective HP
Cost: 25 points
Efficiency: 5.5 EHP per point
```

**Option B: All in HP (current)**
```
Stats:
- 350 HP (100 base + 250)
- 5 Defense (base)

vs 55 Attack opponent:
Reduction = 5 * 0.5 / 55 = 4.5%
EHP = 350 / (1 - 0.045) = 366.5

Result: 366.5 effective HP
Cost: 25 points
Efficiency: 14.7 EHP per point

HP is 2.67x more efficient!
```

**Option C: Mixed (10 HP, 15 Defense)**
```
Stats:
- 200 HP (100 base + 100)
- 20 Defense (5 base + 15)

vs 55 Attack opponent:
Reduction = 20 * 0.5 / 55 = 18.2%
EHP = 200 / (1 - 0.182) = 244.5

Result: 244.5 effective HP
Cost: 25 points
Efficiency: 9.8 EHP per point

Better than pure defense, worse than pure HP!
```

**Conclusion:** Pure HP stacking is mathematically superior!

---

## 🎯 **OPTIMAL STAT DISTRIBUTION MATH**

### **Finding the Sweet Spot**

**Question:** With 50 points, what's the optimal split for max combat power?

**Variables:**
- Attack Points (A)
- HP Points (H)
- Defense Points (D)
- A + H + D = 50

**Combat Power Formula:**
```
Combat Power = (DPS × Survivability)^0.5
DPS = (15 + A*2) × (1 + crit_bonus)
Survivability = EHP = (100 + H*10) / (1 - D*0.5/enemy_attack)
```

**Testing Different Distributions:**

```
Pure Attack (A=50, H=0, D=0):
DPS = 115
EHP = 104.7
Power = (115 * 104.7)^0.5 = 109.7

Pure HP (A=0, H=50, D=0):
DPS = 15
EHP = 550
Power = (15 * 550)^0.5 = 90.8

Pure Defense (A=0, H=0, D=50):
DPS = 15
EHP = 137.5
Power = (15 * 137.5)^0.5 = 45.4

Balanced (A=16, H=17, D=17):
DPS = 47
EHP = 307
Power = (47 * 307)^0.5 = 120.1

Bruiser (A=20, H=10, D=10, Crit=10):
DPS = 59.8
EHP = 226
Power = (59.8 * 226)^0.5 = 116.3

Offensive (A=30, H=10, D=10):
DPS = 75
EHP = 226
Power = (75 * 226)^0.5 = 130.2

Optimal (A=25, H=12, D=13):
DPS = 65
EHP = 265
Power = (65 * 265)^0.5 = 131.2
```

**Winner:** Offensive builds (60-65% attack) with some HP/Defense (35-40%)

**Why Bruiser Wins Despite Lower Math Score?**
- Crit provides burst damage (not captured in average DPS)
- More consistent than pure offense
- Better matchups against specific builds
- 99.8% win rate proves real-world > theory!

---

## 🔬 **DIMINISHING RETURNS ANALYSIS**

### **Why Stacking One Stat Fails**

**Attack Power (Diminishing Returns on Overkill)**
```
Points | Attack | vs 100 HP | Overkill
0      | 15     | Kills in 7 hits | 0
10     | 35     | Kills in 3 hits | 5 damage wasted
20     | 55     | Kills in 2 hits | 10 damage wasted
30     | 75     | Kills in 2 hits | 50 damage wasted!
40     | 95     | Kills in 2 hits | 90 damage wasted!

Diminishing returns after 2-hit threshold!
```

**HP (Linear Returns)**
```
Points | HP  | vs 50 DPS | Survives
0      | 100 | 2 hits    | 2 turns
10     | 180 | 3.6 hits  | 3.6 turns
20     | 260 | 5.2 hits  | 5.2 turns
30     | 340 | 6.8 hits  | 6.8 turns
40     | 420 | 8.4 hits  | 8.4 turns

Linear scaling, no diminishing returns!
```

**Defense (Diminishing Returns from Cap)**
```
Points | Defense | vs 50 Attack | Reduction | Effective
0      | 5       | 5%          | 5%        | 100%
10     | 15      | 15%         | 15%       | 150%
20     | 25      | 25%         | 25%       | 200%
30     | 35      | 35%         | 35%       | 250%
40     | 45      | 45%         | 45%       | 300%
50     | 55      | 55%         | 55%       | 350%

Hits 75% cap at ~75 defense
Diminishing returns after cap!
```

**Conclusion:** HP has best scaling, Attack has overkill waste, Defense hits cap.

---

## 💡 **KEY INSIGHTS FOR PLAYERS**

### **1. Balance > Specialization**
```
Bruiser (balanced): 99.8% WR
Pure Attack (specialized): 46% WR

Math: Having weaknesses is fatal
You die before using your strength
```

### **2. HP > Defense (Currently)**
```
HP efficiency: 14.7 EHP per point
Defense efficiency: 5.5 EHP per point

Math: HP scales linearly, Defense has cap
HP is 2.67x better value
```

### **3. Crit Needs Attack**
```
40% crit with 45 attack: 54 DPS
10% crit with 75 attack: 78.75 DPS

Math: Crit is a multiplier
Multiply high base = better output
```

### **4. Speed Without Damage = Useless**
```
Going first with 35 attack: Lose
Going second with 55 attack: Win

Math: Turn order < DPS difference
Can't win if you can't kill
```

### **5. Spell Power Broken = Build Broken**
```
0 spell power: 55 DPS
50 spell power: 25 DPS (!)

Math: Non-functional stat = wasted points
Fix required for viability
```

---

## 🎓 **CONCLUSION: THE GOLDEN RULES**

1. **Invest in Offense (40-50% of points)**
   - Attack or Spell Power
   - Need to kill opponent

2. **Invest in Survivability (40-50% of points)**
   - HP > Defense (until defense buffed)
   - Need to survive long enough to kill

3. **Utility Stats Need Support (10-20% of points)**
   - Crit needs Attack
   - Speed needs Damage Bonus
   - Defense needs HP

4. **Avoid Pure Specialization**
   - No 100% offense (die too fast)
   - No 100% defense (can't kill)
   - Balance is king

5. **Math Doesn't Lie**
   - Test your builds
   - Calculate EHP and DPS
   - TTK determines winner

**The Formula for Success:**
```
Winning Build = High DPS + High EHP + No Major Weakness

Specifically:
- 45-65 Attack (or equivalent spell)
- 200-300 HP (or equivalent EHP)
- 10-20 Defense
- 15-25% Crit
- 10-20 Speed (after buff)
```
