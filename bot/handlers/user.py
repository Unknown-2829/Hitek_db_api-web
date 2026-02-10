"""
User Command Handlers
Handles /start, /help, /search, /stats, and direct text (mobile number only).
"""

import logging
import re
import time
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart

from bot.database import db
from bot.formatters import (
    format_results,
    format_welcome,
    format_help,
    format_stats,
)
from bot.user_store import user_store

logger = logging.getLogger(__name__)
router = Router(name="user")

# ── Global counters ────────────────────────────────────────────────
search_count: int = 0
start_time: float = time.time()


def get_search_count() -> int:
    return search_count


def get_uptime() -> str:
    elapsed = int(time.time() - start_time)
    days, rem = divmod(elapsed, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def _log_search(user_id: int, username: str | None, query: str, results: int):
    """Log search to the search history log file."""
    global search_count
    search_count += 1
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    uname = username or "N/A"
    logger.info(
        f"[SEARCH] {timestamp} | User: {user_id} (@{uname}) | "
        f"Query: {query} | Results: {results}"
    )


def _clean_mobile(raw: str) -> str | None:
    """
    Extract a clean 10-digit Indian mobile number from any format.
    Handles: +91 90981 95568, 091-9098195568, 91 9098195568, 09098195568, etc.
    Returns 10-digit string or None if invalid.
    """
    # Remove all non-digit characters (spaces, dashes, dots, brackets, +)
    digits = re.sub(r"[^\d]", "", raw)

    if not digits:
        return None

    # Strip leading country code / trunk prefix
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]   # +91 XXXXXXXXXX → XXXXXXXXXX
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]   # 0XXXXXXXXXX → XXXXXXXXXX
    elif len(digits) == 13 and digits.startswith("091"):
        digits = digits[3:]   # 091 XXXXXXXXXX → XXXXXXXXXX

    # Must be exactly 10 digits now
    if len(digits) == 10 and digits[0] in "6789":
        return digits

    return None


# ── /start ─────────────────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(message: Message):
    user_store.add_user(message.from_user.id)
    await message.answer(format_welcome(), parse_mode="HTML")


# ── /help ──────────────────────────────────────────────────────────
@router.message(Command("help"))
async def cmd_help(message: Message):
    user_store.add_user(message.from_user.id)
    await message.answer(format_help(), parse_mode="HTML")


# ── /stats ─────────────────────────────────────────────────────────
@router.message(Command("stats"))
async def cmd_stats(message: Message):
    user_store.add_user(message.from_user.id)
    import bot.state as state

    text = format_stats(
        total_searches=search_count,
        total_users=user_store.user_count,
        bot_mode=state.bot_mode,
        uptime=get_uptime(),
    )
    await message.answer(text, parse_mode="HTML")


# ── /search <number> ──────────────────────────────────────────────
@router.message(Command("search"))
async def cmd_search(message: Message):
    user_store.add_user(message.from_user.id)
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply(
            "⚠️ <b>Usage:</b> <code>/search 9876543210</code>\n\n"
            "📱 Enter a <b>10-digit mobile number</b> only.",
            parse_mode="HTML",
        )
        return

    await _do_mobile_search(message, args[1].strip())


# ── Direct text messages → mobile search ──────────────────────────
@router.message(F.text & ~F.text.startswith("/"))
async def handle_direct_text(message: Message):
    user_store.add_user(message.from_user.id)
    query = message.text.strip()
    if not query:
        return
    await _do_mobile_search(message, query)


# ── Core mobile search logic ──────────────────────────────────────
async def _do_mobile_search(message: Message, raw_input: str):
    """Clean the input, validate as 10-digit mobile, and search."""

    mobile = _clean_mobile(raw_input)

    if mobile is None:
        await message.reply(
            "❌ <b>Invalid number!</b>\n\n"
            "📱 Please enter a valid <b>10-digit Indian mobile number</b>.\n\n"
            "<b>✅ Correct:</b>\n"
            "  <code>9876543210</code>\n\n"
            "<b>❌ Wrong:</b>\n"
            "  <code>+91 9876543210</code>\n"
            "  <code>09876543210</code>\n"
            "  <code>hello</code>\n\n"
            "<i>💡 Just send the 10 digits, we'll handle the rest!</i>",
            parse_mode="HTML",
        )
        return

    # Check if user entered with prefix — warn them strictly
    clean_digits = re.sub(r"[^\d]", "", raw_input)
    prefix_warning = ""
    if clean_digits != mobile:
        prefix_warning = (
            f"\n\n⚠️ <b>You entered:</b> <code>{raw_input}</code>\n"
            f"🔄 <b>Auto-corrected to:</b> <code>{mobile}</code>\n\n"
            f"❗ <b>Next time, enter only 10 digits!</b>\n"
            f"❌ <code>+91 9876543210</code>\n"
            f"❌ <code>09876543210</code>\n"
            f"✅ <code>9876543210</code>"
        )

    processing = await message.reply(
        f"🔍 <b>Searching:</b> <code>{mobile}</code>",
        parse_mode="HTML",
    )

    try:
        t_start = time.perf_counter()
        results = await db.search_by_mobile(mobile)
        elapsed_ms = int((time.perf_counter() - t_start) * 1000)

        text = format_results(results, mobile, "MOBILE", elapsed_ms=elapsed_ms)
        if prefix_warning:
            text += prefix_warning
        _log_search(message.from_user.id, message.from_user.username, mobile, len(results))
        await processing.edit_text(text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Mobile search error: {e}")
        await processing.edit_text(f"❌ <b>Error:</b> <code>{e}</code>", parse_mode="HTML")
