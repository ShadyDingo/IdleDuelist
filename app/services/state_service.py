"""
State storage helpers that transparently switch between Redis and in-memory.
"""

from __future__ import annotations

import json
from typing import Dict, Optional

from app.core.cache import redis_cache
from app.core.config import settings
from app.core.state import game_state


class StateService:
    """Wrapper around combat state, PvP queue, and auto fight sessions."""

    def __init__(self) -> None:
        self._namespace = settings.redis_namespace

    def _client(self):
        return redis_cache.get_client()

    def _key(self, bucket: str, identifier: str) -> str:
        return f"{self._namespace}:{bucket}:{identifier}"

    # Combat state -----------------------------------------------------------------
    def get_combat_state(self, combat_id: str) -> Optional[Dict]:
        client = self._client()
        if client:
            data = client.get(self._key("combat", combat_id))
            return json.loads(data) if data else None
        return game_state.combat_states.get(combat_id)

    def set_combat_state(self, combat_id: str, state: Dict) -> None:
        client = self._client()
        if client:
            client.setex(
                self._key("combat", combat_id),
                settings.combat_state_ttl,
                json.dumps(state),
            )
        else:
            game_state.combat_states[combat_id] = state

    def delete_combat_state(self, combat_id: str) -> None:
        client = self._client()
        if client:
            client.delete(self._key("combat", combat_id))
        else:
            game_state.combat_states.pop(combat_id, None)

    # PvP queue --------------------------------------------------------------------
    def get_pvp_queue_entry(self, character_id: str) -> Optional[str]:
        client = self._client()
        if client:
            return client.get(self._key("pvp_queue", character_id))
        return game_state.pvp_queue.get(character_id)

    def set_pvp_queue_entry(self, character_id: str, timestamp: str) -> None:
        client = self._client()
        if client:
            client.setex(
                self._key("pvp_queue", character_id),
                settings.pvp_queue_ttl,
                timestamp,
            )
        else:
            game_state.pvp_queue[character_id] = timestamp

    def delete_pvp_queue_entry(self, character_id: str) -> None:
        client = self._client()
        if client:
            client.delete(self._key("pvp_queue", character_id))
        else:
            game_state.pvp_queue.pop(character_id, None)

    def get_all_pvp_queue(self) -> Dict[str, str]:
        client = self._client()
        if client:
            entries: Dict[str, str] = {}
            pattern = self._key("pvp_queue", "*")
            for key in client.keys(pattern):
                character_id = key.split(":")[-1]
                timestamp = client.get(key)
                if timestamp:
                    entries[character_id] = timestamp
            return entries
        return game_state.pvp_queue.copy()

    # Auto fight sessions ----------------------------------------------------------
    def get_auto_fight_session(self, session_id: str) -> Optional[Dict]:
        client = self._client()
        if client:
            data = client.get(self._key("autofight", session_id))
            return json.loads(data) if data else None
        return game_state.auto_fight_sessions.get(session_id)

    def set_auto_fight_session(self, session_id: str, session: Dict) -> None:
        client = self._client()
        if client:
            client.setex(
                self._key("autofight", session_id),
                settings.auto_fight_ttl,
                json.dumps(session),
            )
        else:
            game_state.auto_fight_sessions[session_id] = session

    def delete_auto_fight_session(self, session_id: str) -> None:
        client = self._client()
        if client:
            client.delete(self._key("autofight", session_id))
        else:
            game_state.auto_fight_sessions.pop(session_id, None)

    def get_all_auto_fight_sessions(self) -> Dict[str, Dict]:
        client = self._client()
        if client:
            sessions: Dict[str, Dict] = {}
            pattern = self._key("autofight", "*")
            for key in client.keys(pattern):
                session_id = key.split(":")[-1]
                data = client.get(key)
                if data:
                    sessions[session_id] = json.loads(data)
            return sessions
        return game_state.auto_fight_sessions.copy()


state_service = StateService()

# Re-export helper functions for backwards compatibility
get_combat_state = state_service.get_combat_state
set_combat_state = state_service.set_combat_state
delete_combat_state = state_service.delete_combat_state

get_pvp_queue_entry = state_service.get_pvp_queue_entry
set_pvp_queue_entry = state_service.set_pvp_queue_entry
delete_pvp_queue_entry = state_service.delete_pvp_queue_entry

get_auto_fight_session = state_service.get_auto_fight_session
set_auto_fight_session = state_service.set_auto_fight_session
delete_auto_fight_session = state_service.delete_auto_fight_session
get_all_auto_fight_sessions = state_service.get_all_auto_fight_sessions
get_all_pvp_queue = state_service.get_all_pvp_queue
