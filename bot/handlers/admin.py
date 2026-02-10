"""
Admin Command Handlers
Restricted to ADMIN_IDS — /admin, /logs, /dbstats, /alert, /clearlog,
/setmode, /getmode, /ban, /unban, /banlist, /users
"""

import logging
import os
import asyncio

from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

from bot.config import ADMIN_IDS, LOG_FILE
from bot.database import db
from bot.formatters import format_admin_help
from bot.user_store import user_store
import bot.state as state

logger = logging.getLogger(__name__)
router = Router(name="admin")


# ── Admin filter ───────────────────────────────────────────────────
def _is_admin(message: Message) -> bool:
    return message.from_user and message.from_user.id in ADMIN_IDS


# ── /admin ─────────────────────────────────────────────────────────
@router.message(Command("admin"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_admin(message: Message):
    await message.answer(format_admin_help(), parse_mode="HTML")


# ── /logs ──────────────────────────────────────────────────────────
@router.message(Command("logs"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_logs(message: Message):
    if not os.path.exists(LOG_FILE):
        await message.reply("📄 <b>No log file found.</b> No searches recorded yet.", parse_mode="HTML")
        return

    file_size = os.path.getsize(LOG_FILE)
    if file_size == 0:
        await message.reply("📄 <b>Log file is empty.</b>", parse_mode="HTML")
        return

    try:
        doc = FSInputFile(LOG_FILE, filename="search_history.log")
        size_str = _format_size(file_size)
        await message.reply_document(
            doc,
            caption=f"📋 <b>Search History Log</b>\n📦 Size: <code>{size_str}</code>",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Failed to send log file: {e}")
        await message.reply(f"❌ <b>Error sending log:</b> <code>{e}</code>", parse_mode="HTML")


# ── /dbstats ───────────────────────────────────────────────────────
@router.message(Command("dbstats"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_dbstats(message: Message):
    processing = await message.reply("⏳ <b>Fetching database stats...</b>", parse_mode="HTML")

    try:
        row_count = await db.get_row_count()
        db_size = await db.get_db_size()
        size_str = _format_size(db_size)

        text = (
            "<pre>"
            "╔══════════════════════════════════╗\n"
            "║      💾 DATABASE STATISTICS       ║\n"
            "╠══════════════════════════════════╣\n"
            f"║  📊 Rows (approx) : {row_count:>12,} ║\n"
            f"║  💽 DB Size       : {size_str:>12} ║\n"
            f"║  📁 DB Path       : /data/       ║\n"
            f"║  🔧 Mode          : WAL          ║\n"
            "╚══════════════════════════════════╝"
            "</pre>"
        )
        await processing.edit_text(text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"DB stats error: {e}")
        await processing.edit_text(f"❌ <b>Error:</b> <code>{e}</code>", parse_mode="HTML")


# ── /alert <message> ──────────────────────────────────────────────
@router.message(Command("alert"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_alert(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply(
            "⚠️ <b>Usage:</b> <code>/alert &lt;message&gt;</code>",
            parse_mode="HTML",
        )
        return

    alert_text = args[1].strip()
    all_users = user_store.get_all_users()

    if not all_users:
        await message.reply("⚠️ <b>No tracked users to broadcast to.</b>", parse_mode="HTML")
        return

    status = await message.reply(
        f"📡 <b>Broadcasting to {len(all_users)} users...</b>",
        parse_mode="HTML",
    )

    broadcast_msg = (
        "<pre>"
        "╔══════════════════════════════════╗\n"
        "║     📢 ADMIN BROADCAST           ║\n"
        "╚══════════════════════════════════╝"
        "</pre>\n\n"
        f"{alert_text}"
    )

    success = 0
    failed = 0

    for uid in all_users:
        try:
            await message.bot.send_message(uid, broadcast_msg, parse_mode="HTML")
            success += 1
            await asyncio.sleep(0.05)  # avoid Telegram rate limits
        except Exception:
            failed += 1

    await status.edit_text(
        f"✅ <b>Broadcast complete!</b>\n"
        f"📨 Sent: <code>{success}</code>\n"
        f"❌ Failed: <code>{failed}</code>",
        parse_mode="HTML",
    )


# ── /clearlog ─────────────────────────────────────────────────────
@router.message(Command("clearlog"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_clearlog(message: Message):
    try:
        with open(LOG_FILE, "w") as f:
            f.truncate(0)
        await message.reply("🗑️ <b>Search log cleared!</b>", parse_mode="HTML")
        logger.info(f"Log cleared by admin {message.from_user.id}")
    except Exception as e:
        await message.reply(f"❌ <b>Error:</b> <code>{e}</code>", parse_mode="HTML")


# ── /setmode <public|private> ─────────────────────────────────────
@router.message(Command("setmode"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_setmode(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or args[1].strip().lower() not in ("public", "private"):
        await message.reply(
            "⚠️ <b>Usage:</b> <code>/setmode public</code> or <code>/setmode private</code>",
            parse_mode="HTML",
        )
        return

    new_mode = args[1].strip().lower()
    state.bot_mode = new_mode
    state.save_state()

    emoji = "🌐" if new_mode == "public" else "🔒"
    await message.reply(
        f"{emoji} <b>Bot mode set to:</b> <code>{new_mode.upper()}</code>",
        parse_mode="HTML",
    )
    logger.info(f"Bot mode changed to {new_mode} by admin {message.from_user.id}")


# ── /getmode ──────────────────────────────────────────────────────
@router.message(Command("getmode"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_getmode(message: Message):
    emoji = "🌐" if state.bot_mode == "public" else "🔒"
    await message.reply(
        f"{emoji} <b>Current mode:</b> <code>{state.bot_mode.upper()}</code>",
        parse_mode="HTML",
    )


# ── /users ────────────────────────────────────────────────────────
@router.message(Command("users"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_users(message: Message):
    total = user_store.user_count
    banned = len(user_store.get_banned())
    await message.reply(
        f"👥 <b>Tracked Users:</b> <code>{total}</code>\n"
        f"🚫 <b>Banned:</b> <code>{banned}</code>",
        parse_mode="HTML",
    )


# ── /ban <user_id> ────────────────────────────────────────────────
@router.message(Command("ban"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_ban(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.reply(
            "⚠️ <b>Usage:</b> <code>/ban &lt;user_id&gt;</code>",
            parse_mode="HTML",
        )
        return

    target_id = int(args[1].strip())

    if target_id in ADMIN_IDS:
        await message.reply("⚠️ <b>Cannot ban an admin!</b>", parse_mode="HTML")
        return

    if user_store.ban_user(target_id):
        await message.reply(
            f"🚫 <b>User</b> <code>{target_id}</code> <b>has been banned.</b>",
            parse_mode="HTML",
        )
        logger.info(f"User {target_id} banned by admin {message.from_user.id}")
    else:
        await message.reply(
            f"⚠️ <b>User</b> <code>{target_id}</code> <b>is already banned.</b>",
            parse_mode="HTML",
        )


# ── /unban <user_id> ──────────────────────────────────────────────
@router.message(Command("unban"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_unban(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.reply(
            "⚠️ <b>Usage:</b> <code>/unban &lt;user_id&gt;</code>",
            parse_mode="HTML",
        )
        return

    target_id = int(args[1].strip())

    if user_store.unban_user(target_id):
        await message.reply(
            f"✅ <b>User</b> <code>{target_id}</code> <b>has been unbanned.</b>",
            parse_mode="HTML",
        )
        logger.info(f"User {target_id} unbanned by admin {message.from_user.id}")
    else:
        await message.reply(
            f"⚠️ <b>User</b> <code>{target_id}</code> <b>is not banned.</b>",
            parse_mode="HTML",
        )


# ── /banlist ──────────────────────────────────────────────────────
@router.message(Command("banlist"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_banlist(message: Message):
    banned = user_store.get_banned()
    if not banned:
        await message.reply("✅ <b>No banned users.</b>", parse_mode="HTML")
        return

    lines = [f"  • <code>{uid}</code>" for uid in sorted(banned)]
    text = f"🚫 <b>Banned Users ({len(banned)}):</b>\n\n" + "\n".join(lines)
    await message.reply(text, parse_mode="HTML")


# ── Helpers ────────────────────────────────────────────────────────
def _format_size(size_bytes: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"
