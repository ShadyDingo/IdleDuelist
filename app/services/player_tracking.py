"""
Player tracking, progress logging, and matchmaking analytics helpers.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from app.db import execute_query, get_db_connection
from app.db.manager import db_manager

logger = logging.getLogger(__name__)


class PlayerTrackingService:
    """High-level persistence helpers for online features."""

    def __init__(self) -> None:
        self.use_postgres = db_manager.use_postgres
        self.logger = logging.getLogger(self.__class__.__name__)

    def _ensure_profile_from_users(self, user_id: str) -> None:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT username, email FROM users WHERE id = ?", (user_id,)
            )
            user = cursor.fetchone()
        finally:
            conn.close()

        if user:
            email = user["email"] if "email" in user.keys() else None
            self.ensure_profile(user_id, user["username"], email)

    # ------------------------------------------------------------------
    # Profiles / sessions
    def ensure_profile(self, user_id: str, username: str, email: Optional[str]) -> None:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if self.use_postgres:
                cursor.execute(
                    """
                    INSERT INTO player_profiles (user_id, username, email)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id) DO NOTHING
                    """,
                    (user_id, username, email),
                )
            else:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO player_profiles (user_id, username, email)
                    VALUES (?, ?, ?)
                    """,
                    (user_id, username, email),
                )
            conn.commit()
        finally:
            conn.close()

    def record_login(
        self, user_id: str, username: str, ip_address: Optional[str]
    ) -> None:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow()
        session_id = str(uuid.uuid4())

        try:
            self.ensure_profile(user_id, username, None)
            execute_query(
                cursor,
                """
                UPDATE player_profiles 
                SET last_login = ?, total_sessions = total_sessions + 1, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (now, user_id),
            )

            if self.use_postgres:
                cursor.execute(
                    """
                    INSERT INTO player_sessions (user_id, session_id, last_seen, last_ip)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE 
                    SET session_id = EXCLUDED.session_id,
                        last_seen = EXCLUDED.last_seen,
                        last_ip = EXCLUDED.last_ip
                    """,
                    (user_id, session_id, now, ip_address),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO player_sessions (user_id, session_id, last_seen, last_ip)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        session_id=excluded.session_id,
                        last_seen=excluded.last_seen,
                        last_ip=excluded.last_ip
                    """,
                    (user_id, session_id, now, ip_address),
                )
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Progress logging
    def record_progress(
        self,
        *,
        character_id: str,
        user_id: str,
        level: int,
        exp_gain: int,
        gold_gain: int,
        event_type: str = "combat_reward",
        metadata: Optional[Dict] = None,
    ) -> None:
        payload = {
            "level": level,
            "exp_gain": exp_gain,
            "gold_gain": gold_gain,
        }
        if metadata:
            payload.update(metadata)

        conn = get_db_connection()
        cursor = conn.cursor()
        log_id = str(uuid.uuid4())

        try:
            execute_query(
                cursor,
                """
                INSERT INTO player_progress_log (id, character_id, user_id, event_type, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (log_id, character_id, user_id, event_type, json.dumps(payload)),
            )

            execute_query(
                cursor,
                """
                UPDATE player_profiles SET
                    lifetime_exp = lifetime_exp + ?,
                    lifetime_gold = lifetime_gold + ?,
                    total_pve_fights = total_pve_fights + CASE WHEN ? = 'combat_reward' THEN 1 ELSE 0 END,
                    highest_level = CASE WHEN highest_level < ? THEN ? ELSE highest_level END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (exp_gain, gold_gain, event_type, level, level, user_id),
            )
            if cursor.rowcount == 0:
                self._ensure_profile_from_users(user_id)
                execute_query(
                    cursor,
                    """
                    UPDATE player_profiles SET
                        lifetime_exp = lifetime_exp + ?,
                        lifetime_gold = lifetime_gold + ?,
                        total_pve_fights = total_pve_fights + CASE WHEN ? = 'combat_reward' THEN 1 ELSE 0 END,
                        highest_level = CASE WHEN highest_level < ? THEN ? ELSE highest_level END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (exp_gain, gold_gain, event_type, level, level, user_id),
                )
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # PvP logging
    def record_pvp_result(
        self,
        *,
        winner_character_id: str,
        loser_character_id: str,
        winner_user_id: str,
        loser_user_id: str,
        winner_mmr_before: int,
        winner_mmr_after: int,
        loser_mmr_before: int,
        loser_mmr_after: int,
        duration_seconds: Optional[int] = None,
        metadata: Optional[Dict] = None,
    ) -> None:
        match_id = str(uuid.uuid4())
        payload = metadata or {}

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            execute_query(
                cursor,
                """
                INSERT INTO pvp_matches (
                    id, winner_character_id, loser_character_id,
                    winner_user_id, loser_user_id,
                    winner_mmr_before, winner_mmr_after,
                    loser_mmr_before, loser_mmr_after,
                    duration_seconds, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    match_id,
                    winner_character_id,
                    loser_character_id,
                    winner_user_id,
                    loser_user_id,
                    winner_mmr_before,
                    winner_mmr_after,
                    loser_mmr_before,
                    loser_mmr_after,
                    duration_seconds,
                    json.dumps(payload),
                ),
            )

            execute_query(
                cursor,
                """
                UPDATE player_profiles SET
                    total_matches = total_matches + 1,
                    total_wins = total_wins + 1,
                    total_pvp_fights = total_pvp_fights + 1,
                    current_mmr = ?,
                    best_mmr = CASE WHEN best_mmr < ? THEN ? ELSE best_mmr END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (winner_mmr_after, winner_mmr_after, winner_mmr_after, winner_user_id),
            )
            if cursor.rowcount == 0:
                self._ensure_profile_from_users(winner_user_id)
                execute_query(
                    cursor,
                    """
                    UPDATE player_profiles SET
                        total_matches = total_matches + 1,
                        total_wins = total_wins + 1,
                        total_pvp_fights = total_pvp_fights + 1,
                        current_mmr = ?,
                        best_mmr = CASE WHEN best_mmr < ? THEN ? ELSE best_mmr END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (
                        winner_mmr_after,
                        winner_mmr_after,
                        winner_mmr_after,
                        winner_user_id,
                    ),
                )
            execute_query(
                cursor,
                """
                UPDATE player_profiles SET
                    total_matches = total_matches + 1,
                    total_losses = total_losses + 1,
                    total_pvp_fights = total_pvp_fights + 1,
                    current_mmr = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (loser_mmr_after, loser_user_id),
            )
            if cursor.rowcount == 0:
                self._ensure_profile_from_users(loser_user_id)
                execute_query(
                    cursor,
                    """
                    UPDATE player_profiles SET
                        total_matches = total_matches + 1,
                        total_losses = total_losses + 1,
                        total_pvp_fights = total_pvp_fights + 1,
                        current_mmr = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (loser_mmr_after, loser_user_id),
                )

            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Queries
    def get_profile(self, user_id: str) -> Dict:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT * FROM player_profiles WHERE user_id = ?", (user_id,)
            )
            row = cursor.fetchone()
            profile = dict(row) if row else {}

            cursor.execute(
                """
                SELECT id, name, level, pvp_mmr, pvp_wins, pvp_losses, gold, exp
                FROM characters
                WHERE user_id = ?
                ORDER BY level DESC, name ASC
                """,
                (user_id,),
            )
            characters = [dict(char) for char in cursor.fetchall()]

            return {"profile": profile, "characters": characters}
        finally:
            conn.close()

    def get_recent_progress(self, character_id: str, limit: int = 20) -> List[Dict]:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT event_type, payload_json, created_at
                FROM player_progress_log
                WHERE character_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (character_id, limit),
            )
            entries = []
            for row in cursor.fetchall():
                payload = json.loads(row["payload_json"])
                entries.append(
                    {
                        "event_type": row["event_type"],
                        "payload": payload,
                        "created_at": row["created_at"],
                    }
                )
            return entries
        finally:
            conn.close()

    def get_recent_matches(self, user_id: str, limit: int = 20) -> List[Dict]:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT *
                FROM pvp_matches
                WHERE winner_user_id = ? OR loser_user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, user_id, limit),
            )
            matches = []
            for row in cursor.fetchall():
                record = dict(row)
                record["result"] = (
                    "win" if row["winner_user_id"] == user_id else "loss"
                )
                if record.get("metadata_json"):
                    record["metadata"] = json.loads(record.pop("metadata_json"))
                matches.append(record)
            return matches
        finally:
            conn.close()

    def get_leaderboard(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT c.id, c.name, c.level, 
                       COALESCE(c.pvp_mmr, ?) AS mmr,
                       COALESCE(c.pvp_wins, 0) AS wins,
                       COALESCE(c.pvp_losses, 0) AS losses,
                       COALESCE(pp.username, '') AS username,
                       COALESCE(pp.best_mmr, ?) AS best_mmr
                FROM characters c
                LEFT JOIN player_profiles pp ON pp.user_id = c.user_id
                ORDER BY mmr DESC, wins DESC, c.level DESC
                LIMIT ? OFFSET ?
                """,
                (1000, 1000, limit, offset),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()


player_tracking_service = PlayerTrackingService()
