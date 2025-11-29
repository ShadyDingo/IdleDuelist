"""
Redis cache helpers with graceful in-memory fallback.
"""

from __future__ import annotations

import logging

from .config import settings


class RedisCache:
    """Lazily initialised Redis client with safe fallbacks."""

    def __init__(self) -> None:
        self._client = None
        self._logger = logging.getLogger(__name__)

    def get_client(self):
        """Return a Redis client if configured and reachable."""
        if self._client is not None:
            return self._client

        if not settings.redis_url:
            return None

        try:
            import redis  # type: ignore
        except ImportError:
            self._logger.warning(
                "redis package not installed; defaulting to in-memory state store"
            )
            return None

        try:
            self._client = redis.from_url(
                settings.redis_url, decode_responses=True, retry_on_timeout=True
            )
            self._client.ping()
            return self._client
        except Exception as exc:  # pragma: no cover - depends on env setup
            self._logger.warning(
                "Unable to connect to Redis (%s); using in-memory store", exc
            )
            self._client = None
            return None


redis_cache = RedisCache()
