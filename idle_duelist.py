#!/usr/bin/env python3
"""
Idle Duelist - A turn-based combat game with equipment and ranking system
"""

import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.core.audio import SoundLoader
import json
import os
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

kivy.require('2.1.0')

class MusicManager:
    def __init__(self):
        self.background_music = None
        self.combat_music = None
        self.volume = 0.5  # Start at half volume
        self.muted = False
        self.current_track = None
        self.load_music()
    
    def load_music(self):
        """Load music files if they exist"""
        # Main theme music (for menus)
        main_paths = [
            'music/main_theme.mp3',
            'music/main_theme.wav',
            'music/main_theme.ogg'
        ]
        
        for path in main_paths:
            if os.path.exists(path):
                self.background_music = SoundLoader.load(path)
                if self.background_music:
                    self.background_music.loop = True
                    break
        
        # Duel music
        duel_paths = [
            'music/duel.mp3',
            'music/duel.wav',
            'music/duel.ogg'
        ]
        
        for path in duel_paths:
            if os.path.exists(path):
                self.combat_music = SoundLoader.load(path)
                if self.combat_music:
                    self.combat_music.loop = True
                    break
    
    def set_volume(self, volume: float):
        """Set music volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        if not self.muted:
            if self.background_music:
                self.background_music.volume = self.volume
            if self.combat_music:
                self.combat_music.volume = self.volume
    
    def set_muted(self, muted: bool):
        """Mute or unmute music"""
        self.muted = muted
        if muted:
            if self.background_music and self.background_music.state == 'play':
                self.background_music.volume = 0.0
            if self.combat_music and self.combat_music.state == 'play':
                self.combat_music.volume = 0.0
        else:
            if self.background_music and self.background_music.state == 'play':
                self.background_music.volume = self.volume
            if self.combat_music and self.combat_music.state == 'play':
                self.combat_music.volume = self.volume
    
    def play_background(self):
        """Play background music"""
        if self.background_music:
            self.stop_music()
            self.background_music.volume = 0.0 if self.muted else self.volume
            self.background_music.play()
            self.current_track = 'background'
    
    def play_combat(self):
        """Play combat music"""
        if self.combat_music:
            self.stop_music()
            self.combat_music.volume = 0.0 if self.muted else self.volume
            self.combat_music.play()
            self.current_track = 'combat'
    
    def stop_music(self):
        """Stop all music"""
        if self.background_music and self.background_music.state == 'play':
            self.background_music.stop()
        if self.combat_music and self.combat_music.state == 'play':
            self.combat_music.stop()
        self.current_track = None

# Faction System - Three factions with unique passives and abilities
FACTION_DATA = {
    'order_of_the_silver_crusade': {
        'name': 'Order of the Silver Crusade',
        'description': 'Holy warriors focused on defense and healing',
        'passive': 'divine_protection',  # 10% damage reduction
        'passive_value': 0.10,
        'secondary_passive': 'holy_resistance',  # Immune to poison effects
        'secondary_value': True,
        'abilities': ['divine_strike', 'shield_of_faith', 'healing_light', 'righteous_fury', 'purification'],
        'image': 'assets/factions/order_of_the_silver_crusade.png',
        'theme_colors': {'primary': (0.8, 0.8, 1.0), 'secondary': (1.0, 1.0, 0.8)}
    },
    'shadow_covenant': {
        'name': 'Shadow Covenant',
        'description': 'Stealthy assassins focused on critical hits',
        'passive': 'shadow_mastery',  # 15% increased crit chance
        'passive_value': 0.15,
        'secondary_passive': 'stealth_damage',  # +10% damage when invisible
        'secondary_value': 0.10,
        'abilities': ['shadow_strike', 'vanish', 'poison_blade', 'assassinate', 'shadow_clone'],
        'image': 'assets/factions/shadow_covenant.png',
        'theme_colors': {'primary': (0.3, 0.1, 0.5), 'secondary': (0.5, 0.1, 0.3)}
    },
    'wilderness_tribe': {
        'name': 'Wilderness Tribe',
        'description': 'Nature mages focused on adaptability',
        'passive': 'natures_blessing',  # 5% HP regeneration per turn
        'passive_value': 0.05,
        'secondary_passive': 'nature_affinity',  # +10% damage vs slowed enemies
        'secondary_value': 0.10,
        'abilities': ['natures_wrath', 'thorn_barrier', 'wild_growth', 'earthquake', 'spirit_form'],
        'image': 'assets/factions/wilderness_tribe.png',
        'theme_colors': {'primary': (0.2, 0.8, 0.2), 'secondary': (0.4, 0.6, 0.2)}
    }
}

# Armor Set Bonuses - 3-piece and 5-piece combinations
ARMOR_SET_BONUSES = {
    'cloth': {
        'name': 'Lightfoot',
        '3_piece': {
            'name': 'Swift Step',
            'effects': {'dodge_bonus': 0.05, 'speed_bonus': 2},  # +5% dodge, +2 speed
            'description': 'Enhanced mobility and evasion'
        },
        '5_piece': {
            'name': 'Wind Walker',
            'effects': {'dodge_bonus': 0.10, 'speed_bonus': 5, 'crit_chance': 0.05},  # +10% dodge, +5 speed, +5% crit
            'description': 'Master of speed and precision strikes'
        }
    },
    'leather': {
        'name': 'Balanced',
        '3_piece': {
            'name': 'Adaptive Combat',
            'effects': {'stat_bonus': 0.05, 'armor_penetration': 1},  # +5% to all stats, +1 armor pen
            'description': 'Versatile fighting techniques'
        },
        '5_piece': {
            'name': 'Perfect Balance',
            'effects': {'stat_bonus': 0.10, 'armor_penetration': 3, 'damage_bonus': 0.05},  # +10% to all stats, +3 armor pen, +5% damage
            'description': 'Harmonious mastery of all combat arts'
        }
    },
    'metal': {
        'name': 'Fortress',
        '3_piece': {
            'name': 'Iron Will',
            'effects': {'defense_bonus': 3, 'damage_reduction': 0.05},  # +3 defense, +5% damage reduction
            'description': 'Unwavering defensive stance'
        },
        '5_piece': {
            'name': 'Immovable Mountain',
            'effects': {'defense_bonus': 8, 'damage_reduction': 0.10, 'damage_reflect': 0.05},  # +8 defense, +10% damage reduction, +5% damage reflect
            'description': 'Unbreakable fortress that strikes back'
        }
    }
}

# Ability System - Extensible framework for all abilities
ABILITY_DATA = {
    # Order of the Silver Crusade abilities
    'divine_strike': {
        'name': 'Divine Strike',
        'description': 'Holy attack that ignores armor',
        'damage_multiplier': 1.5,
        'armor_penetration': 999,  # Ignores all armor
        'cooldown': 3,
        'image': 'assets/abilities/ability_divine_strike.PNG',
        'faction': 'order_of_the_silver_crusade'
    },
    'shield_of_faith': {
        'name': 'Shield of Faith',
        'description': 'Grants temporary invulnerability',
        'damage_reduction': 1.0,  # 100% damage reduction
        'duration': 2,
        'cooldown': 5,
        'image': 'assets/abilities/ability_shield_of_faith.PNG',
        'faction': 'order_of_the_silver_crusade'
    },
    'healing_light': {
        'name': 'Healing Light',
        'description': 'Restores health over time',
        'heal_amount': 25,
        'duration': 3,
        'cooldown': 4,
        'image': 'assets/abilities/ability_healing_light.PNG',
        'faction': 'order_of_the_silver_crusade'
    },
    'righteous_fury': {
        'name': 'Righteous Fury',
        'description': 'Increases damage and crit chance',
        'damage_bonus': 0.5,  # 50% damage increase
        'crit_bonus': 0.3,    # 30% crit chance increase
        'duration': 4,
        'cooldown': 6,
        'image': 'assets/abilities/ability_righteous_fury.PNG',
        'faction': 'order_of_the_silver_crusade'
    },
    'purification': {
        'name': 'Purification',
        'description': 'Removes all debuffs and heals',
        'heal_amount': 40,
        'cooldown': 8,
        'image': 'assets/abilities/ability_purification.PNG',
        'faction': 'order_of_the_silver_crusade'
    },
    
    # Shadow Covenant abilities
    'shadow_strike': {
        'name': 'Shadow Strike',
        'description': 'Teleport behind enemy for guaranteed crit',
        'damage_multiplier': 2.0,
        'guaranteed_crit': True,
        'cooldown': 4,
        'image': 'assets/abilities/ability_shadow_strike.PNG',
        'faction': 'shadow_covenant'
    },
    'vanish': {
        'name': 'Vanish',
        'description': 'Become invisible for 2 turns',
        'invisibility_duration': 2,
        'cooldown': 6,
        'image': 'assets/abilities/ability_vanish.PNG',
        'faction': 'shadow_covenant'
    },
    'poison_blade': {
        'name': 'Poison Blade',
        'description': 'Poison that deals damage over time',
        'poison_damage': 8,
        'duration': 4,
        'cooldown': 3,
        'image': 'assets/abilities/ability_poison_blade.png',
        'faction': 'shadow_covenant'
    },
    'assassinate': {
        'name': 'Assassinate',
        'description': 'Instant kill if enemy below 25% HP',
        'execute_threshold': 0.25,
        'damage_multiplier': 3.0,
        'cooldown': 8,
        'image': 'assets/abilities/ability_assassinate.PNG',
        'faction': 'shadow_covenant'
    },
    'shadow_clone': {
        'name': 'Shadow Clone',
        'description': 'Creates a clone that attacks for you',
        'clone_damage': 0.75,  # 75% of your damage
        'duration': 3,
        'cooldown': 7,
        'image': 'assets/abilities/ability_shadow_clone.PNG',
        'faction': 'shadow_covenant'
    },
    
    # Wilderness Tribe abilities
    'natures_wrath': {
        'name': "Nature's Wrath",
        'description': 'Summons vines that damage and slow enemy',
        'damage_amount': 15,
        'slow_amount': 0.5,  # 50% speed reduction
        'duration': 3,
        'cooldown': 4,
        'image': 'assets/abilities/ability_nature\'s_wrath.png',
        'faction': 'wilderness_tribe'
    },
    'thorn_barrier': {
        'name': 'Thorn Barrier',
        'description': 'Reflects damage back to attacker',
        'reflect_damage': 0.5,  # Reflect 50% of damage taken
        'duration': 4,
        'cooldown': 5,
        'image': 'assets/abilities/ability_thorn_barrier.PNG',
        'faction': 'wilderness_tribe'
    },
    'wild_growth': {
        'name': 'Wild Growth',
        'description': 'Increases all stats temporarily',
        'stat_bonus': 0.3,  # 30% increase to all stats
        'duration': 5,
        'cooldown': 6,
        'image': 'assets/abilities/ability_wild_growth.PNG',
        'faction': 'wilderness_tribe'
    },
    'earthquake': {
        'name': 'Earthquake',
        'description': 'Area damage that stuns enemy',
        'damage_amount': 20,
        'stun_duration': 1,
        'cooldown': 7,
        'image': 'assets/abilities/ability_earthquake.PNG',
        'faction': 'wilderness_tribe'
    },
    'spirit_form': {
        'name': 'Spirit Form',
        'description': 'Become ethereal, immune to physical damage',
        'damage_reduction': 0.8,  # 80% damage reduction
        'duration': 3,
        'cooldown': 8,
        'image': 'assets/abilities/ability_spirit_form.PNG',
        'faction': 'wilderness_tribe'
    }
}

# Ability Counterplay System - Abilities that counter other abilities
ABILITY_COUNTERS = {
    'shield_of_faith': ['divine_strike'],      # Divine Strike ignores invulnerability
    'vanish': ['natures_wrath'],               # Nature's Wrath reveals invisible enemies
    'poison_blade': ['purification'],          # Purification removes poison effects
    'earthquake': ['spirit_form'],             # Spirit Form immune to stun effects
    'shadow_strike': ['thorn_barrier'],        # Thorn Barrier reflects guaranteed crits
    'assassinate': ['shield_of_faith'],        # Shield of Faith prevents execution
    'healing_light': ['poison_blade'],         # Poison counters healing over time
    'righteous_fury': ['spirit_form'],         # Spirit Form reduces damage buffs
    'wild_growth': ['assassinate'],            # Assassinate ignores stat buffs
    'shadow_clone': ['earthquake'],            # Earthquake hits both original and clone
}

# Enhanced Status Effects
ENHANCED_STATUS_EFFECTS = {
    'poison': {
        'damage': 4,
        'duration': 3,
        'description': 'Deals damage over time and reduces healing effectiveness'
    },
    'stun': {
        'duration': 1,
        'description': 'Prevents actions for the duration'
    },
    'slow': {
        'amount': 0.5,
        'duration': 3,
        'description': 'Reduces speed and movement effectiveness'
    },
    'invisible': {
        'duration': 2,
        'description': 'Cannot be targeted by attacks (except revealing abilities)'
    },
    'shield': {
        'amount': 0,
        'duration': 2,
        'description': 'Absorbs damage before health'
    }
}

# Combat Strategy Types
# Combat Strategy removed - simplified to ability-or-attack only

# Equipment data and stats - REBALANCED FOR STRATEGIC DEPTH
EQUIPMENT_DATA = {
    # Armor pieces - REBALANCED: More balanced trade-offs
    'armor': {
        # CLOTH: High speed, low defense, good for dodging builds
        'cloth_helmet': {'name': 'Cloth Helmet', 'speed': 6, 'defense': 1, 'image': 'assets/armor/cloth_helmet.png'},
        'cloth_armor': {'name': 'Cloth Armor', 'speed': 8, 'defense': 2, 'image': 'assets/armor/cloth_armor.PNG'},
        'cloth_gloves': {'name': 'Cloth Gloves', 'speed': 3, 'defense': 0, 'image': 'assets/armor/cloth_gloves.png'},
        'cloth_pants': {'name': 'Cloth Pants', 'speed': 4, 'defense': 1, 'image': 'assets/armor/cloth_pants.PNG'},
        'cloth_boots': {'name': 'Cloth Boots', 'speed': 5, 'defense': 0, 'image': 'assets/armor/cloth_boots.PNG'},
        
        # LEATHER: Balanced speed and defense - the "jack of all trades"
        'leather_helmet': {'name': 'Leather Helmet', 'speed': 1, 'defense': 3, 'image': 'assets/armor/leather_helmet.png'},
        'leather_armor': {'name': 'Leather Armor', 'speed': -1, 'defense': 5, 'image': 'assets/armor/leather_armor.PNG'},
        'leather_gloves': {'name': 'Leather Gloves', 'speed': 0, 'defense': 2, 'image': 'assets/armor/leather_gloves.png'},
        'leather_pants': {'name': 'Leather Pants', 'speed': -1, 'defense': 3, 'image': 'assets/armor/leather_pants.png'},
        'leather_boots': {'name': 'Leather Boots', 'speed': 1, 'defense': 2, 'image': 'assets/armor/leather_boots.png'},
        
        # METAL: Low speed, high defense - tank builds with major trade-offs
        'metal_helmet': {'name': 'Metal Helmet', 'speed': -4, 'defense': 6, 'image': 'assets/armor/metal_helmet.PNG'},
        'metal_armor': {'name': 'Metal Armor', 'speed': -8, 'defense': 10, 'image': 'assets/armor/metal_armor.png'},
        'metal_gloves': {'name': 'Metal Gloves', 'speed': -2, 'defense': 3, 'image': 'assets/armor/metal_gloves.PNG'},
        'metal_pants': {'name': 'Metal Pants', 'speed': -3, 'defense': 5, 'image': 'assets/armor/metal_pants.png'},
        'metal_boots': {'name': 'Metal Boots', 'speed': -1, 'defense': 3, 'image': 'assets/armor/metal_boots.png'},
    },
    
    # Weapons - REBALANCED: More strategic trade-offs
    'weapons': {
        # FAST WEAPONS: Lower damage, higher critical chance
        'weapon_knife': {
            'name': 'Dagger', 
            'damage': 7, 
            'speed_bonus': 5, 
            'crit_chance': 0.25,  # 25% crit chance
            'armor_penetration': 0,
            'two_handed': False, 
            'image': 'assets/weapons/weapon_knife.PNG'
        },
        
        # BALANCED WEAPONS: Moderate stats
        'weapon_sword': {
            'name': 'Sword', 
            'damage': 11, 
            'speed_bonus': 1, 
            'crit_chance': 0.15,  # 15% crit chance
            'armor_penetration': 2,
            'two_handed': False, 
            'image': 'assets/weapons/weapon_sword.png'
        },
        
        # HEAVY WEAPONS: High damage, low speed, armor penetration - NOW TWO-HANDED
        'weapon_mace': {
            'name': 'Mace', 
            'damage': 18, 
            'speed_bonus': -3, 
            'crit_chance': 0.05,  # 5% crit chance
            'armor_penetration': 4,  # Reduced armor penetration
            'two_handed': True,  # Now two-handed to prevent dual wielding
            'image': 'assets/weapons/weapon_mace.PNG'
        },
        
        # DEFENSIVE WEAPON: Low damage, high defense bonus
        'weapon_shield': {
            'name': 'Shield', 
            'damage': 3, 
            'speed_bonus': -1, 
            'defense_bonus': 5, 
            'crit_chance': 0.0,  # No crits
            'armor_penetration': 0,
            'two_handed': False, 
            'image': 'assets/weapons/weapon_shield.PNG'
        },
    }
}

class PlayerData:
    def __init__(self, player_id: str = None, username: str = None):
        self.player_id = player_id or str(uuid.uuid4())
        self.username = username or self._generate_random_username()
        self.rating = 1000  # Starting ELO rating
        self.wins = 0
        self.losses = 0
        self.weekly_wins = 0
        self.weekly_losses = 0
        self.last_weekly_reset = self._get_current_week_start()
        
        # Damage tracking for tiebreaking
        self.total_damage_dealt = 0
        
        self.equipment = {
            'helmet': 'cloth_helmet',
            'armor': 'cloth_armor', 
            'gloves': 'cloth_gloves',
            'pants': 'cloth_pants',
            'boots': 'cloth_boots',
            'mainhand': 'weapon_sword',
            'offhand': None
        }
        self.hp = 100
        self.max_hp = 100
        
        # Faction system
        self.faction = 'order_of_the_silver_crusade'  # Default faction
        self.faction_level = 1
        
        # Ability system
        self.ability_loadout = []  # Ordered list of ability IDs
        self.ability_cooldowns = {}  # Track cooldowns for each ability
        self.active_buffs = {}  # Track active buffs/debuffs
        
        # Combat strategy removed - simplified to attack-only
        
        # Status effects
        self.status_effects = {
            'poison': {'damage': 0, 'duration': 0},
            'stun': {'duration': 0},
            'invisible': {'duration': 0},
            'slow': {'amount': 0, 'duration': 0},
            'shield': {'amount': 0, 'duration': 0}
        }
        
    def _generate_random_username(self) -> str:
        adjectives = ['Swift', 'Bold', 'Fierce', 'Mystic', 'Shadow', 'Light', 'Storm', 'Iron', 'Golden', 'Crystal']
        nouns = ['Warrior', 'Mage', 'Rogue', 'Knight', 'Hunter', 'Guardian', 'Blade', 'Shield', 'Arrow', 'Spell']
        return f"{random.choice(adjectives)}{random.choice(nouns)}{random.randint(1, 999)}"
    
    def _get_current_week_start(self) -> str:
        """Get the start of the current week (Sunday 10pm EST)"""
        now = datetime.now()
        # Find the most recent Sunday
        days_since_sunday = now.weekday() + 1  # Monday = 0, so Sunday = 6
        if days_since_sunday == 7:  # If today is Sunday
            days_since_sunday = 0
        
        last_sunday = now - timedelta(days=days_since_sunday)
        # Set to 10pm EST (22:00)
        week_start = last_sunday.replace(hour=22, minute=0, second=0, microsecond=0)
        
        # If it's before 10pm on Sunday, go to previous Sunday
        if now.weekday() == 6 and now.hour < 22:
            week_start = week_start - timedelta(days=7)
        
        return week_start.isoformat()
    
    def check_weekly_reset(self):
        """Check if weekly stats need to be reset"""
        current_week_start = self._get_current_week_start()
        if current_week_start != self.last_weekly_reset:
            self.weekly_wins = 0
            self.weekly_losses = 0
            self.last_weekly_reset = current_week_start
            return True
        return False
    
    def add_win(self):
        """Add a win to both lifetime and weekly stats"""
        self.check_weekly_reset()
        self.wins += 1
        self.weekly_wins += 1
    
    def add_loss(self):
        """Add a loss to both lifetime and weekly stats"""
        self.check_weekly_reset()
        self.losses += 1
        self.weekly_losses += 1
    
    def get_total_speed(self) -> int:
        """Calculate total speed from equipped armor and weapons"""
        total_speed = 0
        
        # Armor speed modifiers
        for slot, item_id in self.equipment.items():
            if slot in ['helmet', 'armor', 'gloves', 'pants', 'boots'] and item_id:
                total_speed += EQUIPMENT_DATA['armor'][item_id]['speed']
        
        # Weapon speed modifiers
        if self.equipment['mainhand'] and self.equipment['mainhand'] in EQUIPMENT_DATA['weapons']:
            total_speed += EQUIPMENT_DATA['weapons'][self.equipment['mainhand']].get('speed_bonus', 0)
        if self.equipment['offhand'] and self.equipment['offhand'] in EQUIPMENT_DATA['weapons']:
            total_speed += EQUIPMENT_DATA['weapons'][self.equipment['offhand']].get('speed_bonus', 0)
        
        # Armor set bonus speed
        set_bonuses = self.get_armor_set_bonus()
        total_speed += set_bonuses.get('speed_bonus', 0)
        
        return total_speed
    
    def get_total_defense(self) -> int:
        """Calculate total defense from equipped armor and weapons"""
        total_defense = 0
        
        # Armor defense
        for slot, item_id in self.equipment.items():
            if slot in ['helmet', 'armor', 'gloves', 'pants', 'boots'] and item_id:
                total_defense += EQUIPMENT_DATA['armor'][item_id]['defense']
        
        # Weapon defense bonus (shields)
        if self.equipment['mainhand'] and self.equipment['mainhand'] in EQUIPMENT_DATA['weapons']:
            total_defense += EQUIPMENT_DATA['weapons'][self.equipment['mainhand']].get('defense_bonus', 0)
        if self.equipment['offhand'] and self.equipment['offhand'] in EQUIPMENT_DATA['weapons']:
            total_defense += EQUIPMENT_DATA['weapons'][self.equipment['offhand']].get('defense_bonus', 0)
        
        # Armor set bonus defense
        set_bonuses = self.get_armor_set_bonus()
        total_defense += set_bonuses.get('defense_bonus', 0)
        
        return total_defense
    
    def get_total_damage(self) -> int:
        """Calculate total damage from equipped weapons"""
        total_damage = 0
        
        # Check if mainhand is two-handed
        if self.equipment['mainhand'] and self.equipment['mainhand'] in EQUIPMENT_DATA['weapons']:
            weapon = EQUIPMENT_DATA['weapons'][self.equipment['mainhand']]
            if weapon.get('two_handed', False):
                # Two-handed weapon - no offhand allowed
                total_damage += weapon['damage']
            else:
                # One-handed weapon
                total_damage += weapon['damage']
                # Add offhand damage if it exists and is not two-handed
                if (self.equipment['offhand'] and 
                    self.equipment['offhand'] in EQUIPMENT_DATA['weapons'] and
                    not EQUIPMENT_DATA['weapons'][self.equipment['offhand']].get('two_handed', False)):
                    total_damage += EQUIPMENT_DATA['weapons'][self.equipment['offhand']]['damage']
        
        return total_damage
    
    def get_weapon_property(self, property_name: str, default_value=0) -> float:
        """Get a weapon property (crit_chance, armor_penetration, etc.) from mainhand weapon"""
        if self.equipment['mainhand'] and self.equipment['mainhand'] in EQUIPMENT_DATA['weapons']:
            weapon = EQUIPMENT_DATA['weapons'][self.equipment['mainhand']]
            return weapon.get(property_name, default_value)
        return default_value
    
    def get_total_crit_chance(self) -> float:
        """Calculate total critical hit chance (BALANCED)"""
        base_crit = self.get_weapon_property('crit_chance', 0.0)
        # Speed bonus to crit chance (BALANCED: reduced from 0.5% to 0.25% per speed point)
        speed_bonus = self.get_total_speed() * 0.0025  # 0.25% per speed point
        # Armor set bonus crit chance
        set_bonuses = self.get_armor_set_bonus()
        set_crit_bonus = set_bonuses.get('crit_chance', 0.0)
        return min(0.5, base_crit + speed_bonus + set_crit_bonus)  # Cap at 50%
    
    def get_total_armor_penetration(self) -> int:
        """Calculate total armor penetration"""
        base_penetration = self.get_weapon_property('armor_penetration', 0)
        # Armor set bonus armor penetration
        set_bonuses = self.get_armor_set_bonus()
        set_penetration = set_bonuses.get('armor_penetration', 0)
        return base_penetration + set_penetration
    
    def get_dodge_chance(self) -> float:
        """Calculate dodge chance based on speed (BALANCED)"""
        speed = self.get_total_speed()
        # Higher speed = higher dodge chance, but with diminishing returns
        # BALANCED: reduced from 1.5% to 1% per speed, and 0.5% to 0.25% above 20
        if speed <= 0:
            base_dodge = 0.0
        elif speed <= 20:
            base_dodge = speed * 0.01  # 1% per speed point up to 20 (was 1.5%)
        else:
            # Diminishing returns above 20 speed
            base_dodge = 20 * 0.01  # 20% at 20 speed (was 30%)
            extra_dodge = (speed - 20) * 0.0025  # 0.25% per point above 20 (was 0.5%)
            base_dodge += extra_dodge
        
        # Armor set bonus dodge chance
        set_bonuses = self.get_armor_set_bonus()
        set_dodge_bonus = set_bonuses.get('dodge_bonus', 0.0)
        
        return min(0.4, base_dodge + set_dodge_bonus)  # Cap at 40% (reduced from 50%)
    
    def can_equip_offhand(self) -> bool:
        """Check if offhand can be equipped (not using two-handed weapon)"""
        if not self.equipment['mainhand']:
            return True
        if self.equipment['mainhand'] in EQUIPMENT_DATA['weapons']:
            return not EQUIPMENT_DATA['weapons'][self.equipment['mainhand']].get('two_handed', False)
        return True
    
    def get_faction_data(self):
        """Get faction information"""
        return FACTION_DATA.get(self.faction, FACTION_DATA['order_of_the_silver_crusade'])
    
    def get_faction_passive_bonus(self) -> float:
        """Get faction passive bonus"""
        faction_data = self.get_faction_data()
        passive = faction_data['passive']
        value = faction_data['passive_value']
        
        if passive == 'divine_protection':
            return value  # 10% damage reduction
        elif passive == 'shadow_mastery':
            return value  # 15% crit chance increase
        elif passive == 'natures_blessing':
            return value  # 5% HP regeneration per turn
        return 0.0
    
    def get_faction_secondary_passive(self) -> dict:
        """Get faction secondary passive effects"""
        faction_data = self.get_faction_data()
        passive = faction_data.get('secondary_passive')
        value = faction_data.get('secondary_value')
        
        if passive == 'holy_resistance':
            return {'poison_immunity': value}  # Immune to poison
        elif passive == 'stealth_damage':
            return {'stealth_damage_bonus': value}  # +10% damage when invisible
        elif passive == 'nature_affinity':
            return {'nature_affinity_bonus': value}  # +10% damage vs slowed enemies
        return {}
    
    def get_armor_set_bonus(self) -> dict:
        """Calculate armor set bonuses based on equipped pieces"""
        armor_counts = {'cloth': 0, 'leather': 0, 'metal': 0}
        
        # Count armor pieces by type
        for slot, item_id in self.equipment.items():
            if slot in ['helmet', 'armor', 'gloves', 'pants', 'boots'] and item_id:
                if item_id.startswith('cloth_'):
                    armor_counts['cloth'] += 1
                elif item_id.startswith('leather_'):
                    armor_counts['leather'] += 1
                elif item_id.startswith('metal_'):
                    armor_counts['metal'] += 1
        
        # Apply set bonuses
        set_bonuses = {}
        for armor_type, count in armor_counts.items():
            if count >= 5:
                # 5-piece set bonus
                set_bonuses.update(ARMOR_SET_BONUSES[armor_type]['5_piece']['effects'])
            elif count >= 3:
                # 3-piece set bonus
                set_bonuses.update(ARMOR_SET_BONUSES[armor_type]['3_piece']['effects'])
        
        return set_bonuses
    
    def get_available_abilities(self) -> List[str]:
        """Get list of available abilities for current faction"""
        faction_data = self.get_faction_data()
        return faction_data['abilities']
    
    def can_use_ability(self, ability_id: str) -> bool:
        """Check if ability can be used (cooldown, mana, etc.)"""
        if ability_id not in ABILITY_DATA:
            return False
        
        ability = ABILITY_DATA[ability_id]
        
        # Check if ability belongs to current faction
        if ability['faction'] != self.faction:
            return False
        
        # Check cooldown
        if ability_id in self.ability_cooldowns and self.ability_cooldowns[ability_id] > 0:
            return False
        
        
        return True
    
    def use_ability(self, ability_id: str) -> Dict:
        """Use an ability and return its effects"""
        if not self.can_use_ability(ability_id):
            return {'success': False, 'message': 'Cannot use ability'}
        
        ability = ABILITY_DATA[ability_id]
        
        
        # Set cooldown
        self.ability_cooldowns[ability_id] = ability['cooldown']
        
        return {
            'success': True,
            'ability': ability,
            'effects': self._calculate_ability_effects(ability)
        }
    
    def _calculate_ability_effects(self, ability: Dict) -> Dict:
        """Calculate the effects of an ability"""
        effects = {}
        
        # Damage effects
        if 'damage_multiplier' in ability:
            effects['damage_multiplier'] = ability['damage_multiplier']
        if 'damage_amount' in ability:
            effects['damage_amount'] = ability['damage_amount']
        
        # Healing effects
        if 'heal_amount' in ability:
            effects['heal_amount'] = ability['heal_amount']
        
        # Status effects
        if 'duration' in ability:
            effects['duration'] = ability['duration']
        if 'stun_duration' in ability:
            effects['stun_duration'] = ability['stun_duration']
        if 'slow_amount' in ability:
            effects['slow_amount'] = ability['slow_amount']
        if 'poison_damage' in ability:
            effects['poison_damage'] = ability['poison_damage']
        
        # Special effects
        if 'guaranteed_crit' in ability:
            effects['guaranteed_crit'] = ability['guaranteed_crit']
        if 'armor_penetration' in ability:
            effects['armor_penetration'] = ability['armor_penetration']
        if 'damage_reduction' in ability:
            effects['damage_reduction'] = ability['damage_reduction']
        if 'damage_bonus' in ability:
            effects['damage_bonus'] = ability['damage_bonus']
        if 'crit_bonus' in ability:
            effects['crit_bonus'] = ability['crit_bonus']
        if 'stat_bonus' in ability:
            effects['stat_bonus'] = ability['stat_bonus']
        if 'reflect_damage' in ability:
            effects['reflect_damage'] = ability['reflect_damage']
        if 'invisibility_duration' in ability:
            effects['invisibility_duration'] = ability['invisibility_duration']
        if 'execute_threshold' in ability:
            effects['execute_threshold'] = ability['execute_threshold']
        if 'clone_damage' in ability:
            effects['clone_damage'] = ability['clone_damage']
        
        return effects
    
    def get_action(self, player_hp: int, opponent_hp: int) -> str:
        """Get action - simplified to attack only"""
        return 'attack'
    
    def apply_status_effect(self, effect_type: str, **kwargs):
        """Apply a status effect"""
        if effect_type in self.status_effects:
            self.status_effects[effect_type].update(kwargs)
    
    def process_status_effects(self):
        """Process all active status effects"""
        # Process poison (check for immunity first)
        if self.status_effects['poison']['duration'] > 0:
            # Check for poison immunity from faction passive
            secondary_passives = self.get_faction_secondary_passive()
            if not secondary_passives.get('poison_immunity', False):
                poison_damage = self.status_effects['poison']['damage']
                self.hp = max(0, self.hp - poison_damage)
            self.status_effects['poison']['duration'] -= 1
        
        # Process healing over time (Nature's Blessing)
        if self.faction == 'wilderness_tribe':
            heal_amount = int(self.max_hp * self.get_faction_passive_bonus())
            self.hp = min(self.max_hp, self.hp + heal_amount)
        
        # Process other status effects
        for effect_type, effect_data in self.status_effects.items():
            if 'duration' in effect_data and effect_data['duration'] > 0:
                effect_data['duration'] -= 1
    
    def reduce_cooldowns(self):
        """Reduce all ability cooldowns by 1"""
        for ability_id in self.ability_cooldowns:
            if self.ability_cooldowns[ability_id] > 0:
                self.ability_cooldowns[ability_id] -= 1
    
    def to_dict(self) -> Dict:
        return {
            'player_id': self.player_id,
            'username': self.username,
            'rating': self.rating,
            'wins': self.wins,
            'losses': self.losses,
            'weekly_wins': self.weekly_wins,
            'weekly_losses': self.weekly_losses,
            'last_weekly_reset': self.last_weekly_reset,
            'total_damage_dealt': self.total_damage_dealt,
            'equipment': self.equipment,
            'hp': self.hp,
            'max_hp': self.max_hp,
            'faction': self.faction,
            'faction_level': self.faction_level,
            'ability_loadout': self.ability_loadout,
            'ability_cooldowns': self.ability_cooldowns,
            'active_buffs': self.active_buffs,
            'status_effects': self.status_effects
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        player = cls(data['player_id'], data['username'])
        player.rating = data.get('rating', 1000)
        player.wins = data.get('wins', 0)
        player.losses = data.get('losses', 0)
        player.weekly_wins = data.get('weekly_wins', 0)
        player.weekly_losses = data.get('weekly_losses', 0)
        player.last_weekly_reset = data.get('last_weekly_reset', player._get_current_week_start())
        player.total_damage_dealt = data.get('total_damage_dealt', 0)
        player.equipment = data.get('equipment', player.equipment)
        player.hp = data.get('hp', 100)
        player.max_hp = data.get('max_hp', 100)
        player.faction = data.get('faction', 'order_of_the_silver_crusade')
        player.faction_level = data.get('faction_level', 1)
        player.ability_loadout = data.get('ability_loadout', [])
        player.ability_cooldowns = data.get('ability_cooldowns', {})
        player.active_buffs = data.get('active_buffs', {})
        player.status_effects = data.get('status_effects', {
            'poison': {'damage': 0, 'duration': 0},
            'stun': {'duration': 0},
            'slow': {'amount': 0, 'duration': 0},
            'invisible': {'duration': 0},
            'shield': {'amount': 0, 'duration': 0}
        })
        # Check for weekly reset when loading
        player.check_weekly_reset()
        return player

class DataManager:
    def __init__(self):
        self.data_file = 'player_data.json'
        self.players: Dict[str, PlayerData] = {}
        self.load_data()
    
    def load_data(self):
        """Load player data from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.players = {pid: PlayerData.from_dict(player_data) 
                                  for pid, player_data in data.items()}
                
                # Clean up any invalid equipment from existing players
                self.cleanup_invalid_equipment()
            except Exception as e:
                print(f"Error loading data: {e}")
                self.players = {}
    
    def cleanup_invalid_equipment(self):
        """Remove invalid equipment from existing players"""
        for player in self.players.values():
            # Check each equipment slot
            for slot in ['helmet', 'armor', 'gloves', 'pants', 'boots']:
                if player.equipment[slot] and player.equipment[slot] not in EQUIPMENT_DATA['armor']:
                    print(f"Warning: Invalid armor {player.equipment[slot]} for {player.username}, removing")
                    player.equipment[slot] = None
            
            # Check weapons
            for slot in ['mainhand', 'offhand']:
                if player.equipment[slot] and player.equipment[slot] not in EQUIPMENT_DATA['weapons']:
                    print(f"Warning: Invalid weapon {player.equipment[slot]} for {player.username}, removing")
                    player.equipment[slot] = None
        
        # Save cleaned data
        self.save_data()
    
    def save_data(self):
        """Save player data to file"""
        try:
            data = {pid: player.to_dict() for pid, player in self.players.items()}
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def get_or_create_player(self, player_id: str = None) -> PlayerData:
        """Get existing player or create new one"""
        if player_id and player_id in self.players:
            return self.players[player_id]
        
        player = PlayerData(player_id)
        self.players[player.player_id] = player
        self.save_data()
        return player
    
    def update_player_rating(self, winner_id: str, loser_id: str):
        """Update ELO ratings after a match"""
        if winner_id not in self.players or loser_id not in self.players:
            return
        
        winner = self.players[winner_id]
        loser = self.players[loser_id]
        
        # Simple ELO calculation
        expected_winner = 1 / (1 + 10 ** ((loser.rating - winner.rating) / 400))
        expected_loser = 1 - expected_winner
        
        k_factor = 32
        winner.rating = int(winner.rating + k_factor * (1 - expected_winner))
        loser.rating = int(loser.rating + k_factor * (0 - expected_loser))
        
        winner.add_win()
        loser.add_loss()
        
        self.save_data()
    
    def get_leaderboard(self) -> List[Tuple[str, PlayerData]]:
        """Get sorted leaderboard"""
        return sorted(self.players.items(), key=lambda x: x[1].rating, reverse=True)
    
    def find_opponent(self, player: PlayerData) -> Optional[PlayerData]:
        """Find a suitable opponent based on rating"""
        candidates = []
        for other_player in self.players.values():
            if other_player.player_id != player.player_id:
                rating_diff = abs(other_player.rating - player.rating)
                if rating_diff <= 200:  # Within 200 rating points
                    candidates.append(other_player)
        
        if not candidates:
            # If no suitable opponent, create a bot
            return self._create_bot_opponent(player.rating)
        
        return random.choice(candidates)
    
    def _create_bot_opponent(self, rating: int) -> PlayerData:
        """Create a bot opponent with similar rating"""
        bot = PlayerData()
        bot.username = f"Bot_{random.randint(1, 999)}"
        bot.rating = max(800, rating + random.randint(-100, 100))
        
        # Give bot random equipment - only use valid equipment from current data
        armor_types = list(EQUIPMENT_DATA['armor'].keys())
        weapon_types = list(EQUIPMENT_DATA['weapons'].keys())
        
        for slot in ['helmet', 'armor', 'gloves', 'pants', 'boots']:
            bot.equipment[slot] = random.choice([a for a in armor_types if slot in a])
        
        # Only use valid weapons from current equipment data
        bot.equipment['mainhand'] = random.choice(weapon_types)
        # Only equip shield if mainhand is not two-handed
        if bot.equipment['mainhand'] and not EQUIPMENT_DATA['weapons'][bot.equipment['mainhand']].get('two_handed', False):
            bot.equipment['offhand'] = random.choice([None, 'weapon_shield'])
        else:
            bot.equipment['offhand'] = None
        
        # Give bot random faction and abilities
        bot.faction = random.choice(list(FACTION_DATA.keys()))
        available_abilities = bot.get_available_abilities()
        # Give bot 2-4 random abilities
        num_abilities = random.randint(2, min(4, len(available_abilities)))
        bot.ability_loadout = random.sample(available_abilities, num_abilities)
        
        # Combat strategy removed - all bots attack only
        
        return bot

class MainMenu(FloatLayout):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        
        # Background image
        background = Image(
            source='assets/backgrounds/main_menu_background.png',
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.add_widget(background)
        
        # Logo (top center)
        logo = Image(
            source='assets/idle_duelist_icon_logo.png',
            size_hint=(0.6, 0.25),
            pos_hint={'center_x': 0.5, 'top': 0.9},
            allow_stretch=True,
            keep_ratio=True
        )
        self.add_widget(logo)
        
        # Main menu buttons container - centralized vertically
        button_container = BoxLayout(
            orientation='vertical',
            size_hint=(0.7, 0.5),
            pos_hint={'center_x': 0.5, 'center_y': 0.45},
            spacing=8
        )
        
        # Loadout Button
        self.loadout_btn = Button(
            text='Loadout',
            font_size='24sp',
            size_hint=(1, 0.18),
            background_color=(0.2, 0.6, 1, 0.9)
        )
        self.loadout_btn.bind(on_press=self.open_loadout)
        button_container.add_widget(self.loadout_btn)
        
        # Faction Button
        self.faction_btn = Button(
            text='Faction',
            font_size='24sp',
            size_hint=(1, 0.18),
            background_color=(0.8, 0.4, 0.8, 0.9)
        )
        self.faction_btn.bind(on_press=self.open_faction_screen)
        button_container.add_widget(self.faction_btn)
        
        # Abilities Button
        self.abilities_btn = Button(
            text='Abilities',
            font_size='24sp',
            size_hint=(1, 0.18),
            background_color=(0.4, 0.8, 0.8, 0.9)
        )
        self.abilities_btn.bind(on_press=self.open_abilities_screen)
        button_container.add_widget(self.abilities_btn)
        
        # Duel Button
        self.duel_btn = Button(
            text='Duel',
            font_size='24sp',
            size_hint=(1, 0.18),
            background_color=(1, 0.3, 0.3, 0.9)
        )
        self.duel_btn.bind(on_press=self.start_duel)
        button_container.add_widget(self.duel_btn)
        
        # Leaderboard Button
        self.leaderboard_btn = Button(
            text='Leaderboard',
            font_size='24sp',
            size_hint=(1, 0.18),
            background_color=(0.3, 1, 0.3, 0.9)
        )
        self.leaderboard_btn.bind(on_press=self.show_leaderboard)
        button_container.add_widget(self.leaderboard_btn)
        
        self.add_widget(button_container)
        
        # Audio controls container (bottom)
        audio_container = BoxLayout(
            orientation='horizontal',
            size_hint=(0.9, 0.08),
            pos_hint={'center_x': 0.5, 'bottom': 0.02},
            spacing=10
        )
        
        # Mute button - using music UI asset
        self.mute_btn = Button(
            background_normal='assets/ui/ui_music.png',
            background_down='assets/ui/ui_music.png',
            size_hint_x=0.2,
            border=(0, 0, 0, 0)  # Remove button border
        )
        self.mute_btn.bind(on_press=self.toggle_mute)
        
        # Initialize button appearance based on current mute state
        if self.app.music_manager.muted:
            self.mute_btn.background_color = (0.5, 0.5, 0.5, 1.0)  # Grayed out when muted
        else:
            self.mute_btn.background_color = (1.0, 1.0, 1.0, 1.0)  # Normal when unmuted
        
        # Volume label
        volume_label = Label(
            text='Volume:',
            size_hint_x=0.2,
            font_size='16sp',
            color=(1, 1, 1, 1)
        )
        
        # Volume slider
        self.volume_slider = Slider(
            min=0,
            max=1,
            value=self.app.music_manager.volume,
            size_hint_x=0.6
        )
        self.volume_slider.bind(value=self.on_volume_change)
        
        audio_container.add_widget(self.mute_btn)
        audio_container.add_widget(volume_label)
        audio_container.add_widget(self.volume_slider)
        self.add_widget(audio_container)
    
    def open_loadout(self, instance):
        self.app.show_loadout()
    
    def open_faction_screen(self, instance):
        self.app.show_faction_screen()
    
    def open_abilities_screen(self, instance):
        self.app.show_abilities_screen()
    
    def start_duel(self, instance):
        self.app.start_duel()
    
    def show_leaderboard(self, instance):
        self.app.show_leaderboard()
    
    def toggle_mute(self, instance):
        """Toggle mute state"""
        self.app.music_manager.set_muted(not self.app.music_manager.muted)
        # Visual feedback for mute state - slightly darken when muted
        if self.app.music_manager.muted:
            self.mute_btn.background_color = (0.5, 0.5, 0.5, 1.0)  # Grayed out when muted
        else:
            self.mute_btn.background_color = (1.0, 1.0, 1.0, 1.0)  # Normal when unmuted
    
    def on_volume_change(self, instance, value):
        """Handle volume slider change"""
        self.app.music_manager.set_volume(value)

class LoadoutScreen(FloatLayout):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        
        # Background image
        background = Image(
            source='assets/backgrounds/loadout_menu_background.png',
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.add_widget(background)
        
        # Header with Back button and Title
        header_container = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.08),
            pos_hint={'x': 0, 'top': 0.95},
            spacing=10,
            padding=[10, 0, 10, 0]
        )
        
        self.back_btn = Button(
            text='Back',
            size_hint_x=0.2,
            font_size='16sp',
            background_color=(0.3, 0.3, 0.3, 0.9)
        )
        self.back_btn.bind(on_press=self.go_back)
        
        title = Label(
            text='Loadout',
            font_size='20sp',
            size_hint_x=0.6,
            color=(1, 1, 1, 1)
        )
        
        header_container.add_widget(self.back_btn)
        header_container.add_widget(title)
        self.add_widget(header_container)
        
        # Username section
        username_container = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.08),
            pos_hint={'x': 0, 'top': 0.85},
            spacing=10,
            padding=[10, 0, 10, 0]
        )
        
        username_label = Label(
            text='Username:',
            size_hint_x=0.3,
            font_size='14sp',
            color=(1, 1, 1, 1)
        )
        
        self.username_input = TextInput(
            text=self.app.current_player.username,
            multiline=False,
            size_hint_x=0.5,
            font_size='14sp'
        )
        
        self.save_username_btn = Button(
            text='Save',
            size_hint_x=0.2,
            font_size='14sp',
            background_color=(0.2, 0.8, 0.2, 0.9)
        )
        self.save_username_btn.bind(on_press=self.save_username)
        
        username_container.add_widget(username_label)
        username_container.add_widget(self.username_input)
        username_container.add_widget(self.save_username_btn)
        self.add_widget(username_container)
        
        # Main equipment layout (following your concept)
        self.create_equipment_layout()
    
    def create_equipment_layout(self):
        """Create equipment layout following the concept design with FloatLayout positioning"""
        # Define slot dimensions (square slots)
        slot_size = 0.12  # 12% of screen width/height for square aspect
        slot_spacing = 0.015  # 1.5% spacing between slots
        
        # Left column: 5 armor slots (helmet, armor, gloves, pants, boots)
        armor_slots = ['helmet', 'armor', 'gloves', 'pants', 'boots']
        self.armor_slot_widgets = {}
        
        for i, slot in enumerate(armor_slots):
            # Calculate position for each slot (stacked vertically)
            y_pos = 0.77 - (i * (slot_size + slot_spacing))
            slot_widget = self.create_equipment_slot(slot, 'armor')
            slot_widget.size_hint = (slot_size, slot_size)
            slot_widget.pos_hint = {'x': 0.02, 'top': y_pos}
            self.armor_slot_widgets[slot] = slot_widget
            self.add_widget(slot_widget)
        
        # Top right: 2 weapon slots (mainhand, offhand)
        weapon_slots = ['mainhand', 'offhand']
        self.weapon_slot_widgets = {}
        
        for i, slot in enumerate(weapon_slots):
            # Calculate position for each weapon slot (stacked vertically)
            y_pos = 0.77 - (i * (slot_size + slot_spacing))
            slot_widget = self.create_equipment_slot(slot, 'weapon')
            slot_widget.size_hint = (slot_size, slot_size)
            slot_widget.pos_hint = {'x': 0.52, 'top': y_pos}
            self.weapon_slot_widgets[slot] = slot_widget
            self.add_widget(slot_widget)
        
        # Bottom right: Stats display area
        stats_container = BoxLayout(
            orientation='vertical',
            size_hint=(0.46, 0.37),
            pos_hint={'x': 0.52, 'top': 0.45},
            spacing=5,
            padding=[10, 10, 10, 10]
        )
        
        # Stats title
        stats_title = Label(
            text='Total Stats',
            font_size='16sp',
            color=(1, 1, 1, 1),
            size_hint_y=0.15
        )
        stats_container.add_widget(stats_title)
        
        # Stats display
        self.stats_label = Label(
            text='',
            font_size='14sp',
            color=(1, 1, 1, 1),
            size_hint_y=0.85,
            text_size=(None, None),
            halign='left',
            valign='top'
        )
        self.stats_label.bind(size=self.stats_label.setter('text_size'))
        stats_container.add_widget(self.stats_label)
        
        self.add_widget(stats_container)
        
        # Update stats display
        self.update_stats_display()
    
    def create_equipment_slot(self, slot, slot_type):
        """Create a single equipment slot widget using FloatLayout for precise positioning"""
        # Create main container using FloatLayout for precise control
        slot_container = FloatLayout()
        
        # Slot label (positioned at top of slot)
        label = Label(
            text=slot.title(),
            font_size='10sp',
            color=(1, 1, 1, 1),
            size_hint=(1, 0.25),
            pos_hint={'x': 0, 'top': 1}
        )
        slot_container.add_widget(label)
        
        # Equipment slot button (positioned below label, truly square)
        slot_btn = Button(
            text='',
            size_hint=(1, 0.75),
            pos_hint={'x': 0, 'top': 0.75},
            background_color=(0.2, 0.2, 0.2, 0.8)
        )
        slot_btn.bind(on_press=lambda instance, s=slot: self.show_equipment_popup(s))
        
        # Add current equipment image if equipped
        current_item = self.app.current_player.equipment[slot]
        if current_item:
            try:
                if slot_type == 'armor':
                    image_path = EQUIPMENT_DATA['armor'][current_item]['image']
                else:
                    image_path = EQUIPMENT_DATA['weapons'][current_item]['image']
                
                # Clear button text first to ensure image is visible
                slot_btn.text = ''
                
                # Create image widget as a separate widget in the container, not as a child of the button
                img_widget = Image(
                    source=image_path,
                    allow_stretch=True,
                    keep_ratio=True,
                    size_hint=(0.6, 0.6),  # Make icon smaller than button
                    pos_hint={'center_x': 0.5, 'center_y': 0.375}  # Center the icon in the button area
                )
                slot_container.add_widget(img_widget)
                print(f"Debug: Added image {image_path} to {slot} slot")
            except Exception as e:
                # Fallback if image not found
                slot_btn.text = 'Equipped'
                print(f"Error loading image for {current_item}: {e}")
        else:
            slot_btn.text = 'Empty'
        
        slot_container.add_widget(slot_btn)
        return slot_container
    
    def update_stats_display(self):
        """Update the stats display with current totals"""
        player = self.app.current_player
        stats_text = f"""⚔️ COMBAT STATS ⚔️
Speed: {player.get_total_speed()} (+{int(player.get_total_speed() * 0.5)}% crit)
Defense: {player.get_total_defense()}
Damage: {player.get_total_damage()}
Dodge: {int(player.get_dodge_chance() * 100)}%
Crit Chance: {int(player.get_total_crit_chance() * 100)}%
Armor Pen: {player.get_total_armor_penetration()}

📦 EQUIPMENT:
"""
        
        # Add current equipment list
        for slot in ['helmet', 'armor', 'gloves', 'pants', 'boots', 'mainhand', 'offhand']:
            item = player.equipment[slot]
            if item:
                if slot in ['helmet', 'armor', 'gloves', 'pants', 'boots']:
                    item_data = EQUIPMENT_DATA['armor'][item]
                    item_name = item_data['name']
                else:
                    item_data = EQUIPMENT_DATA['weapons'][item]
                    item_name = item_data['name']
                stats_text += f"{slot.title()}: {item_name}\n"
            else:
                stats_text += f"{slot.title()}: None\n"
        
        self.stats_label.text = stats_text
    
    def show_equipment_popup(self, slot):
        """Show equipment selection popup (mini-menu) for a slot"""
        # Determine equipment type and available items
        if slot in ['helmet', 'armor', 'gloves', 'pants', 'boots']:
            equipment_type = 'armor'
            # Filter armor by slot type - items end with _slotname
            slot_suffix = '_' + slot
            available_items = {k: v for k, v in EQUIPMENT_DATA['armor'].items() if k.endswith(slot_suffix)}
            print(f"Debug: Slot={slot}, Suffix={slot_suffix}, Available items: {list(available_items.keys())}")
        else:
            equipment_type = 'weapons'
            available_items = EQUIPMENT_DATA['weapons']
            print(f"Debug: Slot={slot}, Available weapons: {list(available_items.keys())}")
        
        # Create popup content - simplified layout
        popup_content = BoxLayout(
            orientation='vertical',
            spacing=5,
            padding=[5, 5, 5, 5]
        )
        
        # Title
        title_label = Label(
            text=f"Select {slot.title()}",
            font_size='18sp',
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=40
        )
        popup_content.add_widget(title_label)
        
        # Simple item list without ScrollView for now
        item_layout = BoxLayout(orientation='vertical', spacing=3, size_hint_y=0.8)
        
        print(f"Debug: Creating items for {len(available_items)} items")
        
        # None option
        none_btn = Button(
            text='None - Remove equipment',
            size_hint_y=None,
            height=60,
            font_size='16sp',
            background_color=(0.5, 0.5, 0.5, 1.0),
            color=(1, 1, 1, 1)
        )
        none_btn.bind(on_press=lambda x: self.equip_item_and_close(slot, None))
        item_layout.add_widget(none_btn)
        print(f"Debug: Added None button")
        
        # Available items
        for item_id, item_data in available_items.items():
            print(f"Debug: Processing item {item_id}: {item_data}")
            
            # Create stats text based on item type
            if equipment_type == 'armor':
                speed = item_data.get('speed', 0)
                defense = item_data.get('defense', 0)
                stats_text = f"Speed: {speed:+d}  Defense: {defense}"
            else:  # weapon
                damage = item_data.get('damage', 0)
                speed_bonus = item_data.get('speed_bonus', 0)
                crit_chance = item_data.get('crit_chance', 0.0)
                armor_pen = item_data.get('armor_penetration', 0)
                defense_bonus = item_data.get('defense_bonus', 0)
                
                stats_lines = [f"Damage: {damage}"]
                if speed_bonus != 0:
                    stats_lines.append(f"Speed: {speed_bonus:+d}")
                if crit_chance > 0:
                    stats_lines.append(f"Crit: {int(crit_chance * 100)}%")
                if armor_pen > 0:
                    stats_lines.append(f"Pen: {armor_pen}")
                if defense_bonus > 0:
                    stats_lines.append(f"Def: +{defense_bonus}")
                stats_text = "  ".join(stats_lines)
            
            item_btn = Button(
                text=f"{item_data['name']}\n{stats_text}",
                size_hint_y=None,
                height=60,
                font_size='14sp',
                background_color=(0.2, 0.6, 1.0, 1.0),
                color=(1, 1, 1, 1)
            )
            item_btn.bind(on_press=lambda x, item=item_id: self.equip_item_and_close(slot, item))
            item_layout.add_widget(item_btn)
            print(f"Debug: Added button for {item_id}")
        
        popup_content.add_widget(item_layout)
        
        # Close button
        close_btn = Button(
            text='Close',
            size_hint_y=None,
            height=50,
            font_size='16sp',
            background_color=(0.8, 0.2, 0.2, 1.0),
            color=(1, 1, 1, 1)
        )
        popup_content.add_widget(close_btn)
        
        # Create and show popup
        try:
            popup = Popup(
                title='',
                content=popup_content,
                size_hint=(0.9, 0.8),
                auto_dismiss=True,
                background_color=(0.1, 0.1, 0.1, 0.95)
            )
            
            close_btn.bind(on_press=popup.dismiss)
            popup.open()
            print(f"Debug: Popup opened for {slot} with {len(available_items)} items")
        except Exception as e:
            print(f"Error creating popup: {e}")
    
    def equip_item_and_close(self, slot, item_id):
        """Equip item and close popup, then refresh display"""
        self.equip_item(slot, item_id)
        # Close any open popups
        for child in self.children:
            if isinstance(child, Popup):
                child.dismiss()
        # Refresh the slot display
        self.refresh_slot_display(slot)
        # Update stats
        self.update_stats_display()
    
    def refresh_slot_display(self, slot):
        """Refresh the display of a specific slot"""
        # With FloatLayout positioning, we can directly replace the widget
        if slot in self.armor_slot_widgets:
            # Remove old widget
            old_widget = self.armor_slot_widgets[slot]
            self.remove_widget(old_widget)
            
            # Create new widget with same positioning
            slot_widget = self.create_equipment_slot(slot, 'armor')
            # Apply the same positioning as the original
            armor_slots = ['helmet', 'armor', 'gloves', 'pants', 'boots']
            slot_index = armor_slots.index(slot)
            slot_size = 0.12
            slot_spacing = 0.015
            y_pos = 0.77 - (slot_index * (slot_size + slot_spacing))
            
            slot_widget.size_hint = (slot_size, slot_size)
            slot_widget.pos_hint = {'x': 0.02, 'top': y_pos}
            self.armor_slot_widgets[slot] = slot_widget
            self.add_widget(slot_widget)
        
        elif slot in self.weapon_slot_widgets:
            # Remove old widget
            old_widget = self.weapon_slot_widgets[slot]
            self.remove_widget(old_widget)
            
            # Create new widget with same positioning
            slot_widget = self.create_equipment_slot(slot, 'weapon')
            # Apply the same positioning as the original
            weapon_slots = ['mainhand', 'offhand']
            slot_index = weapon_slots.index(slot)
            slot_size = 0.12
            slot_spacing = 0.015
            y_pos = 0.77 - (slot_index * (slot_size + slot_spacing))
            
            slot_widget.size_hint = (slot_size, slot_size)
            slot_widget.pos_hint = {'x': 0.52, 'top': y_pos}
            self.weapon_slot_widgets[slot] = slot_widget
            self.add_widget(slot_widget)
    
    def create_armor_selection(self, slot: str):
        """Create armor selection for a slot"""
        container = BoxLayout(orientation='vertical', size_hint_y=None, height=200)
        
        # Current equipment with image
        current = self.app.current_player.equipment.get(slot)
        current_layout = BoxLayout(orientation='horizontal', size_hint_y=0.4)
        
        if current:
            # Current equipment image
            current_img = Image(
                source=EQUIPMENT_DATA['armor'][current]['image'],
                size_hint_x=0.3,
                allow_stretch=True,
                keep_ratio=True
            )
            current_layout.add_widget(current_img)
            
            # Current equipment info
            current_info = BoxLayout(orientation='vertical', size_hint_x=0.7)
            current_info.add_widget(Label(
                text=f"Current: {EQUIPMENT_DATA['armor'][current]['name']}",
                font_size='14sp',
                size_hint_y=0.5
            ))
            current_info.add_widget(Label(
                text=f"Speed: {EQUIPMENT_DATA['armor'][current]['speed']}, Defense: {EQUIPMENT_DATA['armor'][current]['defense']}",
                font_size='12sp',
                size_hint_y=0.5
            ))
            current_layout.add_widget(current_info)
        else:
            current_layout.add_widget(Label(text="No equipment", size_hint_x=1))
        
        container.add_widget(current_layout)
        
        # Equipment options with images
        options_scroll = ScrollView(size_hint_y=0.6)
        options_layout = GridLayout(cols=1, spacing=3, size_hint_y=None)
        options_layout.bind(minimum_height=options_layout.setter('height'))
        
        # None option
        none_container = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        none_btn = Button(
            text='None',
            size_hint_x=1,
            font_size='12sp',
            background_color=(0.5, 0.5, 0.5, 0.8)
        )
        none_btn.bind(on_press=lambda x: self.equip_item(slot, None))
        none_container.add_widget(none_btn)
        options_layout.add_widget(none_container)
        
        # Available armor pieces for this slot
        for item_id, item_data in EQUIPMENT_DATA['armor'].items():
            if slot in item_id:
                item_container = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
                
                # Equipment image
                item_img = Image(
                    source=item_data['image'],
                    size_hint_x=0.3,
                    allow_stretch=True,
                    keep_ratio=True
                )
                item_container.add_widget(item_img)
                
                # Equipment button
                btn = Button(
                    text=f"{item_data['name']}\nSpeed: {item_data['speed']}, Defense: {item_data['defense']}",
                    size_hint_x=0.7,
                    font_size='10sp',
                    background_color=(0.3, 0.6, 0.8, 0.8)
                )
                btn.bind(on_press=lambda x, item=item_id: self.equip_item(slot, item))
                item_container.add_widget(btn)
                
                options_layout.add_widget(item_container)
        
        options_scroll.add_widget(options_layout)
        container.add_widget(options_scroll)
        self.equipment_layout.add_widget(container)
    
    def create_weapon_selection(self, slot: str):
        """Create weapon selection for a slot"""
        container = BoxLayout(orientation='vertical', size_hint_y=None, height=200)
        
        # Current equipment with image
        current = self.app.current_player.equipment.get(slot)
        current_layout = BoxLayout(orientation='horizontal', size_hint_y=0.4)
        
        if current:
            # Current equipment image
            current_img = Image(
                source=EQUIPMENT_DATA['weapons'][current]['image'],
                size_hint_x=0.3,
                allow_stretch=True,
                keep_ratio=True
            )
            current_layout.add_widget(current_img)
            
            # Current equipment info
            current_info = BoxLayout(orientation='vertical', size_hint_x=0.7)
            weapon_data = EQUIPMENT_DATA['weapons'][current]
            weapon_text = f"Current: {weapon_data['name']}"
            if weapon_data.get('two_handed', False):
                weapon_text += " (Two-Handed)"
            
            current_info.add_widget(Label(
                text=weapon_text,
                font_size='14sp',
                size_hint_y=0.5
            ))
            
            stats_text = f"Damage: {weapon_data['damage']}"
            if 'speed_bonus' in weapon_data:
                stats_text += f", Speed: {weapon_data['speed_bonus']:+d}"
            if 'defense_bonus' in weapon_data:
                stats_text += f", Defense: +{weapon_data['defense_bonus']}"
                
            current_info.add_widget(Label(
                text=stats_text,
                font_size='12sp',
                size_hint_y=0.5
            ))
            current_layout.add_widget(current_info)
        else:
            current_layout.add_widget(Label(text="No weapon", size_hint_x=1))
        
        container.add_widget(current_layout)
        
        # Equipment options with images
        options_scroll = ScrollView(size_hint_y=0.6)
        options_layout = GridLayout(cols=1, spacing=3, size_hint_y=None)
        options_layout.bind(minimum_height=options_layout.setter('height'))
        
        # None option
        none_container = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        none_btn = Button(
            text='None',
            size_hint_x=1,
            font_size='12sp',
            background_color=(0.5, 0.5, 0.5, 0.8)
        )
        none_btn.bind(on_press=lambda x: self.equip_item(slot, None))
        none_container.add_widget(none_btn)
        options_layout.add_widget(none_container)
        
        # Available weapons - filter based on slot and two-handed restrictions
        for item_id, item_data in EQUIPMENT_DATA['weapons'].items():
            # Skip if this is offhand and weapon is two-handed
            if slot == 'offhand' and item_data.get('two_handed', False):
                continue
            
            item_container = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
            
            # Equipment image
            item_img = Image(
                source=item_data['image'],
                size_hint_x=0.3,
                allow_stretch=True,
                keep_ratio=True
            )
            item_container.add_widget(item_img)
            
            # Equipment button
            button_text = item_data['name']
            if item_data.get('two_handed', False):
                button_text += " (2H)"
            
            button_text += f"\nDmg: {item_data['damage']}"
            if 'speed_bonus' in item_data:
                button_text += f", Spd: {item_data['speed_bonus']:+d}"
            if 'defense_bonus' in item_data:
                button_text += f", Def: +{item_data['defense_bonus']}"
            
            btn = Button(
                text=button_text,
                size_hint_x=0.7,
                font_size='10sp',
                background_color=(0.8, 0.4, 0.2, 0.8)
            )
            btn.bind(on_press=lambda x, item=item_id: self.equip_item(slot, item))
            item_container.add_widget(btn)
            
            options_layout.add_widget(item_container)
        
        options_scroll.add_widget(options_layout)
        container.add_widget(options_scroll)
        self.equipment_layout.add_widget(container)
    
    def equip_item(self, slot: str, item_id: Optional[str]):
        """Equip an item to a slot"""
        player = self.app.current_player
        
        # Handle two-handed weapon restrictions
        if slot == 'mainhand' and item_id and item_id in EQUIPMENT_DATA['weapons']:
            weapon = EQUIPMENT_DATA['weapons'][item_id]
            if weapon.get('two_handed', False):
                # Equipping two-handed weapon - clear offhand
                player.equipment['offhand'] = None
        
        elif slot == 'offhand' and item_id and item_id in EQUIPMENT_DATA['weapons']:
            weapon = EQUIPMENT_DATA['weapons'][item_id]
            if weapon.get('two_handed', False):
                # Can't equip two-handed weapon in offhand
                return
        
        # Check if mainhand is two-handed when trying to equip offhand
        if slot == 'offhand' and item_id:
            mainhand = player.equipment.get('mainhand')
            if mainhand and mainhand in EQUIPMENT_DATA['weapons']:
                if EQUIPMENT_DATA['weapons'][mainhand].get('two_handed', False):
                    # Mainhand is two-handed, can't equip offhand
                    return
        
        player.equipment[slot] = item_id
        self.app.data_manager.save_data()
        
        # Refresh the display
        self.refresh_slot_display(slot)
        self.update_stats_display()
        
        print(f"Debug: Equipped {item_id} to {slot} slot")
    
    def save_username(self, instance):
        """Save the username"""
        new_username = self.username_input.text.strip()
        if new_username:
            self.app.current_player.username = new_username
            self.app.data_manager.save_data()
    
    def go_back(self, instance):
        self.app.show_main_menu()

class FactionScreen(FloatLayout):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        
        # Background image
        background = Image(
            source='assets/backgrounds/loadout_menu_background.png',
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.add_widget(background)
        
        # Header with Back button and Title
        header_container = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.08),
            pos_hint={'x': 0, 'top': 0.95},
            spacing=10,
            padding=[10, 0, 10, 0]
        )
        
        self.back_btn = Button(
            text='Back',
            size_hint_x=0.2,
            font_size='16sp',
            background_color=(0.3, 0.3, 0.3, 0.9)
        )
        self.back_btn.bind(on_press=self.go_back)
        
        title = Label(
            text='Choose Your Faction',
            font_size='20sp',
            size_hint_x=0.6,
            color=(1, 1, 1, 1)
        )
        
        header_container.add_widget(self.back_btn)
        header_container.add_widget(title)
        self.add_widget(header_container)
        
        # Create faction selection
        self.create_faction_section()
    
    def create_faction_section(self):
        """Create detailed faction selection section"""
        # Clear existing faction widgets (keep header and background)
        widgets_to_remove = []
        for widget in self.children:
            if hasattr(widget, 'text') and ('Faction' in widget.text or 'Passive:' in widget.text or 'Abilities:' in widget.text):
                widgets_to_remove.append(widget)
            elif isinstance(widget, BoxLayout) and len(widget.children) > 0:
                # Check if it's the faction buttons container
                for child in widget.children:
                    if hasattr(child, 'text') and any(faction_name in child.text for faction_name in ['Order of the Silver Crusade', 'Shadow Covenant', 'Wilderness Tribe']):
                        widgets_to_remove.append(widget)
                        break
        
        for widget in widgets_to_remove:
            self.remove_widget(widget)
        
        # Current faction display
        current_faction = self.app.current_player.faction
        current_faction_data = FACTION_DATA[current_faction]
        
        # Current faction info
        current_faction_title = Label(
            text=f'Current Faction: {current_faction_data["name"]}',
            font_size='18sp',
            color=(1, 1, 1, 1),
            size_hint=(1, 0.05),
            pos_hint={'x': 0, 'top': 0.85}
        )
        self.add_widget(current_faction_title)
        
        # Current faction details
        faction_details = Label(
            text=f'{current_faction_data["description"]}\n\nPassive: {current_faction_data["passive"].replace("_", " ").title()}\nBonus: {int(current_faction_data["passive_value"] * 100)}%\n\nAbilities: {", ".join([ABILITY_DATA[aid]["name"] for aid in current_faction_data["abilities"]])}',
            font_size='14sp',
            color=(1, 1, 1, 1),
            size_hint=(1, 0.25),
            pos_hint={'x': 0, 'top': 0.8},
            text_size=(None, None),
            halign='left',
            valign='top'
        )
        faction_details.bind(size=faction_details.setter('text_size'))
        self.add_widget(faction_details)
        
        # Faction selection title
        selection_title = Label(
            text='Select a Different Faction:',
            font_size='16sp',
            color=(1, 1, 1, 1),
            size_hint=(1, 0.05),
            pos_hint={'x': 0, 'top': 0.5}
        )
        self.add_widget(selection_title)
        
        # Faction buttons container
        faction_container = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.35),
            pos_hint={'x': 0, 'top': 0.45},
            spacing=10,
            padding=[10, 0, 10, 0]
        )
        
        # Create faction buttons
        for faction_id, faction_data in FACTION_DATA.items():
            if faction_id == current_faction:
                continue  # Skip current faction
                
            faction_btn = Button(
                text=f"{faction_data['name']}\n{faction_data['description']}\nPassive: {int(faction_data['passive_value'] * 100)}% {faction_data['passive'].replace('_', ' ').title()}",
                font_size='12sp',
                background_color=faction_data['theme_colors']['primary'] + (0.8,),
                size_hint_y=None,
                height=80
            )
            faction_btn.bind(on_press=lambda x, fid=faction_id: self.select_faction(fid))
            faction_container.add_widget(faction_btn)
        
        self.add_widget(faction_container)
    
    
    def select_faction(self, faction_id: str):
        """Select a faction and reset abilities"""
        self.app.current_player.faction = faction_id
        # Reset abilities when changing factions
        self.app.current_player.ability_loadout = []
        self.app.current_player.ability_cooldowns = {}
        self.app.data_manager.save_data()
        
        # Update UI
        self.create_faction_section()
        
        # Show faction change confirmation
        faction_data = FACTION_DATA[faction_id]
        popup = Popup(
            title=faction_data['name'],
            content=Label(
                text=f"You have joined {faction_data['name']}!\n\n{faction_data['description']}\n\nPassive: {faction_data['passive'].replace('_', ' ').title()}\nBonus: {int(faction_data['passive_value'] * 100)}%\n\nYour abilities have been reset. Visit the Abilities menu to select new abilities.",
                text_size=(300, None),
                halign='center'
            ),
            size_hint=(0.8, 0.5)
        )
        popup.open()
    
    
    def go_back(self, instance):
        self.app.show_main_menu()

class AbilitiesScreen(FloatLayout):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        
        # Background image
        background = Image(
            source='assets/backgrounds/loadout_menu_background.png',
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.add_widget(background)
        
        # Header with Back button and Title
        header_container = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.08),
            pos_hint={'x': 0, 'top': 0.95},
            spacing=10,
            padding=[10, 0, 10, 0]
        )
        
        self.back_btn = Button(
            text='Back',
            size_hint_x=0.2,
            font_size='16sp',
            background_color=(0.3, 0.3, 0.3, 0.9)
        )
        self.back_btn.bind(on_press=self.go_back)
        
        title = Label(
            text='Ability Loadout',
            font_size='20sp',
            size_hint_x=0.6,
            color=(1, 1, 1, 1)
        )
        
        header_container.add_widget(self.back_btn)
        header_container.add_widget(title)
        self.add_widget(header_container)
        
        # Create ability slots section
        self.create_ability_slots()
        # Create loadout type section
        self.create_loadout_types()
    
    def create_ability_slots(self):
        """Create the 6 ability slots"""
        # Faction info
        faction_data = self.app.current_player.get_faction_data()
        faction_info = Label(
            text=f'Faction: {faction_data["name"]}',
            font_size='16sp',
            color=(1, 1, 1, 1),
            size_hint=(1, 0.05),
            pos_hint={'x': 0, 'top': 0.85}
        )
        self.add_widget(faction_info)
        
        # Ability slots container - centered with proper spacing
        slots_container = BoxLayout(
            orientation='horizontal',
            size_hint=(0.8, 0.12),
            pos_hint={'center_x': 0.5, 'center_y': 0.68},
            spacing=15,
            padding=[0, 0, 0, 0]
        )
        
        # Create 5 ability slots with proper square containers
        self.ability_slots = []
        for i in range(5):
            # Create a square container for the slot
            slot_container = FloatLayout(
                size_hint=(None, None),
                size=(80, 80),  # Perfect square
                pos_hint={'center_x': 0.5, 'center_y': 0.5}
            )
            
            # Background button for interaction (square)
            slot_button = Button(
                text='',
                background_color=(0.3, 0.3, 0.3, 0.9),
                size_hint=(1, 1),
                pos_hint={'x': 0, 'y': 0}
            )
            slot_button.bind(on_press=lambda x, slot_num=i: self.open_ability_selector(slot_num))
            slot_container.add_widget(slot_button)
            
            # Image widget for ability (perfectly square)
            ability_image = Image(
                source='',
                size_hint=(1, 1),
                pos_hint={'x': 0, 'y': 0},
                allow_stretch=False,
                keep_ratio=True
            )
            slot_container.add_widget(ability_image)
            
            self.ability_slots.append({
                'container': slot_container,
                'button': slot_button,
                'image': ability_image
            })
            slots_container.add_widget(slot_container)
        
        self.add_widget(slots_container)
        self.update_slot_display()
    
    def update_slot_display(self):
        """Update the display of ability slots"""
        for i, slot_data in enumerate(self.ability_slots):
            button = slot_data['button']
            image = slot_data['image']
            
            # Ensure loadout has 5 slots
            if not hasattr(self.app.current_player, 'ability_loadout') or self.app.current_player.ability_loadout is None:
                self.app.current_player.ability_loadout = [None] * 5
            
            while len(self.app.current_player.ability_loadout) < 5:
                self.app.current_player.ability_loadout.append(None)
            
            ability_id = self.app.current_player.ability_loadout[i] if i < len(self.app.current_player.ability_loadout) else None
            
            if ability_id is not None and ability_id in ABILITY_DATA:
                ability_data = ABILITY_DATA[ability_id]
                # Show ability image in square slot
                image.source = ability_data['image']
                image.opacity = 1
                button.text = ''
                button.background_color = (0.2, 0.2, 0.2, 0.5)  # Dark overlay for contrast
            else:
                # Hide image and show empty slot
                image.source = ''
                image.opacity = 0
                button.text = ''
                button.background_color = (0.3, 0.3, 0.3, 0.9)  # Gray for empty
    
    def open_ability_selector(self, slot_num: int):
        """Open ability selector popup for a specific slot"""
        available_abilities = self.app.current_player.get_available_abilities()
        current_loadout = self.app.current_player.ability_loadout or []
        
        # Filter out abilities already used in other slots (excluding None values)
        used_abilities = set([aid for aid in current_loadout if aid is not None])
        if slot_num < len(current_loadout) and current_loadout[slot_num] is not None:
            # If slot already has an ability, remove it from used set so we can change it
            used_abilities.remove(current_loadout[slot_num])
        
        available_for_slot = [aid for aid in available_abilities if aid not in used_abilities]
        
        # Create popup content
        popup_layout = BoxLayout(
            orientation='vertical',
            spacing=10,
            padding=[10, 10, 10, 10]
        )
        
        title = Label(
            text=f'Select Ability for Slot {slot_num + 1}',
            font_size='16sp',
            size_hint_y=None,
            height=40
        )
        popup_layout.add_widget(title)
        
        # Scroll view for abilities
        scroll = ScrollView(size_hint=(1, 1))
        abilities_layout = BoxLayout(
            orientation='vertical',
            spacing=5,
            size_hint_y=None
        )
        abilities_layout.bind(minimum_height=abilities_layout.setter('height'))
        
        # Add "Clear Slot" option
        clear_btn = Button(
            text='Clear Slot',
            font_size='14sp',
            size_hint_y=None,
            height=40,
            background_color=(0.8, 0.2, 0.2, 0.8)
        )
        clear_btn.bind(on_press=lambda x: self.set_slot_ability(slot_num, None))
        abilities_layout.add_widget(clear_btn)
        
        # Add available abilities
        for ability_id in available_for_slot:
            ability_data = ABILITY_DATA[ability_id]
            
            ability_btn = Button(
                text=f"{ability_data['name']}\n{ability_data['description']}\nCD: {ability_data['cooldown']}",
                font_size='12sp',
                size_hint_y=None,
                height=80,
                background_color=(0.2, 0.6, 0.8, 0.8)
            )
            ability_btn.bind(on_press=lambda x, aid=ability_id: self.set_slot_ability(slot_num, aid))
            abilities_layout.add_widget(ability_btn)
        
        scroll.add_widget(abilities_layout)
        popup_layout.add_widget(scroll)
        
        # Close button
        close_btn = Button(
            text='Close',
            font_size='14sp',
            size_hint_y=None,
            height=40,
            background_color=(0.3, 0.3, 0.3, 0.8)
        )
        popup_layout.add_widget(close_btn)
        
        popup = Popup(
            title='',
            content=popup_layout,
            size_hint=(0.8, 0.7)
        )
        close_btn.bind(on_press=lambda x: popup.dismiss())
        popup.open()
    
    def set_slot_ability(self, slot_num: int, ability_id: str = None):
        """Set ability for a specific slot"""
        # Initialize loadout as a list of 5 None values if needed
        if not hasattr(self.app.current_player, 'ability_loadout') or self.app.current_player.ability_loadout is None:
            self.app.current_player.ability_loadout = [None] * 5
        
        # Ensure loadout list is exactly 5 slots
        while len(self.app.current_player.ability_loadout) < 5:
            self.app.current_player.ability_loadout.append(None)
        
        # Set the ability for this slot
        self.app.current_player.ability_loadout[slot_num] = ability_id
        
        # Save and update display
        self.app.data_manager.save_data()
        self.update_slot_display()
    
    def create_loadout_types(self):
        """Create loadout type selection (Aggressive/Defensive/Hybrid)"""
        loadout_title = Label(
            text='Loadout Type',
            font_size='16sp',
            color=(1, 1, 1, 1),
            size_hint=(1, 0.05),
            pos_hint={'x': 0, 'top': 0.25}
        )
        self.add_widget(loadout_title)
        
        # Combat strategy UI removed - attack only combat
    
    
    def go_back(self, instance):
        self.app.show_main_menu()

class CombatScreen(FloatLayout):
    def __init__(self, app, opponent: PlayerData, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.opponent = opponent
        self.turn = 1
        self.player_hp = 100
        self.opponent_hp = 100
        self.combat_log = []  # Detailed text log
        self.combat_ended = False
        # Defending removed - attack only combat
        
        # Ability rotation tracking
        self.player_ability_index = 0
        self.opponent_ability_index = 0
        
        # Damage tracking for tiebreaking
        self.player_damage_dealt = 0
        self.opponent_damage_dealt = 0
        
        # Turn limit
        self.max_turns = 50
        
        # NEW: Combat speed control
        self.combat_speed = 1.0  # 1x, 2x, or 3x
        self.combat_speed_multiplier = 1.0
        
        # NEW: Combat log visibility
        self.log_visible = False
        
        # NEW: Last damage breakdown for display
        self.last_damage_breakdown = {}
        
        # NEW: Combo tracking
        self.player_combo_count = 0
        self.opponent_combo_count = 0
        self.last_ability_user = None
        
        self.setup_ui()
        self.start_combat()
    
    def setup_ui(self):
        """Setup the combat UI"""
        # Background image
        background = Image(
            source='assets/backgrounds/duel_background.png',
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.add_widget(background)
        
        # Header with Turn label and controls
        header_container = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.08),
            pos_hint={'x': 0, 'top': 0.95},
            spacing=5,
            padding=[5, 0, 5, 0]
        )
        
        # Turn label
        self.turn_label = Label(
            text='Turn 1',
            font_size='16sp',
            size_hint_x=0.3,
            color=(1, 1, 1, 1)
        )
        header_container.add_widget(self.turn_label)
        
        # Combat speed button
        self.speed_btn = Button(
            text='Speed: 1x',
            font_size='12sp',
            size_hint_x=0.25,
            background_color=(0.3, 0.6, 0.9, 0.9)
        )
        self.speed_btn.bind(on_press=self.toggle_combat_speed)
        header_container.add_widget(self.speed_btn)
        
        # Combat log toggle button
        self.log_toggle_btn = Button(
            text='Log: OFF',
            font_size='12sp',
            size_hint_x=0.25,
            background_color=(0.6, 0.3, 0.9, 0.9)
        )
        self.log_toggle_btn.bind(on_press=self.toggle_combat_log)
        header_container.add_widget(self.log_toggle_btn)
        
        # Damage breakdown button
        self.breakdown_btn = Button(
            text='Stats',
            font_size='11sp',
            size_hint_x=0.15,
            background_color=(0.9, 0.6, 0.3, 0.9)
        )
        self.breakdown_btn.bind(on_press=self.show_damage_breakdown)
        header_container.add_widget(self.breakdown_btn)
        
        # Abilities info button
        self.abilities_btn = Button(
            text='Info',
            font_size='11sp',
            size_hint_x=0.15,
            background_color=(0.3, 0.9, 0.9, 0.9)
        )
        self.abilities_btn.bind(on_press=self.show_abilities_info)
        header_container.add_widget(self.abilities_btn)
        
        self.add_widget(header_container)
        
        # Combatants section (player vs opponent)
        combatants_container = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.4),
            pos_hint={'x': 0, 'top': 0.85},
            spacing=5
        )
        
        # Player info with equipment display
        player_container = BoxLayout(orientation='horizontal', size_hint_y=0.45)
        
        # Player name and HP
        player_header = BoxLayout(orientation='vertical', size_hint_x=0.3)
        player_header.add_widget(Label(
            text=self.app.current_player.username,
            font_size='14sp',
            size_hint_y=0.5,
            color=(1, 1, 1, 1)
        ))
        player_container.add_widget(player_header)
        
        # Player equipment display
        player_equipment = BoxLayout(orientation='horizontal', size_hint_x=0.4)
        
        # Mainhand weapon
        if self.app.current_player.equipment['mainhand']:
            mainhand_img = Image(
                source=EQUIPMENT_DATA['weapons'][self.app.current_player.equipment['mainhand']]['image'],
                size_hint_x=0.5,
                allow_stretch=True,
                keep_ratio=True
            )
            player_equipment.add_widget(mainhand_img)
        else:
            player_equipment.add_widget(Label(text='No Weapon', size_hint_x=0.5, color=(1, 1, 1, 1)))
        
        # Offhand weapon/shield
        if self.app.current_player.equipment['offhand']:
            offhand_img = Image(
                source=EQUIPMENT_DATA['weapons'][self.app.current_player.equipment['offhand']]['image'],
                size_hint_x=0.5,
                allow_stretch=True,
                keep_ratio=True
            )
            player_equipment.add_widget(offhand_img)
        else:
            player_equipment.add_widget(Label(text='No Offhand', size_hint_x=0.5, color=(1, 1, 1, 1)))
        
        player_container.add_widget(player_equipment)
        
        # Player stats
        self.player_stats_label = Label(
            text=f'Speed: {self.app.current_player.get_total_speed()}\n'
                 f'Defense: {self.app.current_player.get_total_defense()}\n'
                 f'Damage: {self.app.current_player.get_total_damage()}',
            font_size='10sp',
            size_hint_x=0.3,
            color=(1, 1, 1, 1)
        )
        player_container.add_widget(self.player_stats_label)
        combatants_container.add_widget(player_container)
        
        # VS
        combatants_container.add_widget(Label(
            text='VS',
            font_size='20sp',
            size_hint_y=0.1,
            color=(1, 1, 0, 1)
        ))
        
        # Opponent info with equipment display
        opponent_container = BoxLayout(orientation='horizontal', size_hint_y=0.45)
        
        # Opponent name and HP
        opponent_header = BoxLayout(orientation='vertical', size_hint_x=0.3)
        opponent_header.add_widget(Label(
            text=self.opponent.username,
            font_size='14sp',
            size_hint_y=0.5,
            color=(1, 1, 1, 1)
        ))
        opponent_container.add_widget(opponent_header)
        
        # Opponent equipment display
        opponent_equipment = BoxLayout(orientation='horizontal', size_hint_x=0.4)
        
        # Mainhand weapon
        if self.opponent.equipment['mainhand']:
            mainhand_img = Image(
                source=EQUIPMENT_DATA['weapons'][self.opponent.equipment['mainhand']]['image'],
                size_hint_x=0.5,
                allow_stretch=True,
                keep_ratio=True
            )
            opponent_equipment.add_widget(mainhand_img)
        else:
            opponent_equipment.add_widget(Label(text='No Weapon', size_hint_x=0.5, color=(1, 1, 1, 1)))
        
        # Offhand weapon/shield
        if self.opponent.equipment['offhand']:
            offhand_img = Image(
                source=EQUIPMENT_DATA['weapons'][self.opponent.equipment['offhand']]['image'],
                size_hint_x=0.5,
                allow_stretch=True,
                keep_ratio=True
            )
            opponent_equipment.add_widget(offhand_img)
        else:
            opponent_equipment.add_widget(Label(text='No Offhand', size_hint_x=0.5, color=(1, 1, 1, 1)))
        
        opponent_container.add_widget(opponent_equipment)
        
        # Opponent stats
        self.opponent_stats_label = Label(
            text=f'Speed: {self.opponent.get_total_speed()}\n'
                 f'Defense: {self.opponent.get_total_defense()}\n'
                 f'Damage: {self.opponent.get_total_damage()}',
            font_size='10sp',
            size_hint_x=0.3,
            color=(1, 1, 1, 1)
        )
        opponent_container.add_widget(self.opponent_stats_label)
        combatants_container.add_widget(opponent_container)
        
        self.add_widget(combatants_container)
        
        # Visual combat area (replaces combat log)
        self.combat_area = FloatLayout(
            size_hint=(1, 0.47),
            pos_hint={'x': 0, 'bottom': 0.02}
        )
        
        # Top section - Turn count and Skip button
        self.create_top_section()
        
        # Middle section - Health bars and player icons
        self.create_middle_section()
        
        # Bottom section - Combat status text
        self.create_bottom_section()
        
        # Hit splat container for floating damage numbers
        self.hit_splats = []
        
        # NEW: Combat log display (initially hidden)
        self.combat_log_scroll = ScrollView(
            size_hint=(0.95, 0.3),
            pos_hint={'center_x': 0.5, 'bottom': 0.15},
            opacity=0
        )
        self.combat_log_text = Label(
            text='',
            font_size='10sp',
            color=(1, 1, 1, 1),
            size_hint_y=None,
            halign='left',
            valign='top',
            markup=True
        )
        self.combat_log_text.bind(texture_size=self.combat_log_text.setter('size'))
        self.combat_log_scroll.add_widget(self.combat_log_text)
        self.combat_area.add_widget(self.combat_log_scroll)
        
        # NEW: Status effect indicators containers
        self.player_status_container = BoxLayout(
            orientation='horizontal',
            size_hint=(0.35, 0.06),
            pos_hint={'center_x': 0.25, 'center_y': 0.75},
            spacing=2
        )
        self.opponent_status_container = BoxLayout(
            orientation='horizontal',
            size_hint=(0.35, 0.06),
            pos_hint={'center_x': 0.75, 'center_y': 0.75},
            spacing=2
        )
        self.combat_area.add_widget(self.player_status_container)
        self.combat_area.add_widget(self.opponent_status_container)
        
        # NEW: Combo counter displays
        self.player_combo_label = Label(
            text='',
            font_size='14sp',
            color=(1, 0.5, 0, 1),
            size_hint=(0.2, 0.06),
            pos_hint={'center_x': 0.25, 'center_y': 0.68},
            bold=True
        )
        self.opponent_combo_label = Label(
            text='',
            font_size='14sp',
            color=(1, 0.5, 0, 1),
            size_hint=(0.2, 0.06),
            pos_hint={'center_x': 0.75, 'center_y': 0.68},
            bold=True
        )
        self.combat_area.add_widget(self.player_combo_label)
        self.combat_area.add_widget(self.opponent_combo_label)
        
        self.add_widget(self.combat_area)
    
    def create_top_section(self):
        """Create top section with turn count and skip button"""
        # Turn count label
        self.turn_count_label = Label(
            text='Turn 1',
            font_size='14sp',
            color=(1, 1, 1, 1),
            size_hint=(0.3, 0.08),
            pos_hint={'x': 0.05, 'top': 0.95}
        )
        
        self.combat_area.add_widget(self.turn_count_label)
    
    def create_middle_section(self):
        """Create middle section with health bars and player icons"""
        # Health bars
        self.create_health_bars()
        
        # Player icons
        self.create_player_icons()
    
    def create_bottom_section(self):
        """Create bottom section with combat status text"""
        self.combat_status = Label(
            text='Combat Starting...',
            font_size='12sp',
            color=(1, 1, 1, 1),
            size_hint=(0.9, 0.08),
            pos_hint={'center_x': 0.5, 'bottom': 0.05},
            halign='center'
        )
        self.combat_area.add_widget(self.combat_status)
    
    def create_player_icons(self):
        """Player icons removed for cleaner interface"""
        pass
    
    def create_health_bars(self):
        """Create animated health bars for both players"""
        # Player health bar container
        player_hp_container = FloatLayout(
            size_hint=(0.4, 0.08),
            pos_hint={'center_x': 0.25, 'center_y': 0.85}
        )
        
        # Player HP background
        self.player_hp_bar_bg = Button(
            text='',
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0},
            background_color=(0.3, 0.3, 0.3, 0.8)
        )
        
        # Player HP bar (overlay)
        self.player_hp_bar = Button(
            text='',
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0},
            background_color=(0, 1, 0, 0.8)
        )
        
        player_hp_container.add_widget(self.player_hp_bar_bg)
        player_hp_container.add_widget(self.player_hp_bar)
        
        # Opponent health bar container
        opponent_hp_container = FloatLayout(
            size_hint=(0.4, 0.08),
            pos_hint={'center_x': 0.75, 'center_y': 0.85}
        )
        
        # Opponent HP background
        self.opponent_hp_bar_bg = Button(
            text='',
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0},
            background_color=(0.3, 0.3, 0.3, 0.8)
        )
        
        # Opponent HP bar (overlay)
        self.opponent_hp_bar = Button(
            text='',
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0},
            background_color=(0, 1, 0, 0.8)
        )
        
        opponent_hp_container.add_widget(self.opponent_hp_bar_bg)
        opponent_hp_container.add_widget(self.opponent_hp_bar)
        
        # Add to combat area
        self.combat_area.add_widget(player_hp_container)
        self.combat_area.add_widget(opponent_hp_container)
    
    def update_health_bar(self, player_type: str, current_hp: int, max_hp: int = 100):
        """Update health bar with animation"""
        hp_percentage = current_hp / max_hp
        
        # Determine color based on HP percentage (same for both players)
        if hp_percentage > 0.5:
            color = (0, 1, 0, 0.8)  # Green
        elif hp_percentage > 0.2:
            color = (1, 1, 0, 0.8)  # Yellow
        else:
            color = (1, 0, 0, 0.8)  # Red
        
        if player_type == 'player':
            # Animate player health bar
            anim = Animation(size_hint_x=hp_percentage, duration=0.5, t='out_cubic')
            anim.start(self.player_hp_bar)
            self.player_hp_bar.background_color = color
            
        else:
            # Animate opponent health bar
            anim = Animation(size_hint_x=hp_percentage, duration=0.5, t='out_cubic')
            anim.start(self.opponent_hp_bar)
            self.opponent_hp_bar.background_color = color
    
    def create_hit_splat(self, damage: int, x_pos: float, y_pos: float, is_critical: bool = False, is_heal: bool = False):
        """Create a floating damage number (hit splat)"""
        # Choose color and text
        if is_heal:
            color = (0, 1, 0, 1)  # Green for healing
            text = f"+{damage}"
        elif is_critical:
            color = (1, 0, 0, 1)  # Red for critical hits
            text = f"{damage}!"
        else:
            color = (1, 1, 1, 1)  # White for normal damage
            text = str(damage)
        
        # Create hit splat label
        hit_splat = Label(
            text=text,
            font_size='20sp',
            color=color,
            size_hint=(None, None),
            size=(60, 30),
            pos_hint={'center_x': x_pos, 'center_y': y_pos}
        )
        
        # Add to combat area
        self.combat_area.add_widget(hit_splat)
        
        # Animate the hit splat
        # Move up and fade out
        anim = Animation(
            pos_hint={'center_x': x_pos, 'center_y': y_pos + 0.2},
            opacity=0,
            duration=1.5,
            t='out_quad'
        )
        anim.bind(on_complete=lambda *args: self.combat_area.remove_widget(hit_splat))
        anim.start(hit_splat)
    
    def create_ability_effect(self, ability: Dict, attacker_type: str):
        """Create a brief ability icon effect with enhanced visuals"""
        # Get ability image path
        ability_image_path = ability.get('image', 'assets/abilities/ability_divine_strike.PNG')
        
        # Create ability icon
        ability_icon = Image(
            source=ability_image_path,
            size_hint=(0.15, 0.15),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            opacity=0.8
        )
        
        # Add to combat area
        self.combat_area.add_widget(ability_icon)
        
        # NEW: Enhanced animation with scale effect
        anim_sequence = (
            Animation(opacity=1, size_hint=(0.18, 0.18), duration=0.2, t='out_back') + 
            Animation(size_hint=(0.15, 0.15), duration=0.1) +
            Animation(opacity=0, duration=0.8)
        )
        anim_sequence.bind(on_complete=lambda *args: self.combat_area.remove_widget(ability_icon))
        anim_sequence.start(ability_icon)
    
    # NEW: Combat control methods
    def toggle_combat_speed(self, instance):
        """Toggle combat speed between 1x, 2x, and 3x"""
        if self.combat_speed == 1.0:
            self.combat_speed = 2.0
            self.speed_btn.text = 'Speed: 2x'
            self.speed_btn.background_color = (0.3, 0.9, 0.6, 0.9)
        elif self.combat_speed == 2.0:
            self.combat_speed = 3.0
            self.speed_btn.text = 'Speed: 3x'
            self.speed_btn.background_color = (0.9, 0.3, 0.3, 0.9)
        else:
            self.combat_speed = 1.0
            self.speed_btn.text = 'Speed: 1x'
            self.speed_btn.background_color = (0.3, 0.6, 0.9, 0.9)
    
    def toggle_combat_log(self, instance):
        """Toggle combat log visibility"""
        self.log_visible = not self.log_visible
        if self.log_visible:
            self.combat_log_scroll.opacity = 1
            self.log_toggle_btn.text = 'Log: ON'
            self.log_toggle_btn.background_color = (0.3, 0.9, 0.3, 0.9)
        else:
            self.combat_log_scroll.opacity = 0
            self.log_toggle_btn.text = 'Log: OFF'
            self.log_toggle_btn.background_color = (0.6, 0.3, 0.9, 0.9)
    
    def show_damage_breakdown(self, instance):
        """Show popup with detailed damage breakdown"""
        if not self.last_damage_breakdown:
            return
        
        breakdown = self.last_damage_breakdown
        breakdown_text = "[b]Last Attack Breakdown[/b]\n\n"
        breakdown_text += f"Attacker: {breakdown.get('attacker', 'N/A')}\n"
        breakdown_text += f"Defender: {breakdown.get('defender', 'N/A')}\n\n"
        breakdown_text += f"Base Damage: {breakdown.get('base_damage', 0)}\n"
        
        if breakdown.get('crit', False):
            breakdown_text += f"Critical Hit: x1.5\n"
        if breakdown.get('damage_buffs', 0) > 0:
            breakdown_text += f"Damage Buffs: +{breakdown.get('damage_buffs', 0)}%\n"
        if breakdown.get('combo', 0) > 0:
            breakdown_text += f"Combo Bonus: +{(breakdown.get('combo', 1) - 1) * 5}%\n"
        if breakdown.get('armor_pen', 0) > 0:
            breakdown_text += f"Armor Penetration: {breakdown.get('armor_pen', 0)}\n"
        
        breakdown_text += f"\nDefense: -{breakdown.get('defense', 0)}\n"
        if breakdown.get('damage_reduction', 0) > 0:
            breakdown_text += f"Damage Reduction: -{breakdown.get('damage_reduction', 0)}%\n"
        
        breakdown_text += f"\n[b]Final Damage: {breakdown.get('final_damage', 0)}[/b]"
        
        # Create popup
        content = Label(text=breakdown_text, markup=True, halign='left', valign='top')
        popup = Popup(
            title='Damage Breakdown',
            content=content,
            size_hint=(0.8, 0.6)
        )
        popup.open()
    
    def show_abilities_info(self, instance):
        """Show popup with abilities info for both players"""
        # Create scrollable content
        scroll = ScrollView(size_hint=(1, 1))
        content_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10, padding=10)
        content_layout.bind(minimum_height=content_layout.setter('height'))
        
        # Player abilities
        content_layout.add_widget(Label(
            text=f"[b][color=00ff00]{self.app.current_player.username}'s Abilities[/color][/b]",
            markup=True,
            size_hint_y=None,
            height=30,
            font_size='14sp'
        ))
        
        for ability_id in self.app.current_player.ability_loadout:
            if ability_id and ability_id in ABILITY_DATA:
                ability = ABILITY_DATA[ability_id]
                ability_text = f"[b]{ability['name']}[/b]\n{ability['description']}\nCooldown: {ability['cooldown']} turns"
                content_layout.add_widget(Label(
                    text=ability_text,
                    markup=True,
                    size_hint_y=None,
                    height=80,
                    font_size='11sp',
                    halign='left',
                    valign='top',
                    text_size=(300, None)
                ))
        
        # Separator
        content_layout.add_widget(Label(text='', size_hint_y=None, height=20))
        
        # Opponent abilities
        content_layout.add_widget(Label(
            text=f"[b][color=ff0000]{self.opponent.username}'s Abilities[/color][/b]",
            markup=True,
            size_hint_y=None,
            height=30,
            font_size='14sp'
        ))
        
        for ability_id in self.opponent.ability_loadout:
            if ability_id and ability_id in ABILITY_DATA:
                ability = ABILITY_DATA[ability_id]
                ability_text = f"[b]{ability['name']}[/b]\n{ability['description']}\nCooldown: {ability['cooldown']} turns"
                content_layout.add_widget(Label(
                    text=ability_text,
                    markup=True,
                    size_hint_y=None,
                    height=80,
                    font_size='11sp',
                    halign='left',
                    valign='top',
                    text_size=(300, None)
                ))
        
        scroll.add_widget(content_layout)
        
        # Create popup
        popup = Popup(
            title='Combat Abilities Info',
            content=scroll,
            size_hint=(0.9, 0.8)
        )
        popup.open()
    
    def _add_to_combat_log(self, message: str):
        """Add message to combat log"""
        self.combat_log.append(message)
        # Update log text (keep last 20 messages)
        log_text = '\n'.join(self.combat_log[-20:])
        self.combat_log_text.text = log_text
    
    def update_status_indicators(self):
        """Update status effect indicators for both players"""
        # Clear existing indicators
        self.player_status_container.clear_widgets()
        self.opponent_status_container.clear_widgets()
        
        # Player status effects
        for effect, data in self.app.current_player.status_effects.items():
            if self._has_active_effect(data):
                icon = self._get_status_icon(effect)
                duration = self._get_effect_duration(data)
                label = Label(
                    text=f'{icon}{duration}',
                    font_size='10sp',
                    size_hint_x=None,
                    width=30,
                    color=(1, 1, 1, 1)
                )
                self.player_status_container.add_widget(label)
        
        # Opponent status effects
        for effect, data in self.opponent.status_effects.items():
            if self._has_active_effect(data):
                icon = self._get_status_icon(effect)
                duration = self._get_effect_duration(data)
                label = Label(
                    text=f'{icon}{duration}',
                    font_size='10sp',
                    size_hint_x=None,
                    width=30,
                    color=(1, 1, 1, 1)
                )
                self.opponent_status_container.add_widget(label)
    
    def _has_active_effect(self, data):
        """Check if effect is active"""
        if isinstance(data, dict):
            return data.get('duration', 0) > 0 or data.get('damage', 0) > 0 or data.get('amount', 0) > 0
        return False
    
    def _get_effect_duration(self, data):
        """Get duration of effect"""
        if isinstance(data, dict):
            return data.get('duration', 0)
        return 0
    
    def _get_status_icon(self, effect):
        """Get icon for status effect"""
        icons = {
            'poison': '☠️',
            'stun': '😵',
            'invisible': '👻',
            'slow': '🐌',
            'shield': '🛡️'
        }
        return icons.get(effect, '?')
    
    def update_combo_display(self, attacker_type: str):
        """Update combo counter display"""
        if attacker_type == 'player':
            if self.player_combo_count > 1:
                self.player_combo_label.text = f'COMBO x{self.player_combo_count}!'
                # Animate combo label
                anim = Animation(font_size='16sp', duration=0.1) + Animation(font_size='14sp', duration=0.1)
                anim.start(self.player_combo_label)
            else:
                self.player_combo_label.text = ''
        else:
            if self.opponent_combo_count > 1:
                self.opponent_combo_label.text = f'COMBO x{self.opponent_combo_count}!'
                # Animate combo label
                anim = Animation(font_size='16sp', duration=0.1) + Animation(font_size='14sp', duration=0.1)
                anim.start(self.opponent_combo_label)
            else:
                self.opponent_combo_label.text = ''
    
    def start_combat(self):
        """Start the automatic combat sequence"""
        player_speed = self.app.current_player.get_total_speed()
        opponent_speed = self.opponent.get_total_speed()
        player_damage = self.app.current_player.get_total_damage()
        opponent_damage = self.opponent.get_total_damage()
        player_defense = self.app.current_player.get_total_defense()
        opponent_defense = self.opponent.get_total_defense()
        
        # Update combat status
        self.combat_status.text = f"⚔️ {self.app.current_player.username} vs {self.opponent.username}"
        
        # Determine turn order
        if player_speed >= opponent_speed:
            self.combat_status.text = f"🚀 {self.app.current_player.username} goes first!"
            self.player_first = True
        else:
            self.combat_status.text = f"🚀 {self.opponent.username} goes first!"
            self.player_first = False
        
        # Start the automatic combat
        Clock.schedule_once(self.execute_turn, 1.0)
    
    def execute_turn(self, dt):
        """Execute one complete turn (both players act)"""
        if self.combat_ended:
            return
        
        # Update turn status
        self.combat_status.text = f"═══ TURN {self.turn} ═══"
        self._add_to_combat_log(f"\n═══ TURN {self.turn} ═══")
        
        # NEW: Update status effect indicators
        self.update_status_indicators()
        
        # Update health bars
        self.update_health_bar('player', self.player_hp)
        self.update_health_bar('opponent', self.opponent_hp)
        
        # Determine actions for both players
        player_action = self.get_player_action()
        opponent_action = self.get_opponent_action()
        
        # NEW: Calculate action delay based on combat speed
        action_delay = 0.3 / self.combat_speed
        
        # Execute actions based on turn order
        if self.player_first:
            self.execute_action(self.app.current_player, self.opponent, player_action, 'player')
            if not self.combat_ended:
                Clock.schedule_once(lambda dt: self.execute_action(self.opponent, self.app.current_player, opponent_action, 'opponent'), action_delay)
        else:
            self.execute_action(self.opponent, self.app.current_player, opponent_action, 'opponent')
            if not self.combat_ended:
                Clock.schedule_once(lambda dt: self.execute_action(self.app.current_player, self.opponent, player_action, 'player'), action_delay)
        
        # Check if combat continues
        if not self.combat_ended:
            self.turn += 1
            self.turn_count_label.text = f'Turn {self.turn}'
            self.turn_label.text = f'Turn {self.turn}'
            
            # Check turn limit
            if self.turn >= self.max_turns:
                self.combat_status.text = f"⏰ Turn limit reached! ({self.max_turns} turns)"
                self._add_to_combat_log(f"⏰ Turn limit reached! ({self.max_turns} turns)")
                self.end_combat_by_damage()
                return
            
            # NEW: Schedule next turn with combat speed multiplier
            turn_delay = 0.7 / self.combat_speed
            Clock.schedule_once(self.execute_turn, turn_delay)
    
    def get_player_action(self) -> str:
        """Get player action - simplified to attack only"""
        return self.app.current_player.get_action(self.player_hp, self.opponent_hp)
    
    def get_opponent_action(self) -> str:
        """Get opponent action (AI) - simplified to attack only"""
        return self.opponent.get_action(self.opponent_hp, self.player_hp)
    
    def execute_action(self, attacker: PlayerData, defender: PlayerData, action: str, attacker_type: str):
        """Execute an action for a player with faction abilities and passives"""
        # Process status effects at start of turn
        attacker.process_status_effects()
        defender.process_status_effects()
        
        # Reduce cooldowns
        attacker.reduce_cooldowns()
        defender.reduce_cooldowns()
        
        # Try to use abilities first (rotation system)
        if attacker.ability_loadout and any(aid for aid in attacker.ability_loadout if aid is not None):
            # Get the next ability in rotation
            next_ability = self._get_next_ability_in_rotation(attacker)
            if next_ability and attacker.can_use_ability(next_ability):
                ability_result = attacker.use_ability(next_ability)
                if ability_result['success']:
                    self._execute_ability(attacker, defender, ability_result, attacker_type)
                    return
        
        # Regular attack action (defend removed)
        self._execute_attack(attacker, defender, attacker_type)
    
    def _execute_ability(self, attacker: PlayerData, defender: PlayerData, ability_result: Dict, attacker_type: str):
        """Execute an ability"""
        ability = ability_result['ability']
        effects = ability_result['effects']
        
        # Get faction color for ability text
        faction_data = attacker.get_faction_data()
        faction_id = attacker.faction
        
        # Map faction IDs to their specific colors
        if faction_id == 'order_of_the_silver_crusade':
            hex_color = "ffa500"  # Orange
        elif faction_id == 'shadow_covenant':
            hex_color = "800080"  # Purple
        elif faction_id == 'wilderness_tribe':
            hex_color = "00ff00"  # Green
        else:
            hex_color = "ffffff"  # White fallback
        
        # Check for ability counterplay
        ability_id = None
        for aid, ability_data in ABILITY_DATA.items():
            if ability_data == ability:
                ability_id = aid
                break
        
        counterplay_applied = False
        if ability_id and ability_id in ABILITY_COUNTERS:
            counter_abilities = ABILITY_COUNTERS[ability_id]
            # Check if defender has any countering abilities active
            for counter_ability_id in counter_abilities:
                if counter_ability_id in defender.active_buffs:
                    # Apply counterplay effect
                    counterplay_applied = True
                    self.combat_status.text = f"🛡️ {defender.username}'s {ABILITY_DATA[counter_ability_id]['name']} counters {ability['name']}!"
                    break
        
        if not counterplay_applied:
            # Show ability usage in combat status
            self.combat_status.text = f"✨ {attacker.username} uses {ability['name']}!"
            self._add_to_combat_log(f"✨ {attacker.username} uses {ability['name']}!")
        else:
            self._add_to_combat_log(f"🛡️ {defender.username}'s ability counters {ability['name']}!")
        
        # Show ability icon briefly
        self.create_ability_effect(ability, attacker_type)
        
        # Apply ability effects
        if 'heal_amount' in effects:
            old_hp = attacker.hp
            heal_amount = effects['heal_amount']
            attacker.hp = min(attacker.max_hp, attacker.hp + heal_amount)
            actual_heal = attacker.hp - old_hp
            
            # Show healing in combat status
            if actual_heal > 0:
                self.combat_status.text = f"💚 {attacker.username} heals for {actual_heal} HP!"
            
            # Update HP display and create heal splat
            if attacker == self.app.current_player:
                self.player_hp = attacker.hp
                self.update_health_bar('player', self.player_hp)
                if actual_heal > 0:
                    self.create_hit_splat(actual_heal, 0.25, 0.5, is_heal=True)
            else:
                self.opponent_hp = attacker.hp
                self.update_health_bar('opponent', self.opponent_hp)
                if actual_heal > 0:
                    self.create_hit_splat(actual_heal, 0.75, 0.5, is_heal=True)
        
        if 'damage_amount' in effects:
            damage = effects['damage_amount']
            self._apply_damage(defender, damage, attacker_type, ability['name'])
        
        if 'damage_multiplier' in effects:
            # Check if this is an immediate damage ability (like Shadow Strike)
            if ability.get('guaranteed_crit', False):
                # Shadow Strike - deal immediate damage with multiplier
                base_damage = attacker.get_total_damage()
                damage_multiplier = effects['damage_multiplier']
                immediate_damage = int(base_damage * damage_multiplier)
                self.combat_status.text = f"⚡ {attacker.username} uses {ability['name']} for {immediate_damage} damage!"
                self._apply_damage(defender, immediate_damage, attacker_type, ability['name'])
            else:
                # Store damage multiplier for next attack
                attacker.active_buffs['damage_multiplier'] = effects['damage_multiplier']
        
        if 'stun_duration' in effects:
            defender.status_effects['stun']['duration'] = effects['stun_duration']
        
        if 'poison_damage' in effects and 'duration' in effects:
            defender.status_effects['poison']['damage'] = effects['poison_damage']
            defender.status_effects['poison']['duration'] = effects['duration']
        
        # Handle other effects
        if 'damage_reduction' in effects and 'duration' in effects:
            attacker.active_buffs['damage_reduction'] = {
                'value': effects['damage_reduction'],
                'duration': effects['duration']
            }
        
        if 'damage_bonus' in effects and 'duration' in effects:
            attacker.active_buffs['damage_bonus'] = {
                'value': effects['damage_bonus'],
                'duration': effects['duration']
            }
        
        if 'crit_bonus' in effects and 'duration' in effects:
            attacker.active_buffs['crit_bonus'] = {
                'value': effects['crit_bonus'],
                'duration': effects['duration']
            }
        
        if 'stat_bonus' in effects and 'duration' in effects:
            attacker.active_buffs['stat_bonus'] = {
                'value': effects['stat_bonus'],
                'duration': effects['duration']
            }
        
        if 'reflect_damage' in effects and 'duration' in effects:
            attacker.active_buffs['reflect_damage'] = {
                'value': effects['reflect_damage'],
                'duration': effects['duration']
            }
        
        if 'invisibility_duration' in effects:
            attacker.status_effects['invisible']['duration'] = effects['invisibility_duration']
        
        # Handle debuff removal (Purification)
        if 'heal_amount' in effects and ability.get('name') == 'Purification':
            # Remove all debuffs from attacker
            attacker.status_effects['poison']['damage'] = 0
            attacker.status_effects['poison']['duration'] = 0
            attacker.status_effects['stun']['duration'] = 0
            attacker.status_effects['slow']['amount'] = 0
            attacker.status_effects['slow']['duration'] = 0
    
    def _execute_attack(self, attacker: PlayerData, defender: PlayerData, attacker_type: str):
        """Execute a regular attack with enhanced tracking and combo system"""
        # Check if attacker is stunned (BUG FIX: was checking defender instead of attacker)
        if attacker.status_effects['stun']['duration'] > 0:
            self.combat_status.text = f"😵 {attacker.username} is stunned!"
            self._add_to_combat_log(f"😵 {attacker.username} is stunned and cannot attack!")
            # Reset combo
            if attacker_type == 'player':
                self.player_combo_count = 0
            else:
                self.opponent_combo_count = 0
            self.update_combo_display(attacker_type)
            return
        
        # Check for dodge first
        dodge_chance = defender.get_dodge_chance()
        if random.random() < dodge_chance:
            self.combat_status.text = f"💨 {defender.username} dodges!"
            self._add_to_combat_log(f"💨 {defender.username} dodges the attack!")
            # Reset combo on dodge
            if attacker_type == 'player':
                self.player_combo_count = 0
            else:
                self.opponent_combo_count = 0
            self.update_combo_display(attacker_type)
            return
        
        # NEW: Track combo (increment if same attacker, reset if different)
        if self.last_ability_user == attacker_type:
            if attacker_type == 'player':
                self.player_combo_count += 1
            else:
                self.opponent_combo_count += 1
        else:
            if attacker_type == 'player':
                self.player_combo_count = 1
                self.opponent_combo_count = 0
            else:
                self.opponent_combo_count = 1
                self.player_combo_count = 0
        self.last_ability_user = attacker_type
        
        # Calculate base damage
        base_damage_original = attacker.get_total_damage()
        base_damage = base_damage_original
        
        # Apply faction passive bonuses
        faction_data = attacker.get_faction_data()
        if faction_data['passive'] == 'shadow_mastery':
            # Shadow Covenant gets crit chance bonus
            pass  # Already handled in get_total_crit_chance
        
        # Apply active buffs
        damage_buff_percent = 0
        if 'damage_multiplier' in attacker.active_buffs:
            multiplier = attacker.active_buffs['damage_multiplier']
            base_damage = int(base_damage * multiplier)
            damage_buff_percent = int((multiplier - 1) * 100)
            del attacker.active_buffs['damage_multiplier']  # Remove after use
        
        # Apply faction secondary passive bonuses
        secondary_passives = attacker.get_faction_secondary_passive()
        if 'stealth_damage_bonus' in secondary_passives and attacker.status_effects['invisible']['duration'] > 0:
            bonus = secondary_passives['stealth_damage_bonus']
            base_damage = int(base_damage * (1 + bonus))
            damage_buff_percent += int(bonus * 100)
        if 'nature_affinity_bonus' in secondary_passives and defender.status_effects['slow']['duration'] > 0:
            bonus = secondary_passives['nature_affinity_bonus']
            base_damage = int(base_damage * (1 + bonus))
            damage_buff_percent += int(bonus * 100)
        
        # Apply armor set bonuses
        set_bonuses = attacker.get_armor_set_bonus()
        if 'damage_bonus' in set_bonuses:
            bonus = set_bonuses['damage_bonus']
            base_damage = int(base_damage * (1 + bonus))
            damage_buff_percent += int(bonus * 100)
        
        # NEW: Apply combo bonus (5% per combo hit, max 25%)
        combo_count = self.player_combo_count if attacker_type == 'player' else self.opponent_combo_count
        if combo_count > 1:
            combo_bonus = min(0.25, (combo_count - 1) * 0.05)
            base_damage = int(base_damage * (1 + combo_bonus))
            damage_buff_percent += int(combo_bonus * 100)
        
        # Check for critical hit
        crit_chance = attacker.get_total_crit_chance()
        is_critical = random.random() < crit_chance
        if is_critical:
            base_damage = int(base_damage * 1.5)  # 50% damage bonus
        
        # Calculate effective defense (with armor penetration)
        total_defense = defender.get_total_defense()
        armor_penetration = attacker.get_total_armor_penetration()
        effective_defense = max(0, total_defense - armor_penetration)
        
        # Apply faction passive defense bonus
        damage_reduction_percent = 0
        if defender.get_faction_data()['passive'] == 'divine_protection':
            damage_reduction = defender.get_faction_passive_bonus()
            base_damage = int(base_damage * (1 - damage_reduction))
            damage_reduction_percent = int(damage_reduction * 100)
        
        # Apply armor set bonus damage reduction
        defender_set_bonuses = defender.get_armor_set_bonus()
        if 'damage_reduction' in defender_set_bonuses:
            reduction = defender_set_bonuses['damage_reduction']
            base_damage = int(base_damage * (1 - reduction))
            damage_reduction_percent += int(reduction * 100)
        
        # Calculate final damage
        actual_damage = max(1, base_damage - effective_defense)
        
        # NEW: Store damage breakdown for stats button
        self.last_damage_breakdown = {
            'attacker': attacker.username,
            'defender': defender.username,
            'base_damage': base_damage_original,
            'crit': is_critical,
            'damage_buffs': damage_buff_percent,
            'armor_pen': armor_penetration,
            'defense': effective_defense,
            'damage_reduction': damage_reduction_percent,
            'final_damage': actual_damage,
            'combo': combo_count if combo_count > 1 else 0
        }
        
        # Show attack in combat status and create hit splat
        combo_text = f" (COMBO x{combo_count})" if combo_count > 1 else ""
        if is_critical:
            self.combat_status.text = f"⚡ {attacker.username} CRITS for {actual_damage} damage!{combo_text}"
            self._add_to_combat_log(f"⚡ {attacker.username} lands a CRITICAL HIT for {actual_damage} damage!{combo_text}")
            # Create critical hit splat
            if attacker_type == 'player':
                self.create_hit_splat(actual_damage, 0.75, 0.5, is_critical=True)
            else:
                self.create_hit_splat(actual_damage, 0.25, 0.5, is_critical=True)
        else:
            self.combat_status.text = f"⚔️ {attacker.username} attacks for {actual_damage} damage!{combo_text}"
            self._add_to_combat_log(f"⚔️ {attacker.username} attacks for {actual_damage} damage!{combo_text}")
            # Create normal hit splat
            if attacker_type == 'player':
                self.create_hit_splat(actual_damage, 0.75, 0.5)
            else:
                self.create_hit_splat(actual_damage, 0.25, 0.5)
        
        # NEW: Update combo display
        self.update_combo_display(attacker_type)
        
        # Apply damage
        self._apply_damage(defender, actual_damage, attacker_type, "attack")
        
        # Handle damage reflection from armor set bonuses
        if 'damage_reflect' in defender_set_bonuses:
            reflect_damage = int(actual_damage * defender_set_bonuses['damage_reflect'])
            if reflect_damage > 0:
                self.combat_status.text = f"⚡ {defender.username} reflects {reflect_damage} damage back!"
                self._add_to_combat_log(f"⚡ {defender.username} reflects {reflect_damage} damage!")
                self._apply_damage(attacker, reflect_damage, 'opponent' if attacker_type == 'player' else 'player', "reflect")
    
    def _apply_damage(self, defender: PlayerData, damage: int, attacker_type: str, source: str):
        """Apply damage to defender"""
        if attacker_type == 'player':
            self.opponent_hp = max(0, self.opponent_hp - damage)
            self.update_health_bar('opponent', self.opponent_hp)
            # Track damage dealt by player
            self.player_damage_dealt += damage
        else:
            self.player_hp = max(0, self.player_hp - damage)
            self.update_health_bar('player', self.player_hp)
            # Track damage dealt by opponent
            self.opponent_damage_dealt += damage
        
        # Check for victory
        if self.opponent_hp <= 0:
            self.combat_status.text = f"💀 {self.opponent.username} is defeated!"
            self.end_combat('victory')
        elif self.player_hp <= 0:
            self.combat_status.text = f"💀 {self.app.current_player.username} is defeated!"
            self.end_combat('defeat')
    
    
    def end_combat(self, result: str):
        """End combat and show results"""
        self.combat_ended = True
        
        if result == 'victory':
            self.combat_status.text = f"🎉 VICTORY! {self.app.current_player.username} WINS! 🎉"
            self.app.data_manager.update_player_rating(
                self.app.current_player.player_id, 
                self.opponent.player_id
            )
        else:
            self.combat_status.text = f"💀 DEFEAT! {self.opponent.username} WINS! 💀"
            self.app.data_manager.update_player_rating(
                self.opponent.player_id,
                self.app.current_player.player_id
            )
        
        # Show result buttons after a delay
        Clock.schedule_once(self.show_result_buttons, 2.0)
    
    def end_combat_by_damage(self):
        """End combat based on damage dealt when turn limit is reached"""
        self.combat_ended = True
        
        # Update total damage dealt for both players
        self.app.current_player.total_damage_dealt += self.player_damage_dealt
        self.opponent.total_damage_dealt += self.opponent_damage_dealt
        
        # Determine winner based on damage dealt
        if self.player_damage_dealt > self.opponent_damage_dealt:
            self.combat_status.text = f"🎉 VICTORY! {self.app.current_player.username} WINS BY DAMAGE! ({self.player_damage_dealt} vs {self.opponent_damage_dealt}) 🎉"
            self.app.data_manager.update_player_rating(
                self.app.current_player.player_id, 
                self.opponent.player_id
            )
            result = 'victory'
        elif self.opponent_damage_dealt > self.player_damage_dealt:
            self.combat_status.text = f"💀 DEFEAT! {self.opponent.username} WINS BY DAMAGE! ({self.opponent_damage_dealt} vs {self.player_damage_dealt}) 💀"
            self.app.data_manager.update_player_rating(
                self.opponent.player_id,
                self.app.current_player.player_id
            )
            result = 'defeat'
        else:
            # Tie - both dealt same damage, player loses by default
            self.combat_status.text = f"🤝 TIE! {self.opponent.username} WINS BY DEFAULT! ({self.player_damage_dealt} damage each) 🤝"
            self.app.data_manager.update_player_rating(
                self.opponent.player_id,
                self.app.current_player.player_id
            )
            result = 'defeat'
        
        # Show result buttons after a delay
        Clock.schedule_once(self.show_result_buttons, 2.0)
    
    def show_result_buttons(self, dt):
        """Show result buttons after combat"""
        result_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        
        duel_again_btn = Button(text='Duel Again', background_color=(0.3, 1, 0.3, 1))
        duel_again_btn.bind(on_press=self.duel_again)
        
        main_menu_btn = Button(text='Main Menu', background_color=(0.3, 0.3, 1, 1))
        main_menu_btn.bind(on_press=self.go_to_main_menu)
        
        result_layout.add_widget(duel_again_btn)
        result_layout.add_widget(main_menu_btn)
        
        self.add_widget(result_layout)
    
    def duel_again(self, instance):
        """Start another duel"""
        self.app.start_duel()
    
    def go_to_main_menu(self, instance):
        """Go back to main menu"""
        # Switch back to background music
        self.app.music_manager.play_background()
        self.app.show_main_menu()
    
    def skip_to_end(self, instance):
        """Skip to end of combat"""
        self.combat_ended = True
        if self.player_hp > self.opponent_hp:
            self.end_combat('victory')
        else:
            self.end_combat('defeat')
    
    
    def _get_next_ability_in_rotation(self, attacker: PlayerData) -> str:
        """Get the next ability in rotation for the attacker"""
        if not attacker.ability_loadout:
            return None
        
        # Determine which index to use based on attacker type
        if attacker == self.app.current_player:
            current_index = self.player_ability_index
        else:
            current_index = self.opponent_ability_index
        
        # Find the next non-None ability in the loadout
        loadout = attacker.ability_loadout
        for i in range(len(loadout)):
            slot_index = (current_index + i) % len(loadout)
            ability_id = loadout[slot_index]
            if ability_id is not None:
                # Update the index for next time
                if attacker == self.app.current_player:
                    self.player_ability_index = (slot_index + 1) % len(loadout)
                else:
                    self.opponent_ability_index = (slot_index + 1) % len(loadout)
                return ability_id
        
        return None

class LeaderboardScreen(FloatLayout):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        
        # Background image
        background = Image(
            source='assets/backgrounds/leaderboard_menu_background.png',
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.add_widget(background)
        
        # Header with Back button, Title, and Refresh button
        header_container = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.08),
            pos_hint={'x': 0, 'top': 0.95},
            spacing=10,
            padding=[10, 0, 10, 0]
        )
        
        self.back_btn = Button(
            text='Back',
            size_hint_x=0.2,
            font_size='16sp',
            background_color=(0.3, 0.3, 0.3, 0.9)
        )
        self.back_btn.bind(on_press=self.go_back)
        
        title = Label(
            text='Leaderboard',
            font_size='20sp',
            size_hint_x=0.6,
            color=(1, 1, 1, 1)
        )
        
        self.refresh_btn = Button(
            text='Refresh',
            size_hint_x=0.2,
            font_size='16sp',
            background_color=(0.2, 0.8, 0.2, 0.9)
        )
        self.refresh_btn.bind(on_press=self.refresh_leaderboard)
        
        header_container.add_widget(self.back_btn)
        header_container.add_widget(title)
        header_container.add_widget(self.refresh_btn)
        self.add_widget(header_container)
        
        # Leaderboard scroll view
        self.scroll = ScrollView(
            size_hint=(1, 0.87),
            pos_hint={'x': 0, 'bottom': 0.02}
        )
        self.leaderboard_layout = GridLayout(cols=4, spacing=5, size_hint_y=None)
        self.leaderboard_layout.bind(minimum_height=self.leaderboard_layout.setter('height'))
        
        self.create_leaderboard()
        self.scroll.add_widget(self.leaderboard_layout)
        self.add_widget(self.scroll)
    
    def create_leaderboard(self):
        """Create the leaderboard display"""
        self.leaderboard_layout.clear_widgets()
        
        # Headers
        headers = ['Rank', 'Username', 'Rating', 'W/L']
        for header in headers:
            label = Label(text=header, font_size='16sp', size_hint_y=None, height=40)
            label.bold = True
            self.leaderboard_layout.add_widget(label)
        
        # Top 10 players
        leaderboard = self.app.data_manager.get_leaderboard()
        current_player_id = self.app.current_player.player_id
        
        for rank, (player_id, player) in enumerate(leaderboard[:10], 1):
            # Rank
            rank_label = Label(text=str(rank), font_size='14sp', size_hint_y=None, height=35)
            self.leaderboard_layout.add_widget(rank_label)
            
            # Username (highlight current player)
            username_label = Label(text=player.username, font_size='14sp', size_hint_y=None, height=35)
            if player_id == current_player_id:
                username_label.color = (1, 1, 0, 1)  # Yellow for current player
            self.leaderboard_layout.add_widget(username_label)
            
            # Rating
            rating_label = Label(text=str(player.rating), font_size='14sp', size_hint_y=None, height=35)
            self.leaderboard_layout.add_widget(rating_label)
            
            # Win/Loss
            wl_label = Label(text=f"{player.wins}/{player.losses}", font_size='14sp', size_hint_y=None, height=35)
            self.leaderboard_layout.add_widget(wl_label)
        
        # Show current player position if not in top 10
        if not any(player_id == current_player_id for player_id, _ in leaderboard[:10]):
            current_player_rank = next((rank for rank, (pid, _) in enumerate(leaderboard, 1) if pid == current_player_id), 11)
            current_player = self.app.current_player
            
            # Separator
            separator1 = Label(text='---', font_size='14sp', size_hint_y=None, height=35)
            separator2 = Label(text='---', font_size='14sp', size_hint_y=None, height=35)
            separator3 = Label(text='---', font_size='14sp', size_hint_y=None, height=35)
            separator4 = Label(text='---', font_size='14sp', size_hint_y=None, height=35)
            self.leaderboard_layout.add_widget(separator1)
            self.leaderboard_layout.add_widget(separator2)
            self.leaderboard_layout.add_widget(separator3)
            self.leaderboard_layout.add_widget(separator4)
            
            # Current player
            rank_label = Label(text=str(current_player_rank), font_size='14sp', size_hint_y=None, height=35)
            self.leaderboard_layout.add_widget(rank_label)
            
            username_label = Label(text=current_player.username, font_size='14sp', size_hint_y=None, height=35)
            username_label.color = (1, 1, 0, 1)  # Yellow for current player
            self.leaderboard_layout.add_widget(username_label)
            
            rating_label = Label(text=str(current_player.rating), font_size='14sp', size_hint_y=None, height=35)
            self.leaderboard_layout.add_widget(rating_label)
            
            wl_label = Label(text=f"{current_player.wins}/{current_player.losses}", font_size='14sp', size_hint_y=None, height=35)
            self.leaderboard_layout.add_widget(wl_label)
    
    def refresh_leaderboard(self, instance):
        """Refresh the leaderboard"""
        self.create_leaderboard()
    
    def go_back(self, instance):
        self.app.show_main_menu()

class IdleDuelistApp(App):
    def build(self):
        # Set mobile portrait resolution
        Window.size = (360, 640)  # Mobile portrait resolution
        Window.minimum_width = 360
        Window.minimum_height = 640
        Window.clearcolor = (0.1, 0.1, 0.1, 1)
        
        # Initialize data manager
        self.data_manager = DataManager()
        
        # Initialize music manager
        self.music_manager = MusicManager()
        
        # Get or create current player
        self.current_player = self.data_manager.get_or_create_player()
        
        # Initialize root widget
        self.root = BoxLayout()
        
        # Show main menu and start background music
        self.show_main_menu()
        self.music_manager.play_background()
        
        return self.root
    
    def show_main_menu(self):
        """Show the main menu"""
        self.root.clear_widgets()
        main_menu = MainMenu(self)
        self.root.add_widget(main_menu)
        # Play background music
        self.music_manager.play_background()
    
    def show_loadout(self):
        """Show the loadout screen"""
        self.root.clear_widgets()
        loadout = LoadoutScreen(self)
        self.root.add_widget(loadout)
        # Continue background music
        self.music_manager.play_background()
    
    def show_faction_screen(self):
        """Show the faction screen"""
        self.root.clear_widgets()
        faction_screen = FactionScreen(self)
        self.root.add_widget(faction_screen)
        # Continue background music
        self.music_manager.play_background()
    
    def show_abilities_screen(self):
        """Show the abilities screen"""
        self.root.clear_widgets()
        abilities_screen = AbilitiesScreen(self)
        self.root.add_widget(abilities_screen)
        # Continue background music
        self.music_manager.play_background()
    
    def start_duel(self):
        """Start a duel"""
        opponent = self.data_manager.find_opponent(self.current_player)
        if opponent:
            self.root.clear_widgets()
            combat = CombatScreen(self, opponent)
            self.root.add_widget(combat)
            # Switch to combat music
            self.music_manager.play_combat()
        else:
            # Show error popup
            popup = Popup(
                title='Error',
                content=Label(text='No opponent found!'),
                size_hint=(0.5, 0.3)
            )
            popup.open()
    
    def show_leaderboard(self):
        """Show the leaderboard"""
        self.root.clear_widgets()
        leaderboard = LeaderboardScreen(self)
        self.root.add_widget(leaderboard)
        # Continue background music
        self.music_manager.play_background()

if __name__ == '__main__':
    IdleDuelistApp().run()
