"""
Async SQLite Database Manager
Handles all DB operations with retry logic for locked/busy database.
Optimized for 1.78B row dataset.
"""

import asyncio
import logging
import sqlite3
from functools import wraps
from typing import Any

import aiosqlite

from bot.config import DB_PATH, DB_RETRY_ATTEMPTS, DB_RETRY_DELAY, MAX_RESULTS

logger = logging.getLogger(__name__)


def retry_on_lock(func):
    """Decorator: retry query on sqlite3.OperationalError (database locked)."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        delay = DB_RETRY_DELAY
        for attempt in range(1, DB_RETRY_ATTEMPTS + 1):
            try:
                return await func(*args, **kwargs)
            except (sqlite3.OperationalError, aiosqlite.OperationalError) as e:
                if "locked" in str(e).lower() or "busy" in str(e).lower():
                    logger.warning(
                        f"DB locked (attempt {attempt}/{DB_RETRY_ATTEMPTS}), "
                        f"retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                    delay *= 2  # exponential backoff
                else:
                    raise
        # Final attempt — let it raise
        return await func(*args, **kwargs)
    return wrapper


class DatabaseManager:
    """Async SQLite connection manager for the users database."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self):
        """Open a persistent connection with optimized settings."""
        logger.info(f"Connecting to database: {self.db_path}")
        self._conn = await aiosqlite.connect(self.db_path, timeout=30)
        self._conn.row_factory = aiosqlite.Row

        # ── Performance optimizations for read-heavy 1.78B row DB ──
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.execute("PRAGMA busy_timeout=10000;")
        await self._conn.execute("PRAGMA cache_size=-64000;")   # 64MB cache
        await self._conn.execute("PRAGMA mmap_size=2147483648;")  # 2GB mmap
        await self._conn.execute("PRAGMA temp_store=MEMORY;")
        await self._conn.execute("PRAGMA query_only=ON;")  # read-only safety

        logger.info("Database connected with WAL mode and optimized settings.")

    async def close(self):
        """Close the database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None
            logger.info("Database connection closed.")

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._conn

    # ── Search Methods ─────────────────────────────────────────────

    @retry_on_lock
    async def search_by_mobile(self, mobile: str) -> list[dict[str, Any]]:
        """Exact match on indexed mobile column — O(log n), very fast."""
        query = "SELECT * FROM users WHERE mobile = ? LIMIT ?"
        async with self.conn.execute(query, (mobile, MAX_RESULTS)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    @retry_on_lock
    async def search_by_name(self, name: str) -> list[dict[str, Any]]:
        """LIKE search on name — full scan, limited results."""
        query = "SELECT * FROM users WHERE name LIKE ? LIMIT ?"
        async with self.conn.execute(query, (f"%{name}%", MAX_RESULTS)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    @retry_on_lock
    async def search_by_email(self, email: str) -> list[dict[str, Any]]:
        """LIKE search on email — full scan, limited results."""
        query = "SELECT * FROM users WHERE email LIKE ? LIMIT ?"
        async with self.conn.execute(query, (f"%{email}%", MAX_RESULTS)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    @retry_on_lock
    async def search_by_address(self, address: str) -> list[dict[str, Any]]:
        """LIKE search on address — full scan, limited results."""
        query = "SELECT * FROM users WHERE address LIKE ? LIMIT ?"
        async with self.conn.execute(query, (f"%{address}%", MAX_RESULTS)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    @retry_on_lock
    async def search_by_fname(self, fname: str) -> list[dict[str, Any]]:
        """LIKE search on father's name."""
        query = "SELECT * FROM users WHERE fname LIKE ? LIMIT ?"
        async with self.conn.execute(query, (f"%{fname}%", MAX_RESULTS)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    @retry_on_lock
    async def get_row_count(self) -> int:
        """Get approximate row count (fast for large tables)."""
        # Use max(rowid) as approximation — much faster than COUNT(*)
        query = "SELECT MAX(rowid) FROM users"
        async with self.conn.execute(query) as cursor:
            row = await cursor.fetchone()
            return row[0] if row and row[0] else 0

    @retry_on_lock
    async def get_db_size(self) -> int:
        """Get database page count * page size = file size in bytes."""
        async with self.conn.execute("PRAGMA page_count") as c1:
            page_count = (await c1.fetchone())[0]
        async with self.conn.execute("PRAGMA page_size") as c2:
            page_size = (await c2.fetchone())[0]
        return page_count * page_size


# ── Singleton instance ─────────────────────────────────────────────
db = DatabaseManager()
