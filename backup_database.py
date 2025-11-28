#!/usr/bin/env python3
"""
Database backup script for IdleDuelist
Supports both SQLite and PostgreSQL backup
"""
import os
import sys
import json
import subprocess
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backup_postgresql(database_url: str, backup_dir: str = "backups"):
    """Backup PostgreSQL database using pg_dump"""
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"idleduelist_backup_{timestamp}.sql")
    
    try:
        # Extract connection details from DATABASE_URL
        # Format: postgresql://user:password@host:port/database
        import re
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
        if not match:
            logger.error("Invalid DATABASE_URL format")
            return False
        
        user, password, host, port, database = match.groups()
        
        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = password
        
        # Run pg_dump
        cmd = [
            'pg_dump',
            '-h', host,
            '-p', port,
            '-U', user,
            '-d', database,
            '-F', 'c',  # Custom format (compressed)
            '-f', backup_file
        ]
        
        logger.info(f"Backing up PostgreSQL database to {backup_file}")
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✓ Backup successful: {backup_file}")
            return backup_file
        else:
            logger.error(f"Backup failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error backing up PostgreSQL: {e}")
        return False

def backup_sqlite(database_file: str, backup_dir: str = "backups"):
    """Backup SQLite database by copying the file"""
    if not os.path.exists(database_file):
        logger.warning(f"Database file {database_file} not found")
        return False
    
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"idleduelist_backup_{timestamp}.db")
    
    try:
        import shutil
        logger.info(f"Backing up SQLite database to {backup_file}")
        shutil.copy2(database_file, backup_file)
        logger.info(f"✓ Backup successful: {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"Error backing up SQLite: {e}")
        return False

def cleanup_old_backups(backup_dir: str = "backups", keep_days: int = 7):
    """Remove backups older than keep_days"""
    if not os.path.exists(backup_dir):
        return
    
    import time
    cutoff_time = time.time() - (keep_days * 24 * 60 * 60)
    
    for filename in os.listdir(backup_dir):
        filepath = os.path.join(backup_dir, filename)
        if os.path.isfile(filepath):
            if os.path.getmtime(filepath) < cutoff_time:
                try:
                    os.remove(filepath)
                    logger.info(f"Removed old backup: {filename}")
                except Exception as e:
                    logger.warning(f"Failed to remove old backup {filename}: {e}")

def main():
    """Main backup function"""
    database_url = os.getenv("DATABASE_URL")
    
    if database_url and database_url.startswith("postgresql"):
        # PostgreSQL backup
        backup_file = backup_postgresql(database_url)
    else:
        # SQLite backup
        database_file = os.getenv("DATABASE", "idleduelist.db")
        backup_file = backup_sqlite(database_file)
    
    if backup_file:
        # Cleanup old backups (keep last 7 days)
        cleanup_old_backups(keep_days=7)
        logger.info("Backup process completed")
        return 0
    else:
        logger.error("Backup process failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

