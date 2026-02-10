"""
Bot State Management
Persists mutable runtime state (bot_mode) to disk.
"""

import json
import logging
from pathlib import Path

from bot.config import BOT_MODE

logger = logging.getLogger(__name__)

STATE_FILE = "bot_state.json"

# ── Mutable state ──────────────────────────────────────────────────
bot_mode: str = BOT_MODE  # "public" or "private"


def load_state():
    """Load persisted state from disk."""
    global bot_mode
    p = Path(STATE_FILE)
    if p.exists():
        try:
            with open(p, "r") as f:
                data = json.load(f)
            bot_mode = data.get("bot_mode", BOT_MODE)
            logger.info(f"State loaded: mode={bot_mode}")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load state: {e}")


def save_state():
    """Persist current state to disk."""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump({"bot_mode": bot_mode}, f, indent=2)
        logger.info(f"State saved: mode={bot_mode}")
    except IOError as e:
        logger.error(f"Failed to save state: {e}")
