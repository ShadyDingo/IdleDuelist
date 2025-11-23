#!/usr/bin/env python3
"""
Build Testing Script - Simulates duels between different character builds
Tests various stat allocations to determine optimal builds
"""

import sys
import random
from typing import Dict, List, Tuple
from collections import defaultdict

# Simplified PlayerData class for testing (no Kivy dependencies)
class PlayerData:
    def __init__(self, player_id: str = None, username: str = None):
        self.player_id = player_id or "test_player"
        self.username = username or "TestPlayer"
        self.equipment = {}
        self.hp = 100
        self.max_hp = 100
        self.faction = 'order_of_the_silver_crusade'
        self.ability_loadout = []
        
        # Progression
        self.level = 1
        self.skill_points_available = 0
        
        # Base stats
        self.base_stats = {
            'attack_power': 0,
            'spell_power': 0,
            'defense': 0,
            'max_hp': 0,
            'speed': 0,
            'crit_chance': 0
        }
    
    def get_total_damage(self) -> int:
        """Calculate total damage"""
        base_damage = 15  # Base weapon damage
        return base_damage + self.base_stats.get('attack_power', 0)
    
    def get_total_spell_power(self) -> int:
        """Calculate total spell power"""
        return self.base_stats.get('spell_power', 0)
    
    def get_total_defense(self) -> int:
        """Calculate total defense"""
        base_defense = 5  # Base armor defense
        return base_defense + self.base_stats.get('defense', 0)
    
    def get_total_speed(self) -> int:
        """Calculate total speed"""
        base_speed = 5  # Base speed from armor
        return base_speed + self.base_stats.get('speed', 0)
    
    def get_total_crit_chance(self) -> float:
        """Calculate total critical hit chance"""
        base_crit = 0.05  # 5% base from weapon
        stat_bonus = self.base_stats.get('crit_chance', 0) * 0.01
        speed_bonus = self.get_total_speed() * 0.005
        return min(0.5, base_crit + stat_bonus + speed_bonus)
    
    def get_dodge_chance(self) -> float:
        """Calculate dodge chance based on speed"""
        speed = self.get_total_speed()
        if speed <= 0:
            return 0.0
        elif speed <= 20:
            base_dodge = speed * 0.015
        else:
            base_dodge = 20 * 0.015
            extra_dodge = (speed - 20) * 0.005
            base_dodge += extra_dodge
        return min(0.5, base_dodge)
    
    def get_total_max_hp(self) -> int:
        """Calculate total maximum HP"""
        base_hp = 100
        stat_bonus = self.base_stats.get('max_hp', 0)
        return base_hp + stat_bonus
    
    def allocate_stat_point(self, stat_name: str) -> bool:
        """Allocate a skill point to a specific stat"""
        if self.skill_points_available <= 0:
            return False
        
        if stat_name not in self.base_stats:
            return False
        
        stat_increases = {
            'attack_power': 2,
            'spell_power': 2,
            'defense': 1,
            'max_hp': 10,
            'speed': 1,
            'crit_chance': 1
        }
        
        self.base_stats[stat_name] += stat_increases.get(stat_name, 1)
        self.skill_points_available -= 1
        
        if stat_name == 'max_hp':
            self.max_hp = self.get_total_max_hp()
            self.hp = min(self.hp, self.max_hp)
        
        return True

class BuildTester:
    def __init__(self):
        self.results = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total_damage': 0, 'duels': 0})
        self.builds = {}
        
    def create_build(self, name: str, stat_allocation: Dict[str, int]) -> PlayerData:
        """Create a player with specific stat allocation"""
        player = PlayerData(username=name)
        player.skill_points_available = 50  # Give 50 points to test with
        
        # Allocate stats
        for stat_name, points in stat_allocation.items():
            for _ in range(points):
                player.allocate_stat_point(stat_name)
        
        # Reset HP
        player.max_hp = player.get_total_max_hp()
        player.hp = player.max_hp
        
        return player
    
    def simulate_duel(self, player1: PlayerData, player2: PlayerData) -> Tuple[PlayerData, int, int]:
        """Simulate a duel between two players, return winner and damage dealt by each"""
        # Reset HP
        player1.hp = player1.max_hp
        player2.hp = player2.max_hp
        player1.max_hp = player1.get_total_max_hp()
        player2.max_hp = player2.get_total_max_hp()
        player1.hp = player1.max_hp
        player2.hp = player2.max_hp
        
        p1_total_damage = 0
        p2_total_damage = 0
        
        max_turns = 50  # Prevent infinite loops
        turn = 0
        
        while player1.hp > 0 and player2.hp > 0 and turn < max_turns:
            turn += 1
            
            # Determine who goes first (speed-based)
            p1_speed = player1.get_total_speed()
            p2_speed = player2.get_total_speed()
            
            if p1_speed > p2_speed:
                first, second = player1, player2
                first_name, second_name = "P1", "P2"
            elif p2_speed > p1_speed:
                first, second = player2, player1
                first_name, second_name = "P2", "P1"
            else:
                # Equal speed, random
                if random.random() < 0.5:
                    first, second = player1, player2
                    first_name, second_name = "P1", "P2"
                else:
                    first, second = player2, player1
                    first_name, second_name = "P2", "P1"
            
            # First attacker
            damage = self.calculate_damage(first, second)
            second.hp -= damage
            
            if first == player1:
                p1_total_damage += damage
            else:
                p2_total_damage += damage
            
            if second.hp <= 0:
                break
            
            # Second attacker
            damage = self.calculate_damage(second, first)
            first.hp -= damage
            
            if second == player1:
                p1_total_damage += damage
            else:
                p2_total_damage += damage
        
        # Determine winner
        if player1.hp > player2.hp:
            return player1, p1_total_damage, p2_total_damage
        elif player2.hp > player1.hp:
            return player2, p1_total_damage, p2_total_damage
        else:
            # Tiebreaker: more damage dealt
            if p1_total_damage > p2_total_damage:
                return player1, p1_total_damage, p2_total_damage
            else:
                return player2, p1_total_damage, p2_total_damage
    
    def calculate_damage(self, attacker: PlayerData, defender: PlayerData) -> int:
        """Calculate damage for one attack"""
        base_damage = attacker.get_total_damage()
        defense = defender.get_total_defense()
        
        # Apply defense reduction
        damage_reduction = min(defense * 0.5, base_damage * 0.75)  # Max 75% reduction
        actual_damage = max(base_damage - damage_reduction, base_damage * 0.25)  # Min 25% damage
        
        # Critical hit chance
        crit_chance = attacker.get_total_crit_chance()
        if random.random() < crit_chance:
            actual_damage *= 1.5  # 50% more damage on crit
        
        # Dodge chance
        dodge_chance = defender.get_dodge_chance()
        if random.random() < dodge_chance:
            actual_damage *= 0.5  # 50% damage if dodged
        
        return int(actual_damage)
    
    def run_matchup(self, build1_name: str, build2_name: str, num_duels: int = 100):
        """Run multiple duels between two builds"""
        player1 = self.builds[build1_name]
        player2 = self.builds[build2_name]
        
        for _ in range(num_duels):
            winner, p1_damage, p2_damage = self.simulate_duel(player1, player2)
            
            if winner == player1:
                self.results[build1_name]['wins'] += 1
                self.results[build2_name]['losses'] += 1
            else:
                self.results[build2_name]['wins'] += 1
                self.results[build1_name]['losses'] += 1
            
            self.results[build1_name]['total_damage'] += p1_damage
            self.results[build2_name]['total_damage'] += p2_damage
            self.results[build1_name]['duels'] += 1
            self.results[build2_name]['duels'] += 1
    
    def define_builds(self):
        """Define all test builds"""
        builds_config = {
            'Pure Attack': {
                'attack_power': 25,  # 50 points total
                'spell_power': 0,
                'defense': 0,
                'max_hp': 0,
                'speed': 0,
                'crit_chance': 0
            },
            'Tank': {
                'attack_power': 0,
                'spell_power': 0,
                'defense': 25,
                'max_hp': 25,
                'speed': 0,
                'crit_chance': 0
            },
            'Balanced': {
                'attack_power': 8,
                'spell_power': 8,
                'defense': 8,
                'max_hp': 8,
                'speed': 9,
                'crit_chance': 9
            },
            'Speed Demon': {
                'attack_power': 10,
                'spell_power': 0,
                'defense': 0,
                'max_hp': 0,
                'speed': 20,
                'crit_chance': 20
            },
            'Crit Build': {
                'attack_power': 15,
                'spell_power': 0,
                'defense': 0,
                'max_hp': 0,
                'speed': 5,
                'crit_chance': 30
            },
            'HP Tank': {
                'attack_power': 5,
                'spell_power': 0,
                'defense': 5,
                'max_hp': 40,
                'speed': 0,
                'crit_chance': 0
            },
            'Bruiser': {
                'attack_power': 20,
                'spell_power': 0,
                'defense': 10,
                'max_hp': 10,
                'speed': 0,
                'crit_chance': 10
            },
            'Spell Caster': {
                'attack_power': 0,
                'spell_power': 25,
                'defense': 5,
                'max_hp': 10,
                'speed': 5,
                'crit_chance': 5
            },
            'Glass Cannon': {
                'attack_power': 20,
                'spell_power': 0,
                'defense': 0,
                'max_hp': 0,
                'speed': 15,
                'crit_chance': 15
            },
            'Dodge Tank': {
                'attack_power': 5,
                'spell_power': 0,
                'defense': 15,
                'max_hp': 5,
                'speed': 25,
                'crit_chance': 0
            }
        }
        
        for name, allocation in builds_config.items():
            self.builds[name] = self.create_build(name, allocation)
            print(f"Created build: {name}")
            self.print_build_stats(name)
            print()
    
    def print_build_stats(self, build_name: str):
        """Print stats for a build"""
        player = self.builds[build_name]
        print(f"  HP: {player.max_hp}")
        print(f"  Attack: {player.get_total_damage()}")
        print(f"  Spell Power: {player.get_total_spell_power()}")
        print(f"  Defense: {player.get_total_defense()}")
        print(f"  Speed: {player.get_total_speed()}")
        print(f"  Crit Chance: {player.get_total_crit_chance() * 100:.1f}%")
        print(f"  Dodge Chance: {player.get_dodge_chance() * 100:.1f}%")
    
    def run_all_matchups(self, duels_per_matchup: int = 100):
        """Run all possible matchups between builds"""
        build_names = list(self.builds.keys())
        total_matchups = len(build_names) * (len(build_names) - 1) // 2
        
        print(f"\n{'='*60}")
        print(f"Running {total_matchups} matchups with {duels_per_matchup} duels each...")
        print(f"{'='*60}\n")
        
        matchup_count = 0
        for i, build1 in enumerate(build_names):
            for build2 in build_names[i+1:]:
                matchup_count += 1
                print(f"[{matchup_count}/{total_matchups}] {build1} vs {build2}...", end=' ')
                self.run_matchup(build1, build2, duels_per_matchup)
                
                # Show quick results
                b1_wins = self.results[build1]['wins']
                b2_wins = self.results[build2]['wins']
                total = b1_wins + b2_wins
                if total > 0:
                    b1_wr = (b1_wins / total) * 100
                    print(f"({b1_wr:.1f}% vs {100-b1_wr:.1f}%)")
                else:
                    print("(No results)")
    
    def print_results(self):
        """Print final results"""
        print(f"\n{'='*80}")
        print("BUILD PERFORMANCE RANKINGS")
        print(f"{'='*80}\n")
        
        # Calculate win rates
        rankings = []
        for build_name, stats in self.results.items():
            total_duels = stats['wins'] + stats['losses']
            if total_duels > 0:
                win_rate = (stats['wins'] / total_duels) * 100
                avg_damage = stats['total_damage'] / stats['duels']
                rankings.append({
                    'name': build_name,
                    'win_rate': win_rate,
                    'wins': stats['wins'],
                    'losses': stats['losses'],
                    'avg_damage': avg_damage
                })
        
        # Sort by win rate
        rankings.sort(key=lambda x: x['win_rate'], reverse=True)
        
        # Print table header
        print(f"{'Rank':<6} {'Build Name':<20} {'Win Rate':<12} {'Record':<15} {'Avg Damage':<12}")
        print(f"{'-'*80}")
        
        # Print rankings
        for i, build in enumerate(rankings, 1):
            rank = f"#{i}"
            name = build['name']
            win_rate = f"{build['win_rate']:.1f}%"
            record = f"{build['wins']}-{build['losses']}"
            avg_damage = f"{build['avg_damage']:.1f}"
            
            print(f"{rank:<6} {name:<20} {win_rate:<12} {record:<15} {avg_damage:<12}")
        
        print(f"\n{'='*80}")
        print("DETAILED BUILD ANALYSIS")
        print(f"{'='*80}\n")
        
        # Print top 3 with detailed stats
        for i in range(min(3, len(rankings))):
            build = rankings[i]
            player = self.builds[build['name']]
            
            print(f"\n#{i+1}: {build['name']} (Win Rate: {build['win_rate']:.1f}%)")
            print(f"{'─'*60}")
            self.print_build_stats(build['name'])
            print(f"  Win-Loss Record: {build['wins']}-{build['losses']}")
            print(f"  Average Damage per Duel: {build['avg_damage']:.1f}")
        
        print(f"\n{'='*80}")

def main():
    """Run the build testing simulation"""
    print("="*80)
    print("IDLE DUELIST - BUILD TESTING SIMULATION")
    print("="*80)
    print("\nTesting various stat allocations with 50 skill points each...")
    print()
    
    tester = BuildTester()
    
    # Define all builds
    tester.define_builds()
    
    # Run all matchups
    tester.run_all_matchups(duels_per_matchup=100)
    
    # Print results
    tester.print_results()
    
    print("\n" + "="*80)
    print("SIMULATION COMPLETE!")
    print("="*80)

if __name__ == '__main__':
    main()
