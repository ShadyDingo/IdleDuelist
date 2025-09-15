"""
Asset manager for Idle Duelist game assets.
Handles loading and managing images for equipment, abilities, and UI elements.
"""

import os
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from kivy.resources import resource_add_path
from kivy.metrics import dp


class AssetManager:
    """Manages game assets including images and icons."""
    
    def __init__(self):
        self.asset_path = os.path.join(os.path.dirname(__file__))
        self.loaded_images = {}
        
        # Add assets directory to Kivy resource path
        resource_add_path(self.asset_path)
        
        # Asset categories and their expected files
        self.asset_categories = {
            'weapons': [
                'sword', 'axe', 'bow', 'crossbow', 'knife', 'mace', 'hammer', 'shield', 'staff'
            ],
            'armor': [
                'cloth_helmet', 'cloth_armor', 'cloth_pants', 'cloth_boots', 'cloth_gloves',
                'leather_helmet', 'leather_armor', 'leather_pants', 'leather_boots', 'leather_gloves',
                'metal_helmet', 'metal_armor', 'metal_pants', 'metal_boots', 'metal_gloves'
            ],
            'abilities': [
                'divine_strike', 'shield_of_faith', 'healing_light', 'righteous_fury', 'purification',
                'shadow_strike', 'vanish', 'poison_blade', 'assassinate', 'shadow_clone',
                'natures_wrath', 'thorn_barrier', 'wild_growth', 'earthquake', 'spirit_form'
            ],
            'ui': [
                'attack', 'defense', 'speed', 'hp', 'crit', 'dodge', 'parry', 'accuracy',
                'constitution', 'victory_points'
            ],
            'rarity': [
                'normal', 'uncommon', 'rare', 'epic', 'legendary', 'mythic'
            ],
            'factions': [
                'order_of_the_silver_crusade', 'shadow_covenant', 'wilderness_tribe'
            ]
        }
        
        # Default fallback images (using emoji/text)
        self.fallback_images = {
            'weapons': '⚔️',
            'armor': '🛡️',
            'abilities': '✨',
            'ui': '📊',
            'rarity': '⭐',
            'factions': '🏛️'
        }
    
    def get_image_path(self, category, name, extension='png'):
        """Get the full path to an image asset."""
        # Handle different naming conventions
        if category == 'weapons':
            filename = f"weapon_{name}.{extension}"
        elif category == 'abilities':
            filename = f"ability_{name}.{extension}"
        elif category == 'armor':
            filename = f"armor_{name}.{extension}"
        elif category == 'ui':
            filename = f"ui_{name}.{extension}"
        elif category == 'factions':
            filename = f"faction_{name}.{extension}"
        else:
            filename = f"{name}.{extension}"
        
        return os.path.join(self.asset_path, category, filename)
    
    def load_image(self, category, name, size=None, fallback=None):
        """Load an image asset with optional size and fallback."""
        # Try different extensions (case insensitive)
        extensions = ['png', 'jpg', 'jpeg', 'gif', 'PNG', 'JPG', 'JPEG', 'GIF']
        
        for ext in extensions:
            image_path = self.get_image_path(category, name, ext)
            if os.path.exists(image_path):
                try:
                    if size:
                        img = Image(source=image_path, size=size, allow_stretch=True, keep_ratio=True)
                    else:
                        img = Image(source=image_path, allow_stretch=True, keep_ratio=True)
                    
                    cache_key = f"{category}_{name}_{ext}"
                    self.loaded_images[cache_key] = img
                    return img
                except Exception as e:
                    print(f"Error loading image {image_path}: {e}")
                    continue
        
        # Return fallback if image not found
        if fallback:
            return self.create_fallback_image(fallback, size)
        
        # Use default fallback for category
        default_fallback = self.fallback_images.get(category, '❓')
        return self.create_fallback_image(default_fallback, size)
    
    def create_fallback_image(self, text, size=None):
        """Create a fallback image with text/emoji."""
        from kivy.uix.label import Label
        
        if size:
            label = Label(
                text=text,
                font_size=dp(24),
                size=size,
                halign='center',
                valign='middle'
            )
        else:
            label = Label(
                text=text,
                font_size=dp(24),
                halign='center',
                valign='middle'
            )
        
        label.bind(size=label.setter('text_size'))
        return label
    
    def get_weapon_image(self, weapon_type, size=None):
        """Get weapon image by type."""
        weapon_name = weapon_type.value if hasattr(weapon_type, 'value') else str(weapon_type)
        return self.load_image('weapons', weapon_name, size)
    
    def get_armor_image(self, armor_type, slot, size=None):
        """Get armor image by type and slot."""
        # Map slot names to the new naming convention
        slot_mapping = {
            'chest': 'armor',
            'legs': 'pants'
        }
        
        # Use mapped slot name or original slot name
        mapped_slot = slot_mapping.get(slot, slot)
        armor_name = f"{armor_type.value}_{mapped_slot}" if hasattr(armor_type, 'value') else f"{armor_type}_{mapped_slot}"
        return self.load_image('armor', armor_name, size)
    
    def get_ability_image(self, ability_name, size=None):
        """Get ability image by name."""
        return self.load_image('abilities', ability_name.lower().replace(' ', '_'), size)
    
    def get_ui_image(self, ui_element, size=None):
        """Get UI element image."""
        return self.load_image('ui', ui_element, size)
    
    def get_rarity_image(self, rarity, size=None):
        """Get rarity border/icon image."""
        rarity_name = rarity.value if hasattr(rarity, 'value') else str(rarity)
        return self.load_image('rarity', rarity_name, size)
    
    def get_faction_image(self, faction, size=None):
        """Get faction image."""
        faction_name = faction.value if hasattr(faction, 'value') else str(faction)
        return self.load_image('factions', faction_name, size)
    
    def list_available_assets(self):
        """List all available asset files."""
        available = {}
        
        for category, items in self.asset_categories.items():
            category_path = os.path.join(self.asset_path, category)
            if os.path.exists(category_path):
                files = os.listdir(category_path)
                available[category] = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
            else:
                available[category] = []
        
        return available
    
    def create_asset_preview(self, category, name, size=(dp(64), dp(64))):
        """Create a preview widget for an asset."""
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        
        layout = BoxLayout(orientation='vertical', spacing=dp(5), size=size)
        
        # Image
        image_widget = self.load_image(category, name, size=(size[0], size[0] * 0.8))
        layout.add_widget(image_widget)
        
        # Label
        label = Label(
            text=name.replace('_', ' ').title(),
            font_size=dp(10),
            size_hint_y=0.2,
            halign='center'
        )
        label.bind(size=label.setter('text_size'))
        layout.add_widget(label)
        
        return layout
    
    def validate_assets(self):
        """Validate that all expected assets are present."""
        missing = {}
        available = self.list_available_assets()
        
        for category, expected_items in self.asset_categories.items():
            missing[category] = []
            for item in expected_items:
                found = False
                for ext in ['png', 'jpg', 'jpeg', 'gif']:
                    if f"{item}.{ext}" in available.get(category, []):
                        found = True
                        break
                if not found:
                    missing[category].append(item)
        
        return missing
    
    def get_asset_info(self):
        """Get information about available assets."""
        available = self.list_available_assets()
        missing = self.validate_assets()
        
        info = {
            'total_categories': len(self.asset_categories),
            'available_assets': sum(len(assets) for assets in available.values()),
            'missing_assets': sum(len(missing_items) for missing_items in missing.values()),
            'categories': {}
        }
        
        for category in self.asset_categories.keys():
            info['categories'][category] = {
                'available': len(available.get(category, [])),
                'expected': len(self.asset_categories[category]),
                'missing': len(missing.get(category, []))
            }
        
        return info
