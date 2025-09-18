#!/usr/bin/env python3
"""
Initialize the first tournament for IdleDuelist
"""

import sqlite3
import json
from datetime import datetime, timedelta
import pytz

def get_db_connection():
    return sqlite3.connect('idle_duelist.db')

def init_first_tournament():
    """Create the first tournament"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if any tournaments exist
            cursor.execute('SELECT COUNT(*) FROM tournaments')
            count = cursor.fetchone()[0]
            
            if count > 0:
                print("✅ Tournaments already exist, skipping initialization")
                return
            
            # Get EST timezone
            est = pytz.timezone('US/Eastern')
            now = datetime.now(est)
            
            # Create tournament starting now and ending in 7 days
            start_date = now
            end_date = now + timedelta(days=7)
            
            tournament_name = f"Weekly Tournament - {start_date.strftime('%B %d, %Y')}"
            
            cursor.execute('''
                INSERT INTO tournaments (name, start_date, end_date, status, prize_pool)
                VALUES (?, ?, ?, 'active', 10000)
            ''', (tournament_name, start_date.isoformat(), end_date.isoformat()))
            
            conn.commit()
            print(f"✅ Created first tournament: {tournament_name}")
            print(f"   Start: {start_date.strftime('%Y-%m-%d %H:%M:%S EST')}")
            print(f"   End: {end_date.strftime('%Y-%m-%d %H:%M:%S EST')}")
            print(f"   Prize Pool: 10,000 Gold")
            
    except Exception as e:
        print(f"❌ Error creating tournament: {e}")

if __name__ == "__main__":
    print("🏆 Initializing IdleDuelist Tournament System")
    print("=" * 50)
    init_first_tournament()
    print("✅ Tournament initialization complete!")
