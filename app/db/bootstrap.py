"""
Bootstrap helpers for advanced persistence tables (player tracking/MMR).
"""

from __future__ import annotations


def ensure_player_tracking_tables(conn, cursor, use_postgres: bool) -> None:
    """Create player tracking related tables if they do not exist."""
    if use_postgres:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS player_profiles (
                user_id VARCHAR(255) PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255),
                last_login TIMESTAMP,
                total_sessions INTEGER DEFAULT 0,
                total_matches INTEGER DEFAULT 0,
                total_wins INTEGER DEFAULT 0,
                total_losses INTEGER DEFAULT 0,
                total_pve_fights INTEGER DEFAULT 0,
                total_pvp_fights INTEGER DEFAULT 0,
                lifetime_exp BIGINT DEFAULT 0,
                lifetime_gold BIGINT DEFAULT 0,
                highest_level INTEGER DEFAULT 1,
                current_mmr INTEGER DEFAULT 1000,
                best_mmr INTEGER DEFAULT 1000,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS player_sessions (
                user_id VARCHAR(255) PRIMARY KEY,
                session_id VARCHAR(255),
                last_seen TIMESTAMP NOT NULL,
                last_ip VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS player_progress_log (
                id VARCHAR(255) PRIMARY KEY,
                character_id VARCHAR(255) NOT NULL,
                user_id VARCHAR(255) NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pvp_matches (
                id VARCHAR(255) PRIMARY KEY,
                winner_character_id VARCHAR(255) NOT NULL,
                loser_character_id VARCHAR(255) NOT NULL,
                winner_user_id VARCHAR(255) NOT NULL,
                loser_user_id VARCHAR(255) NOT NULL,
                winner_mmr_before INTEGER,
                winner_mmr_after INTEGER,
                loser_mmr_before INTEGER,
                loser_mmr_after INTEGER,
                duration_seconds INTEGER,
                metadata_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (winner_character_id) REFERENCES characters (id),
                FOREIGN KEY (loser_character_id) REFERENCES characters (id)
            )
            """
        )
    else:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS player_profiles (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                last_login TIMESTAMP,
                total_sessions INTEGER DEFAULT 0,
                total_matches INTEGER DEFAULT 0,
                total_wins INTEGER DEFAULT 0,
                total_losses INTEGER DEFAULT 0,
                total_pve_fights INTEGER DEFAULT 0,
                total_pvp_fights INTEGER DEFAULT 0,
                lifetime_exp INTEGER DEFAULT 0,
                lifetime_gold INTEGER DEFAULT 0,
                highest_level INTEGER DEFAULT 1,
                current_mmr INTEGER DEFAULT 1000,
                best_mmr INTEGER DEFAULT 1000,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS player_sessions (
                user_id TEXT PRIMARY KEY,
                session_id TEXT,
                last_seen TIMESTAMP NOT NULL,
                last_ip TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS player_progress_log (
                id TEXT PRIMARY KEY,
                character_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pvp_matches (
                id TEXT PRIMARY KEY,
                winner_character_id TEXT NOT NULL,
                loser_character_id TEXT NOT NULL,
                winner_user_id TEXT NOT NULL,
                loser_user_id TEXT NOT NULL,
                winner_mmr_before INTEGER,
                winner_mmr_after INTEGER,
                loser_mmr_before INTEGER,
                loser_mmr_after INTEGER,
                duration_seconds INTEGER,
                metadata_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (winner_character_id) REFERENCES characters (id),
                FOREIGN KEY (loser_character_id) REFERENCES characters (id)
            )
            """
        )

    # Helpful indexes
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_player_progress_character ON player_progress_log (character_id, created_at DESC)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_pvp_matches_winner ON pvp_matches (winner_user_id, created_at DESC)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_pvp_matches_loser ON pvp_matches (loser_user_id, created_at DESC)"
    )

    conn.commit()
