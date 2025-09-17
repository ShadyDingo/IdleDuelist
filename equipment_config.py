#!/usr/bin/env python3
"""
Equipment Configuration System for Idle Duelist
This file provides an extensible framework for adding new weapons and armor
"""

# Weapon Categories - Easy to extend
WEAPON_CATEGORIES = {
    'fast': {
        'name': 'Fast Weapons',
        'description': 'High speed, high crit chance, low damage',
        'base_stats': {'speed_bonus': 5, 'crit_chance': 0.2, 'damage': 8}
    },
    'balanced': {
        'name': 'Balanced Weapons', 
        'description': 'Moderate stats across the board',
        'base_stats': {'speed_bonus': 2, 'crit_chance': 0.15, 'damage': 12}
    },
    'heavy': {
        'name': 'Heavy Weapons',
        'description': 'High damage, low speed, armor penetration',
        'base_stats': {'speed_bonus': -4, 'crit_chance': 0.05, 'damage': 16, 'armor_penetration': 6}
    },
    'defensive': {
        'name': 'Defensive Weapons',
        'description': 'Low damage, high defense bonus',
        'base_stats': {'speed_bonus': -2, 'crit_chance': 0.0, 'damage': 4, 'defense_bonus': 6}
    },
    'ranged': {
        'name': 'Ranged Weapons',
        'description': 'Medium damage, high accuracy, no melee bonus',
        'base_stats': {'speed_bonus': 1, 'crit_chance': 0.18, 'damage': 10, 'accuracy': 0.9}
    }
}

# Armor Categories - Easy to extend
ARMOR_CATEGORIES = {
    'cloth': {
        'name': 'Cloth Armor',
        'description': 'High speed, low defense, good for dodging builds',
        'base_stats': {'speed': 6, 'defense': 1}
    },
    'leather': {
        'name': 'Leather Armor',
        'description': 'Balanced speed and defense',
        'base_stats': {'speed': 1, 'defense': 3}
    },
    'metal': {
        'name': 'Metal Armor',
        'description': 'Low speed, high defense, tank builds',
        'base_stats': {'speed': -5, 'defense': 7}
    },
    'enchanted': {
        'name': 'Enchanted Armor',
        'description': 'Magical armor with special properties',
        'base_stats': {'speed': 0, 'defense': 4, 'mana_bonus': 20}
    }
}

# Equipment Slots
EQUIPMENT_SLOTS = {
    'armor': ['helmet', 'armor', 'gloves', 'pants', 'boots'],
    'weapons': ['mainhand', 'offhand'],
    'jewelry': ['ring', 'amulet', 'bracelet']  # Future expansion
}

# Rarity System - Easy to extend
RARITY_SYSTEM = {
    'normal': {
        'name': 'Normal',
        'color': (0.8, 0.8, 0.8, 1),
        'stat_multiplier': 1.0,
        'special_properties': 0
    },
    'uncommon': {
        'name': 'Uncommon',
        'color': (0.2, 0.8, 0.2, 1),
        'stat_multiplier': 1.2,
        'special_properties': 1
    },
    'rare': {
        'name': 'Rare',
        'color': (0.2, 0.2, 0.8, 1),
        'stat_multiplier': 1.5,
        'special_properties': 2
    },
    'epic': {
        'name': 'Epic',
        'color': (0.8, 0.2, 0.8, 1),
        'stat_multiplier': 1.8,
        'special_properties': 3
    },
    'legendary': {
        'name': 'Legendary',
        'color': (0.8, 0.8, 0.2, 1),
        'stat_multiplier': 2.0,
        'special_properties': 4
    },
    'mythic': {
        'name': 'Mythic',
        'color': (0.8, 0.4, 0.2, 1),
        'stat_multiplier': 2.5,
        'special_properties': 5
    }
}

def create_weapon(weapon_id: str, name: str, category: str, rarity: str = 'normal', 
                 two_handed: bool = False, image_path: str = None, **custom_stats):
    """
    Create a new weapon with the specified properties
    
    Args:
        weapon_id: Unique identifier for the weapon
        name: Display name
        category: Weapon category (fast, balanced, heavy, defensive, ranged)
        rarity: Rarity level (normal, uncommon, rare, epic, legendary, mythic)
        two_handed: Whether the weapon is two-handed
        image_path: Path to weapon image
        **custom_stats: Additional custom stats
    
    Returns:
        Dictionary containing weapon data
    """
    if category not in WEAPON_CATEGORIES:
        raise ValueError(f"Invalid weapon category: {category}")
    
    if rarity not in RARITY_SYSTEM:
        raise ValueError(f"Invalid rarity: {rarity}")
    
    # Get base stats from category
    base_stats = WEAPON_CATEGORIES[category]['base_stats'].copy()
    
    # Apply rarity multiplier
    rarity_data = RARITY_SYSTEM[rarity]
    for stat in base_stats:
        if isinstance(base_stats[stat], (int, float)):
            base_stats[stat] = int(base_stats[stat] * rarity_data['stat_multiplier'])
    
    # Add custom stats
    base_stats.update(custom_stats)
    
    # Add required fields
    base_stats.update({
        'name': name,
        'two_handed': two_handed,
        'image': image_path or f'assets/weapons/{weapon_id}.png',
        'category': category,
        'rarity': rarity
    })
    
    return base_stats

def create_armor(armor_id: str, name: str, slot: str, category: str, 
                rarity: str = 'normal', image_path: str = None, **custom_stats):
    """
    Create a new armor piece with the specified properties
    
    Args:
        armor_id: Unique identifier for the armor
        name: Display name
        slot: Equipment slot (helmet, armor, gloves, pants, boots)
        category: Armor category (cloth, leather, metal, enchanted)
        rarity: Rarity level
        image_path: Path to armor image
        **custom_stats: Additional custom stats
    
    Returns:
        Dictionary containing armor data
    """
    if slot not in EQUIPMENT_SLOTS['armor']:
        raise ValueError(f"Invalid armor slot: {slot}")
    
    if category not in ARMOR_CATEGORIES:
        raise ValueError(f"Invalid armor category: {category}")
    
    if rarity not in RARITY_SYSTEM:
        raise ValueError(f"Invalid rarity: {rarity}")
    
    # Get base stats from category
    base_stats = ARMOR_CATEGORIES[category]['base_stats'].copy()
    
    # Apply rarity multiplier
    rarity_data = RARITY_SYSTEM[rarity]
    for stat in base_stats:
        if isinstance(base_stats[stat], (int, float)):
            base_stats[stat] = int(base_stats[stat] * rarity_data['stat_multiplier'])
    
    # Add custom stats
    base_stats.update(custom_stats)
    
    # Add required fields
    base_stats.update({
        'name': name,
        'image': image_path or f'assets/armor/{armor_id}.png',
        'slot': slot,
        'category': category,
        'rarity': rarity
    })
    
    return base_stats

# Example usage and predefined equipment
def get_extended_equipment_data():
    """
    Get extended equipment data with new weapons and armor
    This function demonstrates how to easily add new equipment
    """
    
    # New weapons using the framework
    new_weapons = {
        # Fast weapons
        'weapon_rapier': create_weapon(
            'weapon_rapier', 'Rapier', 'fast', 'uncommon',
            image_path='assets/weapons/weapon_rapier.png',
            armor_penetration=3  # Custom stat
        ),
        
        'weapon_dagger_poisoned': create_weapon(
            'weapon_dagger_poisoned', 'Poisoned Dagger', 'fast', 'rare',
            image_path='assets/weapons/weapon_dagger_poisoned.png',
            poison_chance=0.2  # Custom stat
        ),
        
        # Heavy weapons
        'weapon_greatsword': create_weapon(
            'weapon_greatsword', 'Greatsword', 'heavy', 'rare',
            two_handed=True,
            image_path='assets/weapons/weapon_greatsword.png',
            cleave_damage=5  # Custom stat
        ),
        
        'weapon_warhammer': create_weapon(
            'weapon_warhammer', 'Warhammer', 'heavy', 'epic',
            two_handed=True,
            image_path='assets/weapons/weapon_warhammer.png',
            stun_chance=0.15  # Custom stat
        ),
        
        # Ranged weapons
        'weapon_longbow': create_weapon(
            'weapon_longbow', 'Longbow', 'ranged', 'uncommon',
            two_handed=True,
            image_path='assets/weapons/weapon_longbow.png',
            range_bonus=2  # Custom stat
        ),
        
        'weapon_crossbow_heavy': create_weapon(
            'weapon_crossbow_heavy', 'Heavy Crossbow', 'ranged', 'rare',
            two_handed=True,
            image_path='assets/weapons/weapon_crossbow_heavy.png',
            armor_penetration=8  # Custom stat
        ),
        
        # Defensive weapons
        'weapon_tower_shield': create_weapon(
            'weapon_tower_shield', 'Tower Shield', 'defensive', 'rare',
            image_path='assets/weapons/weapon_tower_shield.png',
            block_chance=0.3  # Custom stat
        )
    }
    
    # New armor using the framework
    new_armor = {
        # Enchanted armor
        'enchanted_helmet': create_armor(
            'enchanted_helmet', 'Enchanted Helmet', 'helmet', 'enchanted', 'rare',
            image_path='assets/armor/enchanted_helmet.png',
            mana_bonus=25  # Custom stat
        ),
        
        'enchanted_armor': create_armor(
            'enchanted_armor', 'Enchanted Armor', 'armor', 'enchanted', 'epic',
            image_path='assets/armor/enchanted_armor.png',
            spell_resistance=0.2  # Custom stat
        ),
        
        # Specialized armor
        'assassin_gloves': create_armor(
            'assassin_gloves', 'Assassin Gloves', 'gloves', 'leather', 'rare',
            image_path='assets/armor/assassin_gloves.png',
            crit_chance_bonus=0.1  # Custom stat
        ),
        
        'berserker_boots': create_armor(
            'berserker_boots', 'Berserker Boots', 'boots', 'leather', 'uncommon',
            image_path='assets/armor/berserker_boots.png',
            speed_bonus=8  # Custom stat
        )
    }
    
    return {
        'weapons': new_weapons,
        'armor': new_armor
    }

# Function to easily add equipment to the game
def add_equipment_to_game(equipment_data, existing_equipment):
    """
    Add new equipment to existing equipment data
    
    Args:
        equipment_data: New equipment data from get_extended_equipment_data()
        existing_equipment: Existing EQUIPMENT_DATA dictionary
    
    Returns:
        Updated equipment data
    """
    updated_equipment = existing_equipment.copy()
    
    # Add new weapons
    if 'weapons' in equipment_data:
        updated_equipment['weapons'].update(equipment_data['weapons'])
    
    # Add new armor
    if 'armor' in equipment_data:
        updated_equipment['armor'].update(equipment_data['armor'])
    
    return updated_equipment

# Example of how to add a single new weapon quickly
def add_quick_weapon(weapon_id, name, category='balanced', **stats):
    """Quick function to add a single weapon"""
    return create_weapon(weapon_id, name, category, **stats)

# Example of how to add a single new armor piece quickly  
def add_quick_armor(armor_id, name, slot, category='leather', **stats):
    """Quick function to add a single armor piece"""
    return create_armor(armor_id, name, slot, category, **stats)

if __name__ == "__main__":
    # Example usage
    print("Equipment Configuration System")
    print("=" * 40)
    
    # Create a new weapon
    new_sword = create_weapon(
        'weapon_flame_sword', 'Flame Sword', 'balanced', 'epic',
        fire_damage=10, fire_chance=0.3
    )
    print("New weapon created:", new_sword['name'])
    
    # Create new armor
    new_helmet = create_armor(
        'helmet_of_wisdom', 'Helmet of Wisdom', 'helmet', 'enchanted', 'legendary',
        mana_bonus=50, wisdom_bonus=5
    )
    print("New armor created:", new_helmet['name'])
    
    print("\nFramework ready for easy equipment expansion!")





