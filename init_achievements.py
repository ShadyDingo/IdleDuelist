#!/usr/bin/env python3
"""
Initialize achievements
"""

import sqlite3

def init_achievements():
    """Initialize default achievements"""
    achievements = [
        # Combat Achievements
        ("First Blood", "Win your first duel", "combat", 1, "experience", 50, "⚔️"),
        ("Warrior", "Win 10 duels", "combat", 10, "experience", 200, "🛡️"),
        ("Champion", "Win 50 duels", "combat", 50, "experience", 1000, "👑"),
        ("Legend", "Win 100 duels", "combat", 100, "experience", 2500, "🌟"),
        ("Streak Master", "Achieve a 10-win streak", "combat", 10, "skill_points", 5, "🔥"),
        ("Perfect Victory", "Win a duel without taking damage", "combat", 1, "experience", 300, "✨"),
        
        # Progression Achievements
        ("Rising Star", "Reach level 10", "progression", 10, "skill_points", 10, "⭐"),
        ("Veteran", "Reach level 25", "progression", 25, "skill_points", 25, "🎖️"),
        ("Master", "Reach level 50", "progression", 50, "skill_points", 50, "🏆"),
        ("Grandmaster", "Reach level 100", "progression", 100, "skill_points", 100, "💎"),
        
        # Tournament Achievements
        ("Tournament Rookie", "Join your first tournament", "tournament", 1, "experience", 100, "🏅"),
        ("Tournament Veteran", "Join 10 tournaments", "tournament", 10, "experience", 500, "🥇"),
        ("Tournament Champion", "Win a tournament", "tournament", 1, "skill_points", 20, "🏆"),
        
        # PVP Achievements
        ("PVP Novice", "Complete 5 PVP matches", "pvp", 5, "experience", 150, "⚡"),
        ("PVP Expert", "Complete 25 PVP matches", "pvp", 25, "experience", 750, "⚔️"),
        ("PVP Master", "Complete 100 PVP matches", "pvp", 100, "skill_points", 15, "🎯"),
    ]
    
    conn = sqlite3.connect('idle_duelist.db')
    cursor = conn.cursor()
    
    for achievement in achievements:
        cursor.execute('''
            INSERT OR IGNORE INTO achievements 
            (name, description, category, requirement_value, reward_type, reward_value, icon)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', achievement)
    
    conn.commit()
    conn.close()
    print(f"✅ Initialized {len(achievements)} achievements")

if __name__ == "__main__":
    init_achievements()
