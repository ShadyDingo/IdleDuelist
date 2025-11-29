"""
Thread-safe in-memory state used when Redis is unavailable.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import RLock
from typing import Dict, Optional


@dataclass
class GameState:
    """Centralised shared game state with lightweight locking."""

    combat_states: Dict[str, dict] = field(default_factory=dict)
    pvp_queue: Dict[str, float] = field(default_factory=dict)
    auto_fight_sessions: Dict[str, dict] = field(default_factory=dict)
    active_sessions: Dict[str, dict] = field(default_factory=dict)
    _lock: RLock = field(default_factory=RLock, repr=False)

    def touch_session(self, user_id: str, ip_address: Optional[str] = None) -> None:
        """Record an active session heartbeat."""
        with self._lock:
            self.active_sessions[user_id] = {
                "last_seen": time.time(),
                "ip": ip_address,
            }

    def prune_sessions(self, ttl_seconds: int) -> None:
        """Remove stale active sessions."""
        threshold = time.time() - ttl_seconds
        with self._lock:
            stale = [
                user_id
                for user_id, session in self.active_sessions.items()
                if session.get("last_seen", 0) < threshold
            ]
            for user_id in stale:
                self.active_sessions.pop(user_id, None)


game_state = GameState()
