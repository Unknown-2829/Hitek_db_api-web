"""
Async SQLite Database Manager
Optimized for 1.78B row dataset with deep-link search.
Only uses indexed mobile column for all queries.
"""

import asyncio
import logging
import sqlite3
from functools import wraps
from typing import Any

import aiosqlite

from api.config import DB_PATH, DB_RETRY_ATTEMPTS, DB_RETRY_DELAY, MAX_RESULTS, DEEP_SEARCH_DEPTH

logger = logging.getLogger(__name__)


def retry_on_lock(func):
    """Retry on sqlite3.OperationalError (database locked)."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        delay = DB_RETRY_DELAY
        for attempt in range(1, DB_RETRY_ATTEMPTS + 1):
            try:
                return await func(*args, **kwargs)
            except (sqlite3.OperationalError, aiosqlite.OperationalError) as e:
                if "locked" in str(e).lower() or "busy" in str(e).lower():
                    logger.warning(f"DB locked (attempt {attempt}), retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    raise
        return await func(*args, **kwargs)
    return wrapper


class DatabaseManager:
    """Async SQLite manager with deep-link search."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self):
        """Open connection with optimized settings."""
        logger.info(f"Connecting to database: {self.db_path}")
        self._conn = await aiosqlite.connect(self.db_path, timeout=30)
        self._conn.row_factory = aiosqlite.Row

        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.execute("PRAGMA busy_timeout=10000;")
        await self._conn.execute("PRAGMA cache_size=-64000;")
        await self._conn.execute("PRAGMA mmap_size=2147483648;")
        await self._conn.execute("PRAGMA temp_store=MEMORY;")
        await self._conn.execute("PRAGMA query_only=ON;")

        logger.info("Database connected with WAL mode.")

    async def close(self):
        if self._conn:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database not connected.")
        return self._conn

    @retry_on_lock
    async def search_by_mobile(self, mobile: str) -> list[dict[str, Any]]:
        """Exact match on indexed mobile column — O(log n)."""
        query = "SELECT * FROM users WHERE mobile = ? LIMIT ?"
        async with self.conn.execute(query, (mobile, MAX_RESULTS)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def deep_search(self, seed_mobile: str) -> dict[str, Any]:
        """
        BFS deep-link: search mobile (indexed), extract alt_mobile,
        search alt values in mobile column. Up to DEEP_SEARCH_DEPTH levels.
        """
        visited: set[str] = set()
        queue: list[str] = [seed_mobile]
        all_rows: list[dict[str, Any]] = []
        seen_keys: set[int] = set()

        depth = 0
        while queue and depth < DEEP_SEARCH_DEPTH:
            next_queue: list[str] = []

            for number in queue:
                if number in visited:
                    continue
                visited.add(number)

                rows = await self.search_by_mobile(number)

                for row in rows:
                    row_key = hash((
                        row.get("mobile", ""),
                        row.get("name", ""),
                        row.get("fname", ""),
                        row.get("address", ""),
                    ))
                    if row_key in seen_keys:
                        continue
                    seen_keys.add(row_key)
                    all_rows.append(row)

                    alt = str(row.get("alt_mobile", "")).strip()
                    if alt and alt not in ("None", "N/A", ""):
                        alt_digits = alt[-10:] if len(alt) > 10 else alt
                        if (
                            len(alt_digits) == 10
                            and alt_digits[0] in "6789"
                            and alt_digits not in visited
                        ):
                            next_queue.append(alt_digits)

            queue = next_queue
            depth += 1

        return self._build_profile(seed_mobile, all_rows)

    def _build_profile(self, seed: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
        """Consolidate rows into JSON profile."""
        phones, addresses, names, fnames, emails, circles = [], [], [], [], [], []
        seen_p, seen_a, seen_n, seen_fn, seen_e, seen_c = set(), set(), set(), set(), set(), set()

        for row in rows:
            mob = str(row.get("mobile", "")).strip()
            alt = str(row.get("alt_mobile", "")).strip()
            if mob and mob not in seen_p:
                seen_p.add(mob)
                phones.append(mob)
            if alt and alt not in seen_p and alt not in ("None", "N/A"):
                seen_p.add(alt)
                phones.append(alt)

            name = str(row.get("name", "")).strip()
            if name and name not in seen_n and name != "None":
                seen_n.add(name)
                names.append(name)

            fname = str(row.get("fname", "")).strip()
            if fname and fname not in seen_fn and fname != "None":
                seen_fn.add(fname)
                fnames.append(fname)

            email = str(row.get("email", "")).strip()
            if email and email not in seen_e and email not in ("None", "N/A", ""):
                seen_e.add(email)
                emails.append(email)

            addr = str(row.get("address", "")).strip()
            if addr and addr not in seen_a and addr != "None":
                seen_a.add(addr)
                addresses.append(addr)

            circle = str(row.get("circle", "")).strip()
            if circle and circle not in seen_c and circle != "None":
                seen_c.add(circle)
                circles.append(circle)

        return {
            "query": seed,
            "found": len(rows) > 0,
            "total_records": len(rows),
            "total_phones": len(phones),
            "phones": phones,
            "names": names,
            "father_names": fnames,
            "emails": emails,
            "addresses": addresses,
            "regions": circles,
        }

    @retry_on_lock
    async def get_row_count(self) -> int:
        query = "SELECT MAX(rowid) FROM users"
        async with self.conn.execute(query) as cursor:
            row = await cursor.fetchone()
            return row[0] if row and row[0] else 0

    @retry_on_lock
    async def get_db_size(self) -> int:
        async with self.conn.execute("PRAGMA page_count") as c1:
            page_count = (await c1.fetchone())[0]
        async with self.conn.execute("PRAGMA page_size") as c2:
            page_size = (await c2.fetchone())[0]
        return page_count * page_size


db = DatabaseManager()
