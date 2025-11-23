#!/usr/bin/env python3
"""
Migration script to add new stat system to IdleDuelist
Migrates from old system (strength, dex, con, int) to new 6-stat system
"""

import sqlite3
import json

def migrate_database():
    """Add new stat columns to database"""
    
    conn = sqlite3.connect('web_duelist.db')
    cursor = conn.cursor()
    
    print("🔄 Starting database migration...")
    
    # Add new stat columns
    new_columns = [
        ("might", "INTEGER DEFAULT 0"),
        ("finesse", "INTEGER DEFAULT 0"),
        ("fortitude", "INTEGER DEFAULT 0"),
        ("arcana", "INTEGER DEFAULT 0"),
        ("insight", "INTEGER DEFAULT 0"),
        ("presence", "INTEGER DEFAULT 0"),
        ("level", "INTEGER DEFAULT 1"),
        ("current_xp", "INTEGER DEFAULT 0"),
        ("total_xp", "INTEGER DEFAULT 0"),
        ("respecs_used", "INTEGER DEFAULT 0"),
        ("unspent_stat_points", "INTEGER DEFAULT 3"),  # Start with 3 points at level 1
    ]
    
    # Check existing columns
    cursor.execute("PRAGMA table_info(players)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    # Add missing columns
    for column_name, column_type in new_columns:
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE players ADD COLUMN {column_name} {column_type}")
                print(f"  ✅ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                print(f"  ⚠️  Column {column_name} already exists or error: {e}")
    
    conn.commit()
    conn.close()
    
    print("✅ Database migration complete!")

def load_xp_table():
    """Load XP table from JSON"""
    try:
        with open('xp_table.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️  xp_table.json not found, generating...")
        import calculate_xp_table
        levels = calculate_xp_table.calculate_xp_table()
        calculate_xp_table.export_to_json(levels)
        with open('xp_table.json', 'r') as f:
            return json.load(f)

def create_stat_calculation_functions():
    """Create Python module with stat calculation functions"""
    
    code = '''"""
IdleDuelist - New Stat System Calculations
Auto-generated stat calculation functions
"""

# XP Table for leveling
import json

def load_xp_table():
    """Load XP requirements"""
    try:
        with open('xp_table.json', 'r') as f:
            return json.load(f)
    except:
        return {}

XP_TABLE = load_xp_table()

def get_xp_for_level(level):
    """Get XP required for a specific level"""
    return XP_TABLE.get(str(level), {}).get('xp_required', 0)

def get_cumulative_xp_for_level(level):
    """Get total XP required to reach a level"""
    return XP_TABLE.get(str(level), {}).get('cumulative_xp', 0)

def calculate_level_from_xp(total_xp):
    """Calculate player level from total XP"""
    for level in range(100, 0, -1):
        cumulative = get_cumulative_xp_for_level(level)
        if total_xp >= cumulative:
            return level
    return 1

def calculate_stat_points_for_level(level):
    """Calculate total stat points available at a level"""
    return level * 3

# Stat Calculation Functions

def calculate_hp(might, finesse, fortitude, arcana, insight, presence):
    """Calculate total HP"""
    base_hp = 250
    hp = base_hp
    hp += might * 3
    hp += finesse * 1
    hp += fortitude * 8
    hp += arcana * 2
    hp += insight * 2
    hp += presence * 4
    return int(hp)

def calculate_attack_power(might, finesse, insight):
    """Calculate attack power"""
    attack = 0
    attack += might * 2
    attack += finesse * 1
    attack += insight * 1
    return int(attack)

def calculate_spell_power(arcana, insight):
    """Calculate spell power"""
    spell = 0
    spell += arcana * 3
    spell += insight * 1
    return int(spell)

def calculate_defense(fortitude):
    """Calculate defense"""
    return int(fortitude * 0.5)

def calculate_armor_penetration(might):
    """Calculate armor penetration (%)"""
    return min(might * 0.001, 1.0)  # 0.1% per point, max 100%

def calculate_crit_chance(finesse, insight, base_crit=0.0):
    """Calculate critical hit chance"""
    crit = base_crit
    crit += finesse * 0.0015  # 0.15% per point
    crit += insight * 0.0005  # 0.05% per point
    return min(crit, 0.75)  # Soft cap at 75% (requires 500 finesse)

def calculate_dodge_chance(finesse, base_dodge=0.0):
    """Calculate dodge chance"""
    dodge = base_dodge
    dodge += finesse * 0.001  # 0.1% per point
    # Diminishing returns after 40%
    if dodge > 0.4:
        excess = dodge - 0.4
        dodge = 0.4 + (excess * 0.5)  # Half effectiveness
    return min(dodge, 0.6)  # Hard cap at 60%

def calculate_parry_chance(might, fortitude, base_parry=0.0):
    """Calculate parry chance"""
    parry = base_parry
    parry += might * 0.0005  # 0.05% per point
    parry += fortitude * 0.002  # 0.2% per point
    return min(parry, 0.20)  # Cap at 20%

def calculate_hp_regen_percent(fortitude):
    """Calculate HP regeneration per turn (%)"""
    return fortitude * 0.001  # 0.1% per point (10% at 100 fortitude)

def calculate_status_resistance(fortitude):
    """Calculate status effect resistance"""
    return min(fortitude * 0.002, 0.8)  # 0.2% per point, cap at 80%

def calculate_lifesteal(presence):
    """Calculate lifesteal (%)"""
    return presence * 0.002  # 0.2% per point

def calculate_faction_power_multiplier(presence):
    """Calculate faction passive strength multiplier"""
    return 1.0 + (presence * 0.003)  # +0.3% per point

def calculate_crit_damage_multiplier(insight, base_mult=2.0):
    """Calculate critical hit damage multiplier"""
    return base_mult + (insight * 0.005)  # +0.5% per point

def calculate_cooldown_reduction(insight):
    """Calculate ability cooldown reduction"""
    return min(insight * 0.002, 0.5)  # 0.2% per point, cap at 50%

def calculate_turn_meter_bonus(finesse):
    """Calculate turn frequency bonus"""
    return finesse * 0.002  # 0.2% per point = +20% at 100 finesse

def calculate_healing_effectiveness(presence):
    """Calculate healing received/dealt multiplier"""
    return 1.0 + (presence * 0.001)  # +0.1% per point

def calculate_debuff_duration_bonus(presence):
    """Calculate debuff duration extension"""
    return presence * 0.001  # +0.1% per point

# Breakpoint Functions

def get_might_breakpoints(might):
    """Get active might breakpoints"""
    breakpoints = []
    if might >= 50:
        breakpoints.append({"name": "Heavy Weapons Master", "desc": "+10% damage with two-handed weapons"})
    if might >= 100:
        breakpoints.append({"name": "Stunning Blows", "desc": "10% chance to stun on hit"})
    if might >= 200:
        breakpoints.append({"name": "Berserker Rage", "desc": "+20% damage when HP > 80%"})
    if might >= 300:
        breakpoints.append({"name": "Immovable", "desc": "Immune to knockback effects"})
    return breakpoints

def get_finesse_breakpoints(finesse):
    """Get active finesse breakpoints"""
    breakpoints = []
    if finesse >= 50:
        breakpoints.append({"name": "Lethal Precision", "desc": "Critical hits deal 2.5x damage (up from 2x)"})
    if finesse >= 100:
        breakpoints.append({"name": "Swift Strikes", "desc": "+1 turn every 5 turns"})
    if finesse >= 200:
        breakpoints.append({"name": "Evasive Maneuvers", "desc": "Dodging refunds 25% ability cooldown"})
    if finesse >= 300:
        breakpoints.append({"name": "Assassin's Mark", "desc": "First attack each turn is guaranteed crit"})
    return breakpoints

def get_fortitude_breakpoints(fortitude):
    """Get active fortitude breakpoints"""
    breakpoints = []
    if fortitude >= 50:
        breakpoints.append({"name": "Second Wind", "desc": "Regenerate 2% max HP when hit below 30% (once per duel)"})
    if fortitude >= 100:
        breakpoints.append({"name": "Unbreakable", "desc": "Take 50% reduced damage below 50% HP"})
    if fortitude >= 200:
        breakpoints.append({"name": "Poison Immunity", "desc": "Immune to poison and bleed"})
    if fortitude >= 300:
        breakpoints.append({"name": "Undying", "desc": "Survive lethal blow with 1 HP (once per duel)"})
    return breakpoints

def get_arcana_breakpoints(arcana):
    """Get active arcana breakpoints"""
    breakpoints = []
    if arcana >= 50:
        breakpoints.append({"name": "Efficient Casting", "desc": "Abilities cost 10% less mana"})
    if arcana >= 100:
        breakpoints.append({"name": "Spell Mastery", "desc": "Abilities deal 20% more damage"})
    if arcana >= 200:
        breakpoints.append({"name": "Empowered Afflictions", "desc": "Critical spells apply double status effects"})
    if arcana >= 300:
        breakpoints.append({"name": "Spell Crits", "desc": "Abilities can critically strike"})
    return breakpoints

def get_insight_breakpoints(insight):
    """Get active insight breakpoints"""
    breakpoints = []
    if insight >= 50:
        breakpoints.append({"name": "Tactical Vision", "desc": "See enemy's next action"})
    if insight >= 100:
        breakpoints.append({"name": "Exploit Weakness", "desc": "+10% damage to buffed enemies"})
    if insight >= 200:
        breakpoints.append({"name": "True Sight", "desc": "Abilities reveal invisible enemies"})
    if insight >= 300:
        breakpoints.append({"name": "Overwhelming Force", "desc": "Bypass enemy shields and damage reduction"})
    return breakpoints

def get_presence_breakpoints(presence):
    """Get active presence breakpoints"""
    breakpoints = []
    if presence >= 50:
        breakpoints.append({"name": "Inspiring Aura", "desc": "Faction passive affects nearby allies"})
    if presence >= 100:
        breakpoints.append({"name": "Spell Drain", "desc": "Lifesteal applies to spell damage"})
    if presence >= 200:
        breakpoints.append({"name": "Terrifying Presence", "desc": "Enemies below 30% HP deal 20% less damage"})
    if presence >= 300:
        breakpoints.append({"name": "Overwhelming Will", "desc": "Faction passive activates twice per turn"})
    return breakpoints

def get_all_breakpoints(stats_dict):
    """Get all active breakpoints for a player"""
    breakpoints = {
        'might': get_might_breakpoints(stats_dict.get('might', 0)),
        'finesse': get_finesse_breakpoints(stats_dict.get('finesse', 0)),
        'fortitude': get_fortitude_breakpoints(stats_dict.get('fortitude', 0)),
        'arcana': get_arcana_breakpoints(stats_dict.get('arcana', 0)),
        'insight': get_insight_breakpoints(stats_dict.get('insight', 0)),
        'presence': get_presence_breakpoints(stats_dict.get('presence', 0))
    }
    return breakpoints

def calculate_all_stats(stats_dict, equipment_bonuses=None):
    """Calculate all derived stats from base stats"""
    # Extract base stats
    might = stats_dict.get('might', 0)
    finesse = stats_dict.get('finesse', 0)
    fortitude = stats_dict.get('fortitude', 0)
    arcana = stats_dict.get('arcana', 0)
    insight = stats_dict.get('insight', 0)
    presence = stats_dict.get('presence', 0)
    
    # Apply equipment bonuses if provided
    if equipment_bonuses:
        might += equipment_bonuses.get('might', 0)
        finesse += equipment_bonuses.get('finesse', 0)
        fortitude += equipment_bonuses.get('fortitude', 0)
        arcana += equipment_bonuses.get('arcana', 0)
        insight += equipment_bonuses.get('insight', 0)
        presence += equipment_bonuses.get('presence', 0)
    
    return {
        # Base stats
        'might': might,
        'finesse': finesse,
        'fortitude': fortitude,
        'arcana': arcana,
        'insight': insight,
        'presence': presence,
        
        # Derived stats
        'hp': calculate_hp(might, finesse, fortitude, arcana, insight, presence),
        'attack_power': calculate_attack_power(might, finesse, insight),
        'spell_power': calculate_spell_power(arcana, insight),
        'defense': calculate_defense(fortitude),
        'armor_penetration': calculate_armor_penetration(might),
        'crit_chance': calculate_crit_chance(finesse, insight),
        'dodge_chance': calculate_dodge_chance(finesse),
        'parry_chance': calculate_parry_chance(might, fortitude),
        'hp_regen_percent': calculate_hp_regen_percent(fortitude),
        'status_resistance': calculate_status_resistance(fortitude),
        'lifesteal': calculate_lifesteal(presence),
        'faction_power': calculate_faction_power_multiplier(presence),
        'crit_damage_mult': calculate_crit_damage_multiplier(insight),
        'cooldown_reduction': calculate_cooldown_reduction(insight),
        'turn_meter_bonus': calculate_turn_meter_bonus(finesse),
        'healing_effectiveness': calculate_healing_effectiveness(presence),
        'debuff_duration': calculate_debuff_duration_bonus(presence),
        
        # Breakpoints
        'breakpoints': get_all_breakpoints(stats_dict)
    }
'''
    
    with open('stat_calculations.py', 'w') as f:
        f.write(code)
    
    print("✅ Created stat_calculations.py")

def main():
    """Run migration"""
    print("=" * 80)
    print("IDLEDUELIST STAT SYSTEM MIGRATION")
    print("=" * 80)
    
    # Step 1: Migrate database
    migrate_database()
    
    # Step 2: Load XP table
    print("\n🔄 Loading XP table...")
    xp_table = load_xp_table()
    print(f"✅ Loaded XP table with {len(xp_table)} levels")
    
    # Step 3: Create stat calculation module
    print("\n🔄 Creating stat calculation functions...")
    create_stat_calculation_functions()
    
    print("\n" + "=" * 80)
    print("✅ MIGRATION COMPLETE!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Update frontend to show new stats")
    print("2. Add stat allocation UI")
    print("3. Update combat formulas to use new stats")
    print("4. Test stat breakpoints")

if __name__ == '__main__':
    main()
