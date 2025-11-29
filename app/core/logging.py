"""
Logging helpers for IdleDuelist.
Ensures consistent formatting and file rotation between dev/prod.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import Settings


def configure_logging(settings: Settings) -> logging.Logger:
    """Configure logging handlers based on current environment."""
    log_level = logging.INFO if settings.is_production else logging.DEBUG

    handlers: list[logging.Handler] = []
    if settings.is_production:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                log_path,
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
        )
    else:
        handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )

    return logging.getLogger("idleduelist")
