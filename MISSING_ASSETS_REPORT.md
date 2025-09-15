# Missing Assets Report for Idle Duelist

## 🎯 Assets You Need to Add

### ⚔️ Weapons (9 missing)
You have weapon images but they're named with prefixes. The system expects:
- `sword.png` (you have `weapon_sword.png` ✅)
- `axe.png` (you have `weapon_axe.png` ✅)
- `bow.png` (you have `weapon_bow.PNG` ✅)
- `crossbow.png` (you have `weapon_crossbow.PNG` ✅)
- `knife.png` (you have `weapon_knife.PNG` ✅)
- `mace.png` (you have `weapon_mace.PNG` ✅)
- `hammer.png` (you have `weapon_hammer.png` ✅)
- `shield.png` (you have `weapon_shield.PNG` ✅)
- `staff.png` (you have `weapon_staff.png` ✅)

**Status: All weapon assets are present! ✅**

### 🛡️ Armor (15 missing)
You only have 3 armor images but need 15 for different slots:

**Missing Armor Slots:**
- `cloth_helmet.png` - Cloth helmet
- `cloth_chest.png` - Cloth chest (you have `armor_cloth.PNG` but need specific slot)
- `cloth_legs.png` - Cloth legs
- `cloth_boots.png` - Cloth boots
- `cloth_gloves.png` - Cloth gloves
- `leather_helmet.png` - Leather helmet
- `leather_chest.png` - Leather chest (you have `armor_leather.PNG` but need specific slot)
- `leather_legs.png` - Leather legs
- `leather_boots.png` - Leather boots
- `leather_gloves.png` - Leather gloves
- `metal_helmet.png` - Metal helmet
- `metal_chest.png` - Metal chest (you have `armor_metal.png` but need specific slot)
- `metal_legs.png` - Metal legs
- `metal_boots.png` - Metal boots
- `metal_gloves.png` - Metal gloves

**Status: Need 12 more armor slot images ⚠️**

### ✨ Abilities (15 missing)
You have ability images but they're named with prefixes. The system expects:
- `divine_strike.png` (you have `ability_divine_strike.PNG` ✅)
- `shield_of_faith.png` (you have `ability_shield_of_faith.PNG` ✅)
- `healing_light.png` (you have `ability_healing_light.PNG` ✅)
- `righteous_fury.png` (you have `ability_righteous_fury.PNG` ✅)
- `purification.png` (you have `ability_purification.PNG` ✅)
- `shadow_strike.png` (you have `ability_shadow_strike.PNG` ✅)
- `vanish.png` (you have `ability_vanish.PNG` ✅)
- `poison_blade.png` (you have `ability_poison_blade.png` ✅)
- `assassinate.png` (you have `ability_assassinate.PNG` ✅)
- `shadow_clone.png` (you have `ability_shadow_clone.PNG` ✅)
- `natures_wrath.png` (you have `ability_natures_wrath.png` ✅)
- `thorn_barrier.png` (you have `ability_thorn_barrier.PNG` ✅)
- `wild_growth.png` (you have `ability_wild_growth.PNG` ✅)
- `earthquake.png` (you have `ability_earthquake.PNG` ✅)
- `spirit_form.png` (you have `ability_spirit_form.PNG` ✅)

**Status: All ability assets are present! ✅**

### 📊 UI Elements (2 missing)
- `constitution.png` - Constitution stat icon
- `victory_points.png` - Victory points icon

**Status: Need 2 more UI icons ⚠️**

### ⭐ Rarity Borders (6 missing)
You have rarity images but they're named with prefixes. The system expects:
- `normal.png` (you have `rarity_normal.png` ✅)
- `uncommon.png` (you have `rarity_uncommon.png` ✅)
- `rare.png` (you have `rarity_rare.png` ✅)
- `epic.png` (you have `rarity_epic.png` ✅)
- `legendary.png` (you have `rarity_legendary.png` ✅)
- `mythic.png` (you have `rarity_mythic.png` ✅)

**Status: All rarity assets are present! ✅**

### 🏛️ Factions (3 missing)
- `order_of_the_silver_crusade.png` - Order faction icon
- `shadow_covenant.png` - Shadow faction icon
- `wilderness_tribe.png` - Wilderness faction icon

**Status: Need 3 faction images ⚠️**

## 📋 Summary
- **Total Missing: 17 assets**
- **Armor Slots: 12 missing** (most important for equipment system)
- **UI Icons: 2 missing**
- **Faction Images: 3 missing**

## 🎨 Asset Naming Convention
The asset manager now handles prefixes automatically, so your current naming is fine:
- `weapon_sword.png` → loads as `sword`
- `ability_divine_strike.PNG` → loads as `divine_strike`
- `rarity_epic.png` → loads as `epic`

## 🔧 Border Overlay Issue
The rarity borders not covering weapons/armor properly is likely due to:
1. **Size mismatch** - borders and equipment images have different dimensions
2. **Transparency** - borders need proper alpha channels
3. **Positioning** - borders need to be centered over equipment

**Recommendation:** Create borders that are slightly larger than your equipment images (e.g., if equipment is 64x64, make borders 80x80 with transparent center).





