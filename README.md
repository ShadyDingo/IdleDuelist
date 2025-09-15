# Idle Duelist

A turn-based combat game featuring equipment progression, faction-based abilities, and competitive rankings.

## Game Overview

Idle Duelist is a strategic combat game where players duel other players in turn-based combat to gain victory points. Players compete in weekly and monthly rankings to receive equipment rewards based on their competitive bracket performance.

## Key Features

### Equipment System
- **Armor Types**: Cloth (high speed, low defense), Leather (balanced), Metal (low speed, high defense)
- **Weapon Types**: Axes, Bows, Crossbows, Knives, Maces, Hammers, Shields, Staffs, Swords
- **Rarity System**: Normal (1 stat), Uncommon (2 stats), Rare (3 stats), Epic (4 stats), Legendary (5 stats), Mythic (5 stats + special bonus)

### Core Stats
- **Attack Power**: Base damage dealt
- **Critical Hit Chance**: Chance to deal double damage
- **Dodge Chance**: Chance to avoid attacks completely
- **Defense**: Reduces incoming damage
- **Parry Chance**: Chance to deflect attacks and counter-attack
- **Accuracy**: Chance to hit enemies
- **Constitution**: Maximum health points
- **Speed**: Determines turn order in combat

### Faction System
Players can align with one of three factions, each offering unique abilities and passives:

1. **Order of the Silver Crusade**: Focus on defense and healing
   - Passive: Divine Protection (10% damage reduction)
   - Abilities: Divine Strike, Shield of Faith, Healing Light, Righteous Fury, Purification

2. **Shadow Covenant**: Focus on stealth and critical hits
   - Passive: Shadow Mastery (15% increased crit chance)
   - Abilities: Shadow Strike, Vanish, Poison Blade, Assassinate, Shadow Clone

3. **Wilderness Tribe**: Focus on nature magic and adaptability
   - Passive: Nature's Blessing (5% HP regeneration per turn)
   - Abilities: Nature's Wrath, Thorn Barrier, Wild Growth, Earthquake, Spirit Form

### Combat System
- Turn-based combat with speed determining turn order
- Players have 4 ability slots and cycle through abilities
- Each faction provides 5 abilities, but players can only use 4 at a time
- Combat continues until one player reaches 0 HP

## Installation and Running

### Desktop Version
1. Clone or download the game files
2. Ensure you have Python 3.7+ installed
3. Navigate to the game directory
4. Run the main game:

```bash
python game/main.py
```

### Mobile Version (Android)
1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Install Buildozer for Android builds:
```bash
pip install buildozer
```

3. Build the Android APK:
```bash
buildozer android debug
```

4. Install the APK on your Android device:
```bash
buildozer android deploy
```

### Mobile Development Setup
For mobile development, you'll need:
- Python 3.7+
- Kivy framework
- Android SDK and NDK
- Buildozer for Android builds

The mobile version includes:
- Touch-friendly UI
- Material Design components
- Responsive layouts for different screen sizes
- Mobile-optimized combat interface
- Gesture controls

## Game Structure

```
IdleDuelist/
├── game/                      # Core game logic
│   ├── __init__.py
│   ├── main.py               # Desktop entry point
│   ├── core/                 # Core game systems
│   │   ├── __init__.py
│   │   ├── stats.py         # Stat system and calculations
│   │   ├── equipment.py     # Equipment generation and management
│   │   ├── player.py        # Player class and management
│   │   ├── factions.py      # Faction abilities and passives
│   │   └── combat.py        # Turn-based combat system
│   └── ui/                  # Desktop UI
│       ├── __init__.py
│       └── game_interface.py # Desktop game interface
├── mobile_ui/               # Mobile UI components
│   ├── __init__.py
│   └── screens/             # Mobile screens
│       ├── __init__.py
│       ├── main_menu.py     # Main menu screen
│       ├── player_stats.py  # Player stats screen
│       ├── equipment.py    # Equipment management screen
│       ├── faction.py      # Faction management screen
│       ├── combat.py       # Combat screen
│       └── settings.py     # Settings screen
├── assets/                  # Game assets
│   └── README.md          # Asset guidelines
├── mobile_app.py          # Mobile app entry point
├── buildozer.spec        # Android build configuration
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Gameplay Features

### Main Menu Options
1. **View Player Stats**: See current character statistics and equipped items
2. **Manage Equipment**: Equip/unequip items and generate new equipment
3. **Manage Faction**: Change faction or modify ability slots
4. **Duel Another Player**: Fight against AI opponents
5. **View All Factions**: Learn about all available factions
6. **Generate Random Equipment**: Test equipment generation
7. **Simulate Combat**: Run combat simulations for testing

### Equipment Management
- Generate random equipment with different rarities
- Equip items to specific slots (helmet, chest, legs, boots, gloves, main_hand, off_hand)
- View detailed stat bonuses from equipped items
- Equipment affects all core stats and combat performance

### Combat Mechanics
- Speed determines turn order
- Accuracy vs Dodge chance for hit/miss
- Critical hits deal double damage
- Defense reduces incoming damage
- Faction abilities provide unique combat options
- Ability cycling system (4 slots, cycles through abilities)

## Future Development

Planned features include:
- Weekly/monthly ranking system
- Equipment reward distribution based on rankings
- Player vs Player matchmaking
- Data persistence for player progress
- Enhanced UI/UX
- Additional weapon and armor types
- More complex ability interactions
- Guild/clan system

## Contributing

This is a development project. Feel free to suggest improvements or report issues.

## License

This project is for educational and entertainment purposes.
