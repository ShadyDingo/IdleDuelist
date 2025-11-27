#!/usr/bin/env python3
"""
IdleDuelist Game Logic
Core game mechanics, stat calculations, and combat resolution
"""

import random
import math
from typing import Dict, List, Tuple, Optional

# Primary stat names
PRIMARY_STATS = ['might', 'agility', 'vitality', 'intellect', 'wisdom', 'charisma']

# Equipment slots
EQUIPMENT_SLOTS = [
    'helmet', 'chest', 'legs', 'boots', 'gloves',
    'main_hand', 'off_hand'
]

# Weapon types and attack speeds (seconds per attack)
WEAPON_TYPES = ['sword', 'staff', 'bow', 'dagger', 'mace']

# Weapon categories: 'two_handed' or 'one_handed'
WEAPON_CATEGORIES = {
    'sword': 'one_handed',
    'staff': 'one_handed',  # Can be used with shield or dual-wielded
    'bow': 'two_handed',    # Cannot use shield, requires both hands
    'dagger': 'one_handed',
    'mace': 'one_handed'
}

# Base attack speeds (seconds per attack) - for single weapon
WEAPON_ATTACK_SPEEDS = {
    'sword': 2.0,
    'staff': 2.5,
    'bow': 1.8,      # 2h weapon, faster to compensate for no shield
    'dagger': 1.5,
    'mace': 2.3
}

# Weapon damage types
WEAPON_DAMAGE_TYPES = {
    'sword': 'physical',
    'staff': 'magical',
    'bow': 'physical',
    'dagger': 'physical',
    'mace': 'physical'
}

# Rarity tiers
RARITIES = ['common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic']
RARITY_WEIGHTS = {
    'common': 1,
    'uncommon': 2,
    'rare': 3,
    'epic': 4,
    'legendary': 5,
    'mythic': 6
}

# Equipment rarity stat ranges
RARITY_STAT_RANGES = {
    'common': {'primary': (1, 3), 'secondary': (0, 0), 'tertiary': (0, 0), 'quaternary': (0, 0)},
    'uncommon': {'primary': (2, 5), 'secondary': (1, 2), 'tertiary': (0, 0), 'quaternary': (0, 0)},
    'rare': {'primary': (4, 8), 'secondary': (2, 4), 'tertiary': (0, 0), 'quaternary': (0, 0)},
    'epic': {'primary': (6, 12), 'secondary': (3, 6), 'tertiary': (1, 3), 'quaternary': (0, 0)},
    'legendary': {'primary': (10, 18), 'secondary': (5, 9), 'tertiary': (2, 5), 'quaternary': (0, 0)},
    'mythic': {'primary': (15, 25), 'secondary': (8, 12), 'tertiary': (4, 8), 'quaternary': (2, 4)}
}


def calculate_exp_for_level(level: int) -> int:
    """Calculate EXP required to reach a specific level"""
    if level <= 1:
        return 0
    return int((level - 1) ** 2.5 * 100)


def calculate_exp_to_next_level(current_level: int) -> int:
    """Calculate EXP needed to reach next level"""
    if current_level >= 100:
        return 0
    return calculate_exp_for_level(current_level + 1) - calculate_exp_for_level(current_level)


def calculate_combat_stats(base_stats: Dict[str, int], equipment_stats: Dict[str, int] = None, 
                          equipment: Dict[str, Dict] = None) -> Dict[str, float]:
    """
    Calculate derived combat stats from primary stats and equipment
    
    Args:
        base_stats: Dictionary with primary stats (might, agility, vitality, intellect, wisdom, charisma)
        equipment_stats: Additional stats from equipment (optional)
        equipment: Equipment dictionary to check for shield/dual wielding bonuses (optional)
    
    Returns:
        Dictionary with all combat stats
    """
    if equipment_stats is None:
        equipment_stats = {}
    if equipment is None:
        equipment = {}
    
    # Combine base and equipment stats
    total_stats = {stat: base_stats.get(stat, 0) + equipment_stats.get(stat, 0) for stat in PRIMARY_STATS}
    
    might = total_stats.get('might', 0)
    agility = total_stats.get('agility', 0)
    vitality = total_stats.get('vitality', 0)
    intellect = total_stats.get('intellect', 0)
    wisdom = total_stats.get('wisdom', 0)
    charisma = total_stats.get('charisma', 0)
    
    # Calculate base derived stats
    base_defense = (vitality * 2) + (might * 0.5)
    
    # Shield provides additional defense (15% of base defense)
    shield_bonus = 0.0
    if has_shield(equipment):
        shield_bonus = base_defense * 0.15
    
    # Bow (2h weapon) gets attack power bonus to compensate for no shield
    # Check if main hand is bow
    main_weapon_type = get_weapon_type(equipment)
    attack_power_bonus = 0.0
    if main_weapon_type == 'bow':
        # Bow gets 20% attack power bonus to compensate for no shield
        base_attack_power = (might * 2) + (agility * 1) + (intellect * 0.5)
        attack_power_bonus = base_attack_power * 0.20
    
    # Calculate derived stats
    combat_stats = {
        'attack_power': (might * 2) + (agility * 1) + (intellect * 0.5) + attack_power_bonus,
        'defense': base_defense + shield_bonus,
        'crit_chance': min((agility * 0.001) + (intellect * 0.0005), 0.50),  # Cap at 50%
        'dodge_chance': min((agility * 0.0015) + (wisdom * 0.0005), 0.25),  # Cap at 25%
        'parry_chance': min((might * 0.001) + (vitality * 0.0005), 0.15),  # Cap at 15%
        'speed': (agility * 1) + (wisdom * 0.5),
        'spell_power': (intellect * 2) + (wisdom * 1),
        'max_hp': 100 + (might * 2) + (vitality * 6),
        'max_mana': 50 + (intellect * 3) + (wisdom * 2),
        'mana_regen_per_second': 1.0 + (wisdom * 0.1),  # Base 1.0 + 0.1 per Wisdom point
        'magic_resistance': (wisdom * 0.5) + (vitality * 0.25),  # Magic resistance from Wisdom and Vitality
        'is_dual_wielding': is_dual_wielding(equipment),
        'has_shield': has_shield(equipment)
    }
    
    return combat_stats


def generate_equipment(slot: str, rarity: str, level: int) -> Dict:
    """
    Generate a random equipment piece
    
    Args:
        slot: Equipment slot name
        rarity: Rarity tier
        level: Character level (affects stat ranges)
    
    Returns:
        Equipment dictionary with stats
    """
    if rarity not in RARITY_STAT_RANGES:
        rarity = 'common'
    
    ranges = RARITY_STAT_RANGES[rarity]
    
    # Level scaling factor (1.0 at level 1, 2.0 at level 100)
    level_scale = 1.0 + ((level - 1) / 99.0)
    
    # Generate stat bonuses
    stats = {}
    
    # Primary stat
    if ranges['primary'][1] > 0:
        primary_stat = random.choice(PRIMARY_STATS)
        base_value = random.randint(ranges['primary'][0], ranges['primary'][1])
        stats[primary_stat] = int(base_value * level_scale)
    
    # Secondary stat
    if ranges['secondary'][1] > 0:
        available_stats = [s for s in PRIMARY_STATS if s not in stats]
        if available_stats:
            secondary_stat = random.choice(available_stats)
            base_value = random.randint(ranges['secondary'][0], ranges['secondary'][1])
            stats[secondary_stat] = int(base_value * level_scale)
    
    # Tertiary stat
    if ranges['tertiary'][1] > 0:
        available_stats = [s for s in PRIMARY_STATS if s not in stats]
        if available_stats:
            tertiary_stat = random.choice(available_stats)
            base_value = random.randint(ranges['tertiary'][0], ranges['tertiary'][1])
            stats[tertiary_stat] = int(base_value * level_scale)
    
    # Quaternary stat (mythic only)
    if ranges['quaternary'][1] > 0:
        available_stats = [s for s in PRIMARY_STATS if s not in stats]
        if available_stats:
            quaternary_stat = random.choice(available_stats)
            base_value = random.randint(ranges['quaternary'][0], ranges['quaternary'][1])
            stats[quaternary_stat] = int(base_value * level_scale)
    
    # Generate equipment name
    slot_names = {
        'helmet': 'Helmet', 'chest': 'Chestplate', 'legs': 'Leggings',
        'boots': 'Boots', 'gloves': 'Gloves',
        'main_hand': 'Weapon', 'off_hand': 'Shield'
    }
    
    rarity_names = {
        'common': 'Common', 'uncommon': 'Uncommon', 'rare': 'Rare',
        'epic': 'Epic', 'legendary': 'Legendary', 'mythic': 'Mythic'
    }
    
    name = f"{rarity_names[rarity]} {slot_names.get(slot, slot.title())}"
    
    equipment = {
        'id': f"eq_{random.randint(100000, 999999)}",
        'name': name,
        'slot': slot,
        'rarity': rarity,
        'level': level,
        'stats': stats
    }
    
    # Add armor_type for armor slots (randomly choose between cloth, leather, metal)
    armor_slots = ['helmet', 'chest', 'legs', 'boots', 'gloves']
    if slot in armor_slots:
        equipment['armor_type'] = random.choice(['cloth', 'leather', 'metal'])
    
    # Add weapon_type for weapon slots (randomly choose from available weapon types)
    if slot == 'main_hand':
        # For main hand, randomly select a weapon type
        weapon_choices = ['sword', 'bow', 'staff', 'mace', 'dagger', 'wand', 'crossbow', 'hammer', 'axe']
        equipment['weapon_type'] = random.choice(weapon_choices)
    elif slot == 'off_hand':
        # For off hand, it's usually a shield, but could be a weapon for dual-wielding
        # Randomly choose between shield and a one-handed weapon
        if random.random() < 0.3:  # 30% chance of dual-wielding
            one_handed_weapons = ['sword', 'mace', 'dagger', 'wand']
            equipment['weapon_type'] = random.choice(one_handed_weapons)
        else:
            # Default to shield (no weapon_type, handled separately in frontend)
            pass
    
    return equipment


def roll_equipment_rarity(is_pvp: bool = False, enemy_level: int = 1, player_level: int = 1) -> str:
    """
    Roll for equipment rarity based on PVP/PVE with level requirements
    
    Args:
        is_pvp: True if from PVP, False if from PVE
        enemy_level: Level of enemy (for PvE scaling, but still capped at Rare)
        player_level: Level of the player receiving the drop (for rarity level requirements)
    
    Returns:
        Rarity string
    """
    if is_pvp:
        # PVP drop rates with level requirements:
        # - Legendary requires player level 75+
        # - Mythic requires player level 95+
        # Adjusted rates: 35% Common, 30% Uncommon, 20% Rare, 12% Epic, 2.5% Legendary, 0.5% Mythic
        roll = random.random() * 100
        
        # Check level requirements for high rarities
        if roll >= 99.5:  # 0.5% chance for Mythic
            if player_level >= 95:
                return 'mythic'
            else:
                # Downgrade to Legendary if not high enough level
                roll = 97.0  # Fall into Legendary range
        elif roll >= 97:  # 2.5% chance for Legendary (97-99.5)
            if player_level >= 75:
                return 'legendary'
            else:
                # Downgrade to Epic if not high enough level
                roll = 85.0  # Fall into Epic range
        
        # Standard rarity rolls (with downgrades applied if needed)
        if roll < 35:
            return 'common'
        elif roll < 65:
            return 'uncommon'
        elif roll < 85:
            return 'rare'
        elif roll < 97:
            return 'epic'
        elif roll < 99.5:
            return 'legendary'
        else:
            return 'mythic'
    else:
        # PVE drop rates: Capped at Rare (never Epic, Legendary, or Mythic)
        # Higher level enemies have better chance of Rare
        # Level 1-20: 60% Common, 35% Uncommon, 5% Rare
        # Level 21-50: 50% Common, 40% Uncommon, 10% Rare
        # Level 51-100: 40% Common, 45% Uncommon, 15% Rare
        roll = random.random() * 100
        if enemy_level <= 20:
            if roll < 60:
                return 'common'
            elif roll < 95:
                return 'uncommon'
            else:
                return 'rare'
        elif enemy_level <= 50:
            if roll < 50:
                return 'common'
            elif roll < 90:
                return 'uncommon'
            else:
                return 'rare'
        else:
            if roll < 40:
                return 'common'
            elif roll < 85:
                return 'uncommon'
            else:
                return 'rare'


def calculate_damage(attacker_stats: Dict[str, float], defender_stats: Dict[str, float], 
                     is_crit: bool = False, damage_type: str = 'physical', 
                     damage_multiplier: float = 1.0, attacker_buffs: Dict = None, 
                     defender_debuffs: Dict = None, attacker_equipment: Dict[str, Dict] = None) -> int:
    """
    Calculate damage dealt in combat
    
    Args:
        attacker_stats: Attacker's combat stats
        defender_stats: Defender's combat stats
        is_crit: Whether this is a critical hit
        damage_type: 'physical' or 'magical'
        damage_multiplier: Multiplier for ability damage
        attacker_buffs: Dictionary of active buffs on attacker
        defender_debuffs: Dictionary of active debuffs on defender
    
    Returns:
        Damage amount
    """
    # Determine base damage based on damage type
    if damage_type == 'magical':
        base_damage = attacker_stats.get('spell_power', 0)
    else:  # physical
        base_damage = attacker_stats.get('attack_power', 0)
    
    # Apply dual wielding penalty: 30% damage reduction per hit (but attacks 20% faster)
    # This balances dual wielding vs 1h+shield: DW gets more attacks but less damage per hit
    if attacker_equipment and is_dual_wielding(attacker_equipment):
        base_damage *= 0.70  # 30% reduction per hit
    
    # Apply ability multiplier
    base_damage *= damage_multiplier
    
    # Apply damage boost buff
    if attacker_buffs:
        for buff_data in attacker_buffs.values():
            if buff_data.get('type') == 'damage_boost':
                boost_power = buff_data.get('power', 0) / 100.0  # Convert percentage to multiplier
                base_damage *= (1.0 + boost_power)
    
    # Apply vulnerability debuff
    if defender_debuffs:
        for debuff_data in defender_debuffs.values():
            if debuff_data.get('type') == 'vulnerability':
                vuln_power = debuff_data.get('power', 0) / 100.0  # Convert percentage to multiplier
                base_damage *= (1.0 + vuln_power)
    
    # Apply random variance (50-100% of base damage)
    variance = random.uniform(0.5, 1.0)
    varied_damage = base_damage * variance
    
    # Apply defense/magic resistance reduction
    if damage_type == 'magical':
        magic_resist = defender_stats.get('magic_resistance', 0)
        damage_reduction = magic_resist / (magic_resist + 100)  # Diminishing returns
    else:  # physical
        defense = defender_stats.get('defense', 0)
        damage_reduction = defense / (defense + 100)  # Diminishing returns
    
    final_damage = varied_damage * (1 - damage_reduction)
    
    # Apply crit multiplier AFTER all other calculations
    if is_crit:
        final_damage *= 2.0
    
    # Minimum damage (10% of base)
    min_damage = base_damage * 0.1
    
    return max(int(final_damage), int(min_damage))


def check_hit(attacker_stats: Dict[str, float], defender_stats: Dict[str, float]) -> Tuple[bool, bool, bool, bool]:
    """
    Check if an attack hits, crits, is dodged, or is parried
    
    Returns:
        Tuple of (hit, crit, dodge, parry)
    """
    crit_roll = random.random()
    dodge_roll = random.random()
    parry_roll = random.random()
    
    crit_chance = attacker_stats.get('crit_chance', 0)
    dodge_chance = defender_stats.get('dodge_chance', 0)
    parry_chance = defender_stats.get('parry_chance', 0)
    
    is_dodged = dodge_roll < dodge_chance
    is_parried = parry_roll < parry_chance and not is_dodged
    is_crit = crit_roll < crit_chance and not is_dodged and not is_parried
    
    # Attack always hits unless dodged or parried
    hit = not is_dodged and not is_parried
    
    return hit, is_crit, is_dodged, is_parried


def calculate_exp_gain(winner_level: int, loser_level: int, is_pvp: bool = True) -> int:
    """
    Calculate EXP gain from combat
    
    Args:
        winner_level: Winner's level
        loser_level: Loser's level
        is_pvp: True if PVP, False if PVE
    
    Returns:
        EXP amount (always positive, minimum 1)
    """
    if is_pvp:
        # PVP: 500-2000 EXP based on opponent level
        base_exp = 500 + (loser_level * 15)
        # Level difference bonus/penalty
        level_diff = loser_level - winner_level
        exp_multiplier = 1.0 + (level_diff * 0.1)
        # Ensure multiplier never goes below 0.1 to prevent negative EXP
        exp_multiplier = max(0.1, exp_multiplier)
        exp_gain = int(base_exp * exp_multiplier)
        # Ensure minimum EXP gain of 1 (always gain at least 1 EXP for winning)
        return max(1, exp_gain)
    else:
        # PVE: 200-800 EXP based on enemy level
        base_exp = 200 + (loser_level * 6)
        level_diff = loser_level - winner_level
        exp_multiplier = 1.0 + (level_diff * 0.1)
        # Ensure multiplier never goes below 0.1 to prevent negative EXP
        exp_multiplier = max(0.1, exp_multiplier)
        exp_gain = int(base_exp * exp_multiplier)
        # Ensure minimum EXP gain of 1 (always gain at least 1 EXP for winning)
        return max(1, exp_gain)


def process_level_up(character_data: Dict) -> Dict:
    """
    Process level up if character has enough EXP
    
    Args:
        character_data: Character data with level, exp, skill_points
    
    Returns:
        Updated character data
    """
    level = character_data.get('level', 1)
    exp = character_data.get('exp', 0)
    skill_points = character_data.get('skill_points', 0)
    
    if level >= 100:
        return character_data
    
    exp_for_next = calculate_exp_to_next_level(level)
    
    levels_gained = 0
    while exp >= exp_for_next and level < 100:
        exp -= exp_for_next
        level += 1
        skill_points += 3  # 3 skill points per level
        levels_gained += 1
        
        if level < 100:
            exp_for_next = calculate_exp_to_next_level(level)
    
    character_data['level'] = level
    character_data['exp'] = exp
    character_data['skill_points'] = skill_points
    
    return character_data


def get_equipment_stats(equipment: Dict[str, Dict]) -> Dict[str, int]:
    """
    Sum up all stat bonuses from equipped items
    
    Args:
        equipment: Dictionary of slot -> equipment item
    
    Returns:
        Dictionary of stat -> total bonus
    """
    total_stats = {stat: 0 for stat in PRIMARY_STATS}
    
    for slot, item in equipment.items():
        if item and isinstance(item, dict):
            item_stats = item.get('stats', {})
            for stat, value in item_stats.items():
                if stat in total_stats:
                    total_stats[stat] += value
    
    return total_stats


def get_weapon_type(equipment: Dict[str, Dict]) -> Optional[str]:
    """
    Get weapon type from equipped main_hand item
    
    Args:
        equipment: Dictionary of slot -> equipment item
    
    Returns:
        Weapon type string or None if no weapon equipped
    """
    main_hand = equipment.get('main_hand')
    if main_hand and isinstance(main_hand, dict):
        weapon_type = main_hand.get('weapon_type')
        if weapon_type in WEAPON_TYPES:
            return weapon_type
    return None

def get_offhand_weapon_type(equipment: Dict[str, Dict]) -> Optional[str]:
    """
    Get weapon type from equipped off_hand item (if it's a weapon, not a shield)
    
    Args:
        equipment: Dictionary of slot -> equipment item
    
    Returns:
        Weapon type string or None if no weapon in offhand
    """
    off_hand = equipment.get('off_hand')
    if off_hand and isinstance(off_hand, dict):
        weapon_type = off_hand.get('weapon_type')
        if weapon_type in WEAPON_TYPES:
            return weapon_type
    return None

def is_dual_wielding(equipment: Dict[str, Dict]) -> bool:
    """
    Check if character is dual wielding (has weapons in both hands)
    
    Args:
        equipment: Dictionary of slot -> equipment item
    
    Returns:
        True if dual wielding, False otherwise
    """
    main_weapon = get_weapon_type(equipment)
    offhand_weapon = get_offhand_weapon_type(equipment)
    return main_weapon is not None and offhand_weapon is not None

def has_shield(equipment: Dict[str, Dict]) -> bool:
    """
    Check if character has a shield equipped
    
    Args:
        equipment: Dictionary of slot -> equipment item
    
    Returns:
        True if shield is equipped, False otherwise
    """
    off_hand = equipment.get('off_hand')
    if off_hand and isinstance(off_hand, dict):
        # Shield doesn't have weapon_type, or has weapon_type=None
        weapon_type = off_hand.get('weapon_type')
        return weapon_type is None or weapon_type not in WEAPON_TYPES
    return False

def can_use_with_shield(weapon_type: Optional[str]) -> bool:
    """
    Check if a weapon can be used with a shield
    
    Args:
        weapon_type: Weapon type string
    
    Returns:
        True if weapon can be used with shield, False otherwise
    """
    if weapon_type is None:
        return False
    return WEAPON_CATEGORIES.get(weapon_type) == 'one_handed'


def get_weapon_attack_speed(weapon_type: Optional[str], equipment: Dict[str, Dict] = None) -> float:
    """
    Get attack speed for a weapon type, accounting for dual wielding
    
    Args:
        weapon_type: Weapon type string (main hand)
        equipment: Optional equipment dict to check for dual wielding
    
    Returns:
        Attack speed in seconds (default 2.0 if invalid)
    """
    if weapon_type and weapon_type in WEAPON_ATTACK_SPEEDS:
        base_speed = WEAPON_ATTACK_SPEEDS[weapon_type]
        
        # Check for dual wielding
        if equipment and is_dual_wielding(equipment):
            # Dual wielding: 20% faster attack speed (more attacks, but less damage per hit)
            return base_speed * 0.8
        
        return base_speed
    return 2.0  # Default attack speed


def get_weapon_damage_type(weapon_type: Optional[str]) -> str:
    """
    Get damage type for a weapon type
    
    Args:
        weapon_type: Weapon type string
    
    Returns:
        'physical' or 'magical' (default 'physical')
    """
    if weapon_type and weapon_type in WEAPON_DAMAGE_TYPES:
        return WEAPON_DAMAGE_TYPES[weapon_type]
    return 'physical'  # Default to physical


# Ability definitions (3 per weapon: 2 regular + 1 ultimate)
ABILITIES = {
    'sword': [
        {'id': 'sword_power_strike', 'name': 'Power Strike', 'description': 'Deal 1.5x physical damage', 
         'cooldown_seconds': 5, 'damage_multiplier': 1.5, 'damage_type': 'physical', 'mana_cost': 10, 'is_ultimate': False,
         'status_effects': [{'type': 'vulnerability', 'power': 15, 'duration': 8, 'chance': 1.0, 'target': 'enemy'}]},
        {'id': 'sword_cleave', 'name': 'Cleave', 'description': 'Deal 1.3x physical damage', 
         'cooldown_seconds': 8, 'damage_multiplier': 1.3, 'damage_type': 'physical', 'mana_cost': 15, 'is_ultimate': False,
         'status_effects': [{'type': 'damage_boost', 'power': 20, 'duration': 10, 'chance': 1.0, 'target': 'self'}]},
        {'id': 'sword_whirlwind', 'name': 'Whirlwind', 'description': 'Deal 2.0x AOE physical damage', 
         'cooldown_seconds': 15, 'damage_multiplier': 2.0, 'damage_type': 'physical', 'mana_cost': 30, 'is_ultimate': True,
         'status_effects': [{'type': 'vulnerability', 'power': 20, 'duration': 12, 'chance': 1.0, 'target': 'enemy', 'aoe': True}]}
    ],
    'staff': [
        {'id': 'staff_magic_bolt', 'name': 'Magic Bolt', 'description': 'Deal 1.5x magical damage', 
         'cooldown_seconds': 5, 'damage_multiplier': 1.5, 'damage_type': 'magical', 'mana_cost': 10, 'is_ultimate': False,
         'status_effects': [{'type': 'slow', 'power': 15, 'duration': 6, 'chance': 1.0, 'target': 'enemy'}]},
        {'id': 'staff_fireball', 'name': 'Fireball', 'description': 'Deal 1.8x magical damage', 
         'cooldown_seconds': 8, 'damage_multiplier': 1.8, 'damage_type': 'magical', 'mana_cost': 20, 'is_ultimate': False,
         'status_effects': [{'type': 'poison', 'power': 8, 'duration': 10, 'chance': 1.0, 'target': 'enemy'}]},
        {'id': 'staff_meteor', 'name': 'Meteor', 'description': 'Deal 3.0x high magical damage', 
         'cooldown_seconds': 20, 'damage_multiplier': 3.0, 'damage_type': 'magical', 'mana_cost': 50, 'is_ultimate': True,
         'status_effects': [
             {'type': 'vulnerability', 'power': 25, 'duration': 15, 'chance': 1.0, 'target': 'enemy'},
             {'type': 'stun', 'power': 1, 'duration': 2, 'chance': 0.7, 'target': 'enemy'}
         ]}
    ],
    'bow': [
        {'id': 'bow_quick_shot', 'name': 'Quick Shot', 'description': 'Deal 1.3x physical damage', 
         'cooldown_seconds': 4, 'damage_multiplier': 1.3, 'damage_type': 'physical', 'mana_cost': 8, 'is_ultimate': False,
         'status_effects': [{'type': 'slow', 'power': 10, 'duration': 5, 'chance': 0.8, 'target': 'enemy'}]},
        {'id': 'bow_piercing_arrow', 'name': 'Piercing Arrow', 'description': 'Deal 1.6x physical damage, ignores some defense', 
         'cooldown_seconds': 7, 'damage_multiplier': 1.6, 'damage_type': 'physical', 'mana_cost': 15, 'is_ultimate': False,
         'status_effects': [{'type': 'vulnerability', 'power': 20, 'duration': 10, 'chance': 1.0, 'target': 'enemy'}]},
        {'id': 'bow_barrage', 'name': 'Barrage', 'description': 'Deal 2.5x multi-hit physical damage', 
         'cooldown_seconds': 18, 'damage_multiplier': 2.5, 'damage_type': 'physical', 'mana_cost': 40, 'is_ultimate': True,
         'status_effects': [{'type': 'vulnerability', 'power': 15, 'duration': 12, 'chance': 1.0, 'target': 'enemy', 'max_stacks': 3}]}
    ],
    'dagger': [
        {'id': 'dagger_backstab', 'name': 'Backstab', 'description': 'Deal 1.4x physical damage, high crit chance', 
         'cooldown_seconds': 4, 'damage_multiplier': 1.4, 'damage_type': 'physical', 'mana_cost': 8, 'is_ultimate': False,
         'status_effects': [{'type': 'vulnerability', 'power': 25, 'duration': 6, 'chance': 1.0, 'target': 'enemy'}]},
        {'id': 'dagger_poison_strike', 'name': 'Poison Strike', 'description': 'Deal 1.2x physical damage over time', 
         'cooldown_seconds': 6, 'damage_multiplier': 1.2, 'damage_type': 'physical', 'mana_cost': 12, 'is_ultimate': False,
         'status_effects': [{'type': 'poison', 'power': 10, 'duration': 12, 'chance': 1.0, 'target': 'enemy'}]},
        {'id': 'dagger_assassinate', 'name': 'Assassinate', 'description': 'Deal 3.5x physical damage, guaranteed crit', 
         'cooldown_seconds': 12, 'damage_multiplier': 3.5, 'damage_type': 'physical', 'mana_cost': 35, 'is_ultimate': True,
         'status_effects': [
             {'type': 'stun', 'power': 1, 'duration': 2, 'chance': 1.0, 'target': 'enemy'},
             {'type': 'vulnerability', 'power': 30, 'duration': 8, 'chance': 1.0, 'target': 'enemy'}
         ]}
    ],
    'mace': [
        {'id': 'mace_crush', 'name': 'Crush', 'description': 'Deal 1.5x physical damage', 
         'cooldown_seconds': 6, 'damage_multiplier': 1.5, 'damage_type': 'physical', 'mana_cost': 12, 'is_ultimate': False,
         'status_effects': [{'type': 'slow', 'power': 20, 'duration': 8, 'chance': 1.0, 'target': 'enemy'}]},
        {'id': 'mace_stun_strike', 'name': 'Stun Strike', 'description': 'Deal 1.3x physical damage, chance to stun', 
         'cooldown_seconds': 9, 'damage_multiplier': 1.3, 'damage_type': 'physical', 'mana_cost': 18, 'is_ultimate': False,
         'status_effects': [{'type': 'stun', 'power': 1, 'duration': 2, 'chance': 0.6, 'target': 'enemy'}]},
        {'id': 'mace_devastate', 'name': 'Devastate', 'description': 'Deal 2.8x physical damage, reduces enemy armor', 
         'cooldown_seconds': 16, 'damage_multiplier': 2.8, 'damage_type': 'physical', 'mana_cost': 45, 'is_ultimate': True,
         'status_effects': [
             {'type': 'vulnerability', 'power': 30, 'duration': 15, 'chance': 1.0, 'target': 'enemy'},
             {'type': 'slow', 'power': 25, 'duration': 10, 'chance': 1.0, 'target': 'enemy'}
         ]}
    ],
}


def get_abilities_for_weapon(weapon_type: Optional[str]) -> List[Dict]:
    """
    Get abilities for a weapon type
    
    Args:
        weapon_type: Weapon type string
    
    Returns:
        List of ability dictionaries
    """
    if weapon_type and weapon_type in ABILITIES:
        return ABILITIES[weapon_type]
    return []


def get_ability_by_id(ability_id: str) -> Optional[Dict]:
    """
    Get ability by ID
    
    Args:
        ability_id: Ability ID string
    
    Returns:
        Ability dictionary or None if not found
    """
    for weapon_abilities in ABILITIES.values():
        for ability in weapon_abilities:
            if ability['id'] == ability_id:
                return ability
    return None

