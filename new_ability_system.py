#!/usr/bin/env python3
"""
New Ability System with Attack/Spell Power Scaling
"""

# NEW ABILITY SYSTEM WITH PROPER SCALING
ABILITY_DATA = {
    # ORDER OF THE SILVER CRUSADE
    'divine_strike': {
        'name': 'Divine Strike',
        'description': 'Holy attack that scales with both attack and spell power',
        'attack_scaling': 0.8,  # 80% attack power
        'spell_scaling': 0.6,   # 60% spell power
        'base_damage': 20,
        'armor_penetration': 0.5,  # Ignores 50% armor
        'cooldown': 3,
        'faction': 'order_of_the_silver_crusade'
    },
    'shield_of_faith': {
        'name': 'Shield of Faith',
        'description': 'Grants damage reduction based on spell power',
        'spell_scaling': 0.4,   # 40% spell power
        'base_reduction': 0.3,   # 30% base reduction
        'duration': 2,
        'cooldown': 5,
        'faction': 'order_of_the_silver_crusade'
    },
    'healing_light': {
        'name': 'Healing Light',
        'description': 'Restores health based on spell power',
        'spell_scaling': 0.8,   # 80% spell power
        'base_healing': 25,
        'duration': 3,
        'cooldown': 4,
        'faction': 'order_of_the_silver_crusade'
    },
    'righteous_fury': {
        'name': 'Righteous Fury',
        'description': 'Increases next attack damage with spell power',
        'spell_scaling': 0.6,   # 60% spell power
        'base_multiplier': 1.5, # 50% damage increase
        'cooldown': 3,
        'faction': 'order_of_the_silver_crusade'
    },
    'purification': {
        'name': 'Purification',
        'description': 'Removes all negative effects',
        'spell_scaling': 0.2,   # 20% spell power (utility)
        'cleanse': True,
        'cooldown': 4,
        'faction': 'order_of_the_silver_crusade'
    },
    
    # SHADOW COVENANT
    'shadow_strike': {
        'name': 'Shadow Strike',
        'description': 'Guaranteed critical hit scaling with attack power',
        'attack_scaling': 1.0,  # 100% attack power
        'spell_scaling': 0.3,   # 30% spell power
        'base_damage': 15,
        'guaranteed_crit': True,
        'cooldown': 4,
        'faction': 'shadow_covenant'
    },
    'vanish': {
        'name': 'Vanish',
        'description': 'Become invisible for 2 turns',
        'spell_scaling': 0.3,   # 30% spell power (utility)
        'effects': {'invisible': 2},
        'cooldown': 5,
        'faction': 'shadow_covenant'
    },
    'poison_blade': {
        'name': 'Poison Blade',
        'description': 'Poisons enemy with attack power scaling',
        'attack_scaling': 0.6,  # 60% attack power
        'spell_scaling': 0.4,   # 40% spell power
        'base_damage': 10,
        'effects': {'poison': 3},
        'cooldown': 3,
        'faction': 'shadow_covenant'
    },
    'assassinate': {
        'name': 'Assassinate',
        'description': 'High damage attack that scales with attack power',
        'attack_scaling': 1.2,  # 120% attack power
        'spell_scaling': 0.2,   # 20% spell power
        'base_damage': 30,
        'ignores_buffs': True,
        'cooldown': 5,
        'faction': 'shadow_covenant'
    },
    'shadow_clone': {
        'name': 'Shadow Clone',
        'description': 'Creates a clone that attacks with spell power',
        'spell_scaling': 0.7,   # 70% spell power
        'attack_scaling': 0.3,  # 30% attack power
        'base_damage': 20,
        'clone_attack': True,
        'cooldown': 6,
        'faction': 'shadow_covenant'
    },
    
    # WILDERNESS TRIBE
    'natures_wrath': {
        'name': "Nature's Wrath",
        'description': 'Powerful nature attack scaling with both powers',
        'attack_scaling': 0.7,  # 70% attack power
        'spell_scaling': 0.8,   # 80% spell power
        'base_damage': 25,
        'reveals_stealth': True,
        'cooldown': 4,
        'faction': 'wilderness_tribe'
    },
    'thorn_barrier': {
        'name': 'Thorn Barrier',
        'description': 'Reflects damage based on spell power',
        'spell_scaling': 0.5,   # 50% spell power
        'base_reflect': 0.2,    # 20% base reflect
        'duration': 3,
        'cooldown': 4,
        'faction': 'wilderness_tribe'
    },
    'wild_growth': {
        'name': 'Wild Growth',
        'description': 'Increases all stats with spell power',
        'spell_scaling': 0.4,   # 40% spell power
        'base_buff': 0.15,      # 15% stat increase
        'duration': 3,
        'cooldown': 5,
        'faction': 'wilderness_tribe'
    },
    'earthquake': {
        'name': 'Earthquake',
        'description': 'Stuns enemy and deals area damage',
        'attack_scaling': 0.5,  # 50% attack power
        'spell_scaling': 0.7,   # 70% spell power
        'base_damage': 20,
        'effects': {'stun': 1},
        'cooldown': 5,
        'faction': 'wilderness_tribe'
    },
    'spirit_form': {
        'name': 'Spirit Form',
        'description': 'Reduces incoming damage with spell power',
        'spell_scaling': 0.6,   # 60% spell power
        'base_reduction': 0.2,   # 20% base reduction
        'stun_immunity': True,
        'duration': 3,
        'cooldown': 6,
        'faction': 'wilderness_tribe'
    }
}

# Ability Counterplay System (unchanged)
ABILITY_COUNTERS = {
    'shield_of_faith': ['divine_strike'],      # Divine Strike ignores invulnerability
    'vanish': ['natures_wrath'],               # Nature's Wrath reveals invisible enemies
    'poison_blade': ['purification'],          # Purification removes poison effects
    'earthquake': ['spirit_form'],             # Spirit Form immune to stun effects
    'shadow_strike': ['thorn_barrier'],        # Thorn Barrier reflects guaranteed crits
    'assassinate': ['shield_of_faith'],        # Shield of Faith prevents execution
    'healing_light': ['poison_blade'],         # Poison counters healing over time
    'righteous_fury': ['spirit_form'],         # Spirit Form reduces damage buffs
}

def calculate_ability_damage(ability_name, attacker_stats):
    """Calculate ability damage based on attack and spell power"""
    if ability_name not in ABILITY_DATA:
        return 0
    
    ability = ABILITY_DATA[ability_name]
    attack_power = attacker_stats.get('attack_power', 0)
    spell_power = attacker_stats.get('spell_power', 0)
    
    # Calculate damage from both attack and spell power
    attack_damage = attack_power * ability.get('attack_scaling', 0)
    spell_damage = spell_power * ability.get('spell_scaling', 0)
    base_damage = ability.get('base_damage', 0)
    
    total_damage = base_damage + attack_damage + spell_damage
    return int(total_damage)

def calculate_ability_healing(ability_name, caster_stats):
    """Calculate ability healing based on spell power"""
    if ability_name not in ABILITY_DATA:
        return 0
    
    ability = ABILITY_DATA[ability_name]
    spell_power = caster_stats.get('spell_power', 0)
    
    spell_healing = spell_power * ability.get('spell_scaling', 0)
    base_healing = ability.get('base_healing', 0)
    
    total_healing = base_healing + spell_healing
    return int(total_healing)

if __name__ == "__main__":
    # Test the new system
    test_stats = {
        'attack_power': 50,
        'spell_power': 30
    }
    
    print("Testing new ability system:")
    print(f"Divine Strike damage: {calculate_ability_damage('divine_strike', test_stats)}")
    print(f"Healing Light healing: {calculate_ability_healing('healing_light', test_stats)}")
    print(f"Shadow Strike damage: {calculate_ability_damage('shadow_strike', test_stats)}")
