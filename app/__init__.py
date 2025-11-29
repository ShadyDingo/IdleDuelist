"""
Application package initialisation for IdleDuelist.
Exposes shared configuration so modules can import `settings`
without causing circular dependencies.
"""

from .core.config import settings

__all__ = ["settings"]
