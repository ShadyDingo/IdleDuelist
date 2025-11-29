"""
Database manager that abstracts SQLite/PostgreSQL differences.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import Any, Optional, Sequence

from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Shared database connection helper."""

    def __init__(self) -> None:
        self.database_url = settings.database_url
        self.sqlite_path = settings.sqlite_path
        self.use_postgres = bool(
            self.database_url and self.database_url.startswith("postgres")
        )

    def get_connection(self):
        """Return a database connection, preferring PostgreSQL when configured."""
        if self.use_postgres:
            try:
                import psycopg2  # type: ignore
                from psycopg2.extras import RealDictCursor  # type: ignore

                class AutoConvertCursor(RealDictCursor):
                    def execute(self, query, vars=None):
                        if isinstance(query, str):
                            query = query.replace("?", "%s")
                        return super().execute(query, vars)

                conn = psycopg2.connect(self.database_url)
                conn.cursor_factory = AutoConvertCursor
                return conn
            except ImportError:
                logger.error("psycopg2 not installed, falling back to SQLite")
                # fallthrough to SQLite
            except Exception as exc:
                logger.error(
                    "Failed to connect to PostgreSQL: %s. Falling back to SQLite.", exc
                )
                # fallthrough to SQLite

        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_cursor(self, conn):
        """Return a cursor with placeholder-conversion for PostgreSQL."""
        cursor = conn.cursor()
        if self.use_postgres:
            original_execute = cursor.execute

            def wrapped_execute(query, params=None):
                if isinstance(query, str):
                    query = query.replace("?", "%s")
                return original_execute(query, params)

            cursor.execute = wrapped_execute  # type: ignore
        return cursor

    def execute(self, cursor, query: str, params: Optional[Sequence[Any]] = None):
        """Execute a query with placeholder conversion when needed."""
        params = params or ()
        if self.use_postgres and isinstance(query, str):
            query = query.replace("?", "%s")
        return cursor.execute(query, params)


db_manager = DatabaseManager()


def get_db_connection():
    return db_manager.get_connection()


def get_db_cursor(conn):
    return db_manager.get_cursor(conn)


def execute_query(cursor, query: str, params: Optional[Sequence[Any]] = None):
    return db_manager.execute(cursor, query, params)
