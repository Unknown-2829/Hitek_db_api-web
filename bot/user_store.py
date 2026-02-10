"""
User Data Persistence
Saves user IDs and banned list to disk as JSON.
"""

import json
import logging
from pathlib import Path
from typing import Set

from bot.config import USERS_FILE

logger = logging.getLogger(__name__)


class UserStore:
    """Persist user IDs and banned users to a JSON file on disk."""

    def __init__(self, filepath: str = USERS_FILE):
        self.filepath = Path(filepath)
        self.users: Set[int] = set()
        self.banned: Set[int] = set()
        self._load()

    def _load(self):
        """Load user data from disk."""
        if self.filepath.exists():
            try:
                with open(self.filepath, "r") as f:
                    data = json.load(f)
                self.users = set(data.get("users", []))
                self.banned = set(data.get("banned", []))
                logger.info(
                    f"Loaded {len(self.users)} users, "
                    f"{len(self.banned)} banned from {self.filepath}"
                )
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load user store: {e}")
                self.users = set()
                self.banned = set()
        else:
            logger.info("No user store found, starting fresh.")

    def _save(self):
        """Persist user data to disk."""
        try:
            data = {
                "users": list(self.users),
                "banned": list(self.banned),
            }
            with open(self.filepath, "w") as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save user store: {e}")

    def add_user(self, user_id: int):
        """Track a user who interacted with the bot."""
        if user_id not in self.users:
            self.users.add(user_id)
            self._save()

    def ban_user(self, user_id: int) -> bool:
        """Ban a user. Returns True if newly banned."""
        if user_id in self.banned:
            return False
        self.banned.add(user_id)
        self._save()
        return True

    def unban_user(self, user_id: int) -> bool:
        """Unban a user. Returns True if was banned."""
        if user_id not in self.banned:
            return False
        self.banned.discard(user_id)
        self._save()
        return True

    def get_all_users(self) -> Set[int]:
        return self.users.copy()

    def get_banned(self) -> Set[int]:
        return self.banned.copy()

    @property
    def user_count(self) -> int:
        return len(self.users)


# ── Singleton ──────────────────────────────────────────────────────
user_store = UserStore()
