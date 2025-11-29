"""
Centralised configuration for IdleDuelist.
Uses Pydantic settings so deployment targets (Fly.io, local, CI)
share a single source of truth for environment variables.
"""

from __future__ import annotations

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    environment: str = Field(default="development", alias="ENVIRONMENT")
    sqlite_path: str = Field(default="idleduelist.db", alias="SQLITE_PATH")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    redis_namespace: str = Field(default="idleduelist", alias="REDIS_NAMESPACE")
    cors_origins: str | None = Field(default=None, alias="CORS_ORIGINS")

    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production-min-32-chars",
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_hours: int = Field(default=24, alias="ACCESS_TOKEN_EXPIRE_HOURS")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    mmr_k_factor: int = Field(default=32, alias="MMR_K_FACTOR")
    base_mmr: int = Field(default=1000, alias="MMR_BASE")
    mmr_floor: int = Field(default=0, alias="MMR_FLOOR")

    combat_state_ttl: int = Field(default=3600, alias="COMBAT_STATE_TTL")
    auto_fight_ttl: int = Field(default=7200, alias="AUTO_FIGHT_TTL")
    pvp_queue_ttl: int = Field(default=300, alias="PVP_QUEUE_TTL")
    active_session_ttl: int = Field(default=900, alias="ACTIVE_SESSION_TTL")

    log_file: str = Field(default="idleduelist.log", alias="LOG_FILE")
    telemetry_sample_rate: float = Field(default=1.0, alias="TELEMETRY_SAMPLE_RATE")

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        """Return parsed CORS origins respecting production requirements."""
        if self.cors_origins:
            return [
                origin.strip()
                for origin in self.cors_origins.split(",")
                if origin.strip()
            ]
        # Default to wildcard only for non-production
        return [] if self.is_production else ["*"]


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance to avoid repeated environment parsing."""
    return Settings()


settings = get_settings()
