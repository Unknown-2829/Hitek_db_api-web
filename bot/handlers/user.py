"""
User Command Handlers
Handles /start, /help, /search, /email, /addr, /fname, /stats, and direct text searches.
"""

import logging
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


def _log_search(user_id: int, username: str | None, query: str, search_type: str, results: int):
    """Log search to the search history log file."""
    global search_count
    search_count += 1
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    uname = username or "N/A"
    logger.info(
        f"[SEARCH] {timestamp} | User: {user_id} (@{uname}) | "
        f"Type: {search_type} | Query: {query} | Results: {results}"
    )


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
    # Import here to get the latest bot_mode
    from bot.config import BOT_MODE
    # We use a mutable ref from main
    import bot.state as state

    text = format_stats(
        total_searches=search_count,
        total_users=user_store.user_count,
        bot_mode=state.bot_mode,
        uptime=get_uptime(),
    )
    await message.answer(text, parse_mode="HTML")


# ── /search <query> ───────────────────────────────────────────────
@router.message(Command("search"))
async def cmd_search(message: Message):
    user_store.add_user(message.from_user.id)
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply(
            "⚠️ <b>Usage:</b> <code>/search &lt;mobile or name&gt;</code>",
            parse_mode="HTML",
        )
        return

    query = args[1].strip()
    await _do_search(message, query)


# ── /email <query> ────────────────────────────────────────────────
@router.message(Command("email"))
async def cmd_email(message: Message):
    user_store.add_user(message.from_user.id)
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply(
            "⚠️ <b>Usage:</b> <code>/email &lt;email address&gt;</code>",
            parse_mode="HTML",
        )
        return

    query = args[1].strip()
    processing = await message.reply("🔍 <b>Searching by email...</b>\n⏳ This may take a while on 1.78B records...", parse_mode="HTML")

    try:
        results = await db.search_by_email(query)
        text = format_results(results, query, "EMAIL")
        _log_search(message.from_user.id, message.from_user.username, query, "EMAIL", len(results))
        await processing.edit_text(text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Email search error: {e}")
        await processing.edit_text(f"❌ <b>Error:</b> <code>{e}</code>", parse_mode="HTML")


# ── /addr <query> ─────────────────────────────────────────────────
@router.message(Command("addr"))
async def cmd_addr(message: Message):
    user_store.add_user(message.from_user.id)
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply(
            "⚠️ <b>Usage:</b> <code>/addr &lt;address&gt;</code>",
            parse_mode="HTML",
        )
        return

    query = args[1].strip()
    processing = await message.reply("🔍 <b>Searching by address...</b>\n⏳ This may take a while on 1.78B records...", parse_mode="HTML")

    try:
        results = await db.search_by_address(query)
        text = format_results(results, query, "ADDRESS")
        _log_search(message.from_user.id, message.from_user.username, query, "ADDRESS", len(results))
        await processing.edit_text(text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Address search error: {e}")
        await processing.edit_text(f"❌ <b>Error:</b> <code>{e}</code>", parse_mode="HTML")


# ── /fname <query> ────────────────────────────────────────────────
@router.message(Command("fname"))
async def cmd_fname(message: Message):
    user_store.add_user(message.from_user.id)
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply(
            "⚠️ <b>Usage:</b> <code>/fname &lt;father name&gt;</code>",
            parse_mode="HTML",
        )
        return

    query = args[1].strip()
    processing = await message.reply("🔍 <b>Searching by father's name...</b>\n⏳ This may take a while on 1.78B records...", parse_mode="HTML")

    try:
        results = await db.search_by_fname(query)
        text = format_results(results, query, "FATHER NAME")
        _log_search(message.from_user.id, message.from_user.username, query, "FNAME", len(results))
        await processing.edit_text(text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Father name search error: {e}")
        await processing.edit_text(f"❌ <b>Error:</b> <code>{e}</code>", parse_mode="HTML")


# ── Direct text messages (auto-detect mobile vs name) ─────────────
@router.message(F.text & ~F.text.startswith("/"))
async def handle_direct_text(message: Message):
    user_store.add_user(message.from_user.id)
    query = message.text.strip()
    if not query:
        return
    await _do_search(message, query)


# ── Shared search logic ───────────────────────────────────────────
async def _do_search(message: Message, query: str):
    """Auto-detect query type and search."""

    # Detect if query is a mobile number (all digits, 10-12 chars)
    clean_query = query.replace(" ", "").replace("-", "").replace("+", "")
    is_mobile = clean_query.isdigit() and 7 <= len(clean_query) <= 15

    if is_mobile:
        search_type = "MOBILE"
        processing = await message.reply(
            f"🔍 <b>Searching mobile:</b> <code>{query}</code>",
            parse_mode="HTML",
        )
        try:
            results = await db.search_by_mobile(clean_query)
            text = format_results(results, query, search_type)
            _log_search(message.from_user.id, message.from_user.username, query, search_type, len(results))
            await processing.edit_text(text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Mobile search error: {e}")
            await processing.edit_text(f"❌ <b>Error:</b> <code>{e}</code>", parse_mode="HTML")
    else:
        search_type = "NAME"
        if len(query) < 3:
            await message.reply(
                "⚠️ <b>Name search requires at least 3 characters.</b>",
                parse_mode="HTML",
            )
            return

        processing = await message.reply(
            f"🔍 <b>Searching name:</b> <code>{query}</code>\n"
            f"⏳ This may take a while on 1.78B records...",
            parse_mode="HTML",
        )
        try:
            results = await db.search_by_name(query)
            text = format_results(results, query, search_type)
            _log_search(message.from_user.id, message.from_user.username, query, search_type, len(results))
            await processing.edit_text(text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Name search error: {e}")
            await processing.edit_text(f"❌ <b>Error:</b> <code>{e}</code>", parse_mode="HTML")
