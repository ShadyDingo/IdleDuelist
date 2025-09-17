# Equipment Expansion Guide for Idle Duelist

This guide shows you how to easily add new weapons and armor to Idle Duelist using the extensible framework.

## 🎯 Quick Start

### Adding a New Weapon

```python
# Import the equipment configuration system
from equipment_config import create_weapon, add_quick_weapon

# Method 1: Using the full create_weapon function
new_weapon = create_weapon(
    weapon_id='weapon_flame_sword',
    name='Flame Sword',
    category='balanced',  # fast, balanced, heavy, defensive, ranged
    rarity='epic',        # normal, uncommon, rare, epic, legendary, mythic
    two_handed=False,
    image_path='assets/weapons/flame_sword.png',
    fire_damage=10,       # Custom stat
    fire_chance=0.3       # Custom stat
)

# Method 2: Using the quick function
quick_weapon = add_quick_weapon(
    'weapon_ice_dagger', 'Ice Dagger', 'fast',
    ice_damage=8, freeze_chance=0.2
)
```

### Adding New Armor

```python
from equipment_config import create_armor, add_quick_armor

# Method 1: Using the full create_armor function
new_armor = create_armor(
    armor_id='helmet_of_wisdom',
    name='Helmet of Wisdom',
    slot='helmet',        # helmet, armor, gloves, pants, boots
    category='enchanted', # cloth, leather, metal, enchanted
    rarity='legendary',
    image_path='assets/armor/wisdom_helmet.png',
    mana_bonus=50,        # Custom stat
    wisdom_bonus=5        # Custom stat
)

# Method 2: Using the quick function
quick_armor = add_quick_armor(
    'boots_of_speed', 'Boots of Speed', 'boots', 'leather',
    speed_bonus=15, dodge_bonus=0.1
)
```

## 🏗️ Framework Components

### Weapon Categories

| Category | Description | Base Stats |
|----------|-------------|------------|
| `fast` | High speed, high crit chance, low damage | Speed: +5, Crit: 20%, Damage: 8 |
| `balanced` | Moderate stats across the board | Speed: +2, Crit: 15%, Damage: 12 |
| `heavy` | High damage, low speed, armor penetration | Speed: -4, Crit: 5%, Damage: 16, Pen: 6 |
| `defensive` | Low damage, high defense bonus | Speed: -2, Crit: 0%, Damage: 4, Def: +6 |
| `ranged` | Medium damage, high accuracy | Speed: +1, Crit: 18%, Damage: 10, Acc: 90% |

### Armor Categories

| Category | Description | Base Stats |
|----------|-------------|------------|
| `cloth` | High speed, low defense | Speed: +6, Defense: 1 |
| `leather` | Balanced speed and defense | Speed: +1, Defense: 3 |
| `metal` | Low speed, high defense | Speed: -5, Defense: 7 |
| `enchanted` | Magical armor with special properties | Speed: 0, Defense: 4, Mana: +20 |

### Rarity System

| Rarity | Color | Stat Multiplier | Special Properties |
|--------|-------|-----------------|-------------------|
| `normal` | Gray | 1.0x | 0 |
| `uncommon` | Green | 1.2x | 1 |
| `rare` | Blue | 1.5x | 2 |
| `epic` | Purple | 1.8x | 3 |
| `legendary` | Gold | 2.0x | 4 |
| `mythic` | Orange | 2.5x | 5 |

## 🔧 Integration Steps

### Step 1: Add Equipment to Game Data

```python
# In idle_duelist.py, import the equipment config
from equipment_config import get_extended_equipment_data, add_equipment_to_game

# Get new equipment
new_equipment = get_extended_equipment_data()

# Add to existing equipment data
EQUIPMENT_DATA = add_equipment_to_game(new_equipment, EQUIPMENT_DATA)
```

### Step 2: Add Asset Files

1. Place weapon images in `assets/weapons/`
2. Place armor images in `assets/armor/`
3. Use consistent naming: `weapon_[name].png`, `armor_[slot]_[type].png`

### Step 3: Update UI (if needed)

The existing UI will automatically display new equipment. No changes needed unless you want custom display logic.

## 📝 Examples

### Example 1: Magic Staff

```python
magic_staff = create_weapon(
    'weapon_magic_staff',
    'Magic Staff',
    'balanced',
    'rare',
    two_handed=True,
    image_path='assets/weapons/magic_staff.png',
    mana_bonus=30,
    spell_power=15,
    elemental_damage=8
)
```

### Example 2: Dragon Scale Armor

```python
dragon_armor = create_armor(
    'dragon_scale_armor',
    'Dragon Scale Armor',
    'armor',
    'metal',
    'mythic',
    image_path='assets/armor/dragon_scale_armor.png',
    fire_resistance=0.5,
    dragon_blessing=True,
    intimidation=10
)
```

### Example 3: Jewelry (Future Expansion)

```python
# For future jewelry system
magic_ring = create_armor(
    'ring_of_power',
    'Ring of Power',
    'ring',  # New slot
    'enchanted',
    'legendary',
    image_path='assets/jewelry/ring_of_power.png',
    all_stats_bonus=5,
    special_ability='power_surge'
)
```

## 🎮 Custom Stats

You can add any custom stats to equipment:

### Combat Stats
- `damage_bonus`: Additional damage
- `crit_chance_bonus`: Additional crit chance
- `speed_bonus`: Additional speed
- `defense_bonus`: Additional defense
- `dodge_bonus`: Additional dodge chance

### Elemental Stats
- `fire_damage`: Fire damage per hit
- `ice_damage`: Ice damage per hit
- `lightning_damage`: Lightning damage per hit
- `poison_damage`: Poison damage per hit

### Resistance Stats
- `fire_resistance`: Reduce fire damage
- `ice_resistance`: Reduce ice damage
- `lightning_resistance`: Reduce lightning damage
- `poison_resistance`: Reduce poison damage

### Special Stats
- `mana_bonus`: Additional mana
- `health_bonus`: Additional health
- `lifesteal`: Heal on damage dealt
- `spell_power`: Increase ability damage
- `cooldown_reduction`: Reduce ability cooldowns

## 🚀 Advanced Features

### Weapon-Specific Abilities

```python
# Weapons can grant special abilities
sword_of_storms = create_weapon(
    'weapon_storm_sword',
    'Sword of Storms',
    'balanced',
    'epic',
    image_path='assets/weapons/storm_sword.png',
    lightning_strike=True,  # Special ability
    storm_call_cooldown=5   # Ability cooldown
)
```

### Set Bonuses

```python
# Equipment sets can provide bonuses
dragon_set_helmet = create_armor(
    'dragon_set_helmet',
    'Dragon Helmet',
    'helmet',
    'metal',
    'legendary',
    image_path='assets/armor/dragon_helmet.png',
    set_name='dragon_set',  # Set identifier
    set_pieces=4            # Total pieces in set
)
```

## 🔄 Updating Existing Equipment

To modify existing equipment:

```python
# Update existing weapon
EQUIPMENT_DATA['weapons']['weapon_sword']['damage'] = 15
EQUIPMENT_DATA['weapons']['weapon_sword']['new_stat'] = 10

# Update existing armor
EQUIPMENT_DATA['armor']['cloth_armor']['speed'] = 15
EQUIPMENT_DATA['armor']['cloth_armor']['special_property'] = True
```

## 📱 Mobile Considerations

- Keep image sizes reasonable (64x64 to 128x128 pixels)
- Use transparent backgrounds for better UI integration
- Test on different screen sizes
- Consider touch-friendly UI elements

## 🎯 Best Practices

1. **Naming Convention**: Use descriptive, consistent names
2. **Balancing**: Test new equipment in combat to ensure balance
3. **Assets**: Use high-quality, consistent art style
4. **Documentation**: Document custom stats and their effects
5. **Testing**: Test thoroughly before releasing

## 🐛 Troubleshooting

### Common Issues

1. **Missing Images**: Ensure image paths are correct
2. **Invalid Categories**: Use only predefined categories
3. **Stat Conflicts**: Avoid conflicting stat names
4. **Performance**: Don't add too many items at once

### Debug Tips

```python
# Check if equipment was added correctly
print(EQUIPMENT_DATA['weapons']['your_new_weapon'])

# Validate equipment data
from equipment_config import create_weapon
try:
    test_weapon = create_weapon('test', 'Test', 'invalid_category')
except ValueError as e:
    print(f"Error: {e}")
```

---

## 🎉 Conclusion

This framework makes it incredibly easy to add new equipment to Idle Duelist:

- **Simple Functions**: Just call `create_weapon()` or `create_armor()`
- **Automatic Balancing**: Rarity system handles stat scaling
- **Flexible Stats**: Add any custom stats you need
- **Future-Proof**: Easy to extend with new categories and features

Happy equipment crafting! ⚔️🛡️




