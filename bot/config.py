"""
Bot Configuration
Loads settings from .env file, falls back to hardcoded defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Try loading .env file ──────────────────────────────────────────
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

# ── Bot Settings ───────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# Admin Telegram user IDs (comma-separated in .env)
_admin_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: set[int] = set()
if _admin_raw:
    for _id in _admin_raw.split(","):
        _id = _id.strip()
        if _id.isdigit():
            ADMIN_IDS.add(int(_id))

# ── Database ───────────────────────────────────────────────────────
DB_PATH: str = os.getenv("DB_PATH", "/data/users.db")

# ── Rate Limiting ──────────────────────────────────────────────────
RATE_LIMIT: int = int(os.getenv("RATE_LIMIT", "2"))

# ── Bot Mode: "private" or "public" ───────────────────────────────
BOT_MODE: str = os.getenv("BOT_MODE", "private")

# ── Logging ────────────────────────────────────────────────────────
LOG_FILE: str = os.getenv("LOG_FILE", "search_history.log")

# ── Persistence ────────────────────────────────────────────────────
USERS_FILE: str = os.getenv("USERS_FILE", "users_data.json")

# ── Search limits ──────────────────────────────────────────────────
MAX_RESULTS: int = int(os.getenv("MAX_RESULTS", "25"))

# ── DB Retry ───────────────────────────────────────────────────────
DB_RETRY_ATTEMPTS: int = 3
DB_RETRY_DELAY: float = 0.5  # seconds, doubles each retry


def validate_config() -> list[str]:
    """Validate critical config values. Returns list of errors."""
    errors = []
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN is not set. Set it in .env or environment variables.")
    if not ADMIN_IDS:
        errors.append("ADMIN_IDS is empty. Set at least one admin ID.")
    if not Path(DB_PATH).exists():
        errors.append(f"Database not found at: {DB_PATH}")
    return errors
