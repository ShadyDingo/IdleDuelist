# Rarity Asset Naming Guide

## 🎨 **Recommended Approach: Pre-made Rarity Versions**

Instead of trying to layer rarity borders over equipment images, create separate versions of each weapon and armor piece with the rarity border already applied.

## 📁 **New File Naming Convention**

### **Weapons:**
```
weapon_sword_normal.png
weapon_sword_uncommon.png
weapon_sword_rare.png
weapon_sword_epic.png
weapon_sword_legendary.png
weapon_sword_mythic.png
```

### **Armor:**
```
armor_cloth_helmet_normal.png
armor_cloth_helmet_uncommon.png
armor_cloth_helmet_rare.png
armor_cloth_helmet_epic.png
armor_cloth_helmet_legendary.png
armor_cloth_helmet_mythic.png
```

## 🎯 **Benefits of This Approach**

1. **Perfect Visual Control** - You can ensure borders fit exactly right
2. **Consistent Styling** - All items have uniform border appearance
3. **Better Performance** - No complex layering operations
4. **Easier Maintenance** - Simpler asset management
5. **No Border Issues** - Borders are part of the image, not overlays

## 📋 **Complete Asset List Needed**

### **Weapons (9 types × 6 rarities = 54 files):**
- sword_normal.png, sword_uncommon.png, sword_rare.png, sword_epic.png, sword_legendary.png, sword_mythic.png
- axe_normal.png, axe_uncommon.png, axe_rare.png, axe_epic.png, axe_legendary.png, axe_mythic.png
- bow_normal.png, bow_uncommon.png, bow_rare.png, bow_epic.png, bow_legendary.png, bow_mythic.png
- crossbow_normal.png, crossbow_uncommon.png, crossbow_rare.png, crossbow_epic.png, crossbow_legendary.png, crossbow_mythic.png
- knife_normal.png, knife_uncommon.png, knife_rare.png, knife_epic.png, knife_legendary.png, knife_mythic.png
- mace_normal.png, mace_uncommon.png, mace_rare.png, mace_epic.png, mace_legendary.png, mace_mythic.png
- hammer_normal.png, hammer_uncommon.png, hammer_rare.png, hammer_epic.png, hammer_legendary.png, hammer_mythic.png
- shield_normal.png, shield_uncommon.png, shield_rare.png, shield_epic.png, shield_legendary.png, shield_mythic.png
- staff_normal.png, staff_uncommon.png, staff_rare.png, staff_epic.png, staff_legendary.png, staff_mythic.png

### **Armor (15 types × 6 rarities = 90 files):**
- cloth_helmet_normal.png, cloth_helmet_uncommon.png, cloth_helmet_rare.png, cloth_helmet_epic.png, cloth_helmet_legendary.png, cloth_helmet_mythic.png
- cloth_armor_normal.png, cloth_armor_uncommon.png, cloth_armor_rare.png, cloth_armor_epic.png, cloth_armor_legendary.png, cloth_armor_mythic.png
- cloth_pants_normal.png, cloth_pants_uncommon.png, cloth_pants_rare.png, cloth_pants_epic.png, cloth_pants_legendary.png, cloth_pants_mythic.png
- cloth_boots_normal.png, cloth_boots_uncommon.png, cloth_boots_rare.png, cloth_boots_epic.png, cloth_boots_legendary.png, cloth_boots_mythic.png
- cloth_gloves_normal.png, cloth_gloves_uncommon.png, cloth_gloves_rare.png, cloth_gloves_epic.png, cloth_gloves_legendary.png, cloth_gloves_mythic.png
- leather_helmet_normal.png, leather_helmet_uncommon.png, leather_helmet_rare.png, leather_helmet_epic.png, leather_helmet_legendary.png, leather_helmet_mythic.png
- leather_armor_normal.png, leather_armor_uncommon.png, leather_armor_rare.png, leather_armor_epic.png, leather_armor_legendary.png, leather_armor_mythic.png
- leather_pants_normal.png, leather_pants_uncommon.png, leather_pants_rare.png, leather_pants_epic.png, leather_pants_legendary.png, leather_pants_mythic.png
- leather_boots_normal.png, leather_boots_uncommon.png, leather_boots_rare.png, leather_boots_epic.png, leather_boots_legendary.png, leather_boots_mythic.png
- leather_gloves_normal.png, leather_gloves_uncommon.png, leather_gloves_rare.png, leather_gloves_epic.png, leather_gloves_legendary.png, leather_gloves_mythic.png
- metal_helmet_normal.png, metal_helmet_uncommon.png, metal_helmet_rare.png, metal_helmet_epic.png, metal_helmet_legendary.png, metal_helmet_mythic.png
- metal_armor_normal.png, metal_armor_uncommon.png, metal_armor_rare.png, metal_armor_epic.png, metal_armor_legendary.png, metal_armor_mythic.png
- metal_pants_normal.png, metal_pants_uncommon.png, metal_pants_rare.png, metal_pants_epic.png, metal_pants_legendary.png, metal_pants_mythic.png
- metal_boots_normal.png, metal_boots_uncommon.png, metal_boots_rare.png, metal_boots_epic.png, metal_boots_legendary.png, metal_boots_mythic.png
- metal_gloves_normal.png, metal_gloves_uncommon.png, metal_gloves_rare.png, metal_gloves_epic.png, metal_gloves_legendary.png, metal_gloves_mythic.png

## 🔄 **Fallback System**

The asset manager will:
1. **First try** the rarity-specific version (e.g., `weapon_sword_rare.png`)
2. **Fall back** to the base version (e.g., `weapon_sword.png`) if rarity version doesn't exist
3. **Use emoji fallback** if neither exists

## 🎨 **Design Tips**

1. **Border Colors by Rarity:**
   - Normal: Gray/Silver
   - Uncommon: Green
   - Rare: Blue
   - Epic: Purple
   - Legendary: Orange/Gold
   - Mythic: Red/Pink

2. **Border Thickness:** Make borders thick enough to be visible but not overwhelming

3. **Consistent Size:** Keep all images the same size for uniform appearance

4. **Transparency:** Use PNG format with transparency for clean borders

## 📊 **Total Files Needed**
- **Weapons**: 54 files (9 types × 6 rarities)
- **Armor**: 90 files (15 types × 6 rarities)
- **Total**: 144 rarity-specific equipment images

This approach will give you perfect control over the visual appearance and eliminate any border overlay issues!







