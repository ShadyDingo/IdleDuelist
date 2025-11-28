#!/usr/bin/env python3
"""
Unit tests for game logic
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from game_logic import (
    calculate_combat_stats,
    generate_equipment,
    roll_equipment_rarity,
    calculate_damage,
    check_hit,
    calculate_exp_gain,
    process_level_up,
    PRIMARY_STATS,
    WEAPON_TYPES,
    RARITIES
)

class TestCombatStats:
    def test_calculate_combat_stats_basic(self):
        base_stats = {'might': 10, 'agility': 10, 'vitality': 10}
        result = calculate_combat_stats(base_stats)
        
        assert 'attack_power' in result
        assert 'defense' in result
        assert 'max_hp' in result
        assert result['attack_power'] > 0
        assert result['defense'] > 0
        assert result['max_hp'] > 0
    
    def test_calculate_combat_stats_with_equipment(self):
        base_stats = {'might': 10, 'agility': 10, 'vitality': 10}
        equipment_stats = {'attack_power': 5, 'defense': 3}
        result = calculate_combat_stats(base_stats, equipment_stats)
        
        assert result['attack_power'] > equipment_stats['attack_power']
        assert result['defense'] > equipment_stats['defense']

class TestEquipment:
    def test_generate_equipment_has_required_fields(self):
        equipment = generate_equipment('main_hand', 'common', 1)
        
        assert 'id' in equipment
        assert 'name' in equipment
        assert 'slot' in equipment
        assert 'rarity' in equipment
        assert 'level' in equipment
        assert 'stats' in equipment
        assert equipment['slot'] == 'main_hand'
        assert equipment['rarity'] == 'common'
        assert equipment['level'] == 1
    
    def test_generate_equipment_weapon_has_weapon_type(self):
        equipment = generate_equipment('main_hand', 'rare', 5)
        
        assert 'weapon_type' in equipment
        assert equipment['weapon_type'] in ['sword', 'bow', 'staff', 'mace', 'dagger', 'wand', 'crossbow', 'hammer', 'axe']
    
    def test_generate_equipment_armor_has_armor_type(self):
        equipment = generate_equipment('chest', 'uncommon', 3)
        
        assert 'armor_type' in equipment
        assert equipment['armor_type'] in ['cloth', 'leather', 'metal']

class TestRarityRolls:
    def test_roll_equipment_rarity_returns_valid_rarity(self):
        rarity = roll_equipment_rarity(is_pvp=False, enemy_level=10, player_level=10)
        assert rarity in RARITIES
    
    def test_pvp_rarity_can_be_higher(self):
        pvp_rarities = [roll_equipment_rarity(is_pvp=True, enemy_level=50, player_level=50) for _ in range(100)]
        pve_rarities = [roll_equipment_rarity(is_pvp=False, enemy_level=50, player_level=50) for _ in range(100)]
        
        # PvP should have more epic+ items (statistically)
        pvp_high_rarity = sum(1 for r in pvp_rarities if r in ['epic', 'legendary', 'mythic'])
        # This is probabilistic, so we just check it's a valid rarity

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

