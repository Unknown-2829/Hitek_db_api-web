"""
Bot Configuration
Priority: .env file > config.json > hardcoded defaults.
"""

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# ── Locate project root ───────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent

# ── Step 1: Try loading .env ───────────────────────────────────────
ENV_PATH = ROOT_DIR / ".env"
_env_loaded = False
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
    _env_loaded = True

# ── Step 2: Load config.json as fallback ───────────────────────────
CONFIG_JSON_PATH = ROOT_DIR / "config.json"
_json_config: dict = {}
if CONFIG_JSON_PATH.exists():
    try:
        with open(CONFIG_JSON_PATH, "r") as f:
            _json_config = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load config.json: {e}")


def _get(key: str, default: str = "") -> str:
    """Get config value: env var > config.json > default."""
    val = os.getenv(key)
    if val is not None:
        return val
    if key in _json_config:
        return str(_json_config[key])
    return default


# ── Bot Settings ───────────────────────────────────────────────────
BOT_TOKEN: str = _get("BOT_TOKEN", "")

# Admin Telegram user IDs (comma-separated)
_admin_raw = _get("ADMIN_IDS", "")
ADMIN_IDS: set[int] = set()
if _admin_raw:
    for _id in _admin_raw.split(","):
        _id = _id.strip()
        if _id.isdigit():
            ADMIN_IDS.add(int(_id))

# ── Database ───────────────────────────────────────────────────────
DB_PATH: str = _get("DB_PATH", "/data/users.db")

# ── Rate Limiting ──────────────────────────────────────────────────
RATE_LIMIT: int = int(_get("RATE_LIMIT", "2"))

# ── Bot Mode: "private" or "public" ───────────────────────────────
BOT_MODE: str = _get("BOT_MODE", "private")

# ── Logging ────────────────────────────────────────────────────────
LOG_FILE: str = _get("LOG_FILE", "search_history.log")

# ── Persistence ────────────────────────────────────────────────────
USERS_FILE: str = _get("USERS_FILE", "users_data.json")

# ── Search limits ──────────────────────────────────────────────────
MAX_RESULTS: int = int(_get("MAX_RESULTS", "25"))

# ── DB Retry ───────────────────────────────────────────────────────
DB_RETRY_ATTEMPTS: int = 3
DB_RETRY_DELAY: float = 0.5  # seconds, doubles each retry


def validate_config() -> list[str]:
    """Validate critical config values. Returns list of errors."""
    errors = []
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
        src = ".env" if _env_loaded else "config.json"
        errors.append(f"BOT_TOKEN is not set. Set it in {src} or environment variables.")
    if not ADMIN_IDS:
        errors.append("ADMIN_IDS is empty. Set at least one admin ID.")
    if not Path(DB_PATH).exists():
        errors.append(f"Database not found at: {DB_PATH}")
    return errors
