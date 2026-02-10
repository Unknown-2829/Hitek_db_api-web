"""
HiTek DB Telegram Bot — Main Entry Point
High-performance bot for querying 1.78B row SQLite database.
"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats

from bot.config import BOT_TOKEN, ADMIN_IDS, RATE_LIMIT, LOG_FILE, validate_config
from bot.database import db
from bot.middlewares import AntiFloodMiddleware, AccessControlMiddleware
from bot.user_store import user_store
import bot.state as state
from bot.handlers import user as user_handlers
from bot.handlers import admin as admin_handlers


# ── Logging Setup ──────────────────────────────────────────────────
def setup_logging():
    """Configure dual logging: console + search_history.log file."""
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Root logger
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(log_format, date_format))
    root.addHandler(console)

    # File handler for search history
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    root.addHandler(file_handler)

    # Suppress noisy libraries
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)


# ── Startup & Shutdown ─────────────────────────────────────────────
async def on_startup(bot: Bot):
    """Called when bot starts polling."""
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("⚡ HiTek DB Bot Starting...")
    logger.info(f"👑 Admin IDs: {ADMIN_IDS}")
    logger.info(f"🔒 Bot Mode: {state.bot_mode}")
    logger.info(f"⏱️ Rate Limit: {RATE_LIMIT}s")
    logger.info("=" * 50)

    # Connect to database
    await db.connect()

    # Load persisted state
    state.load_state()

    # Register bot commands with Telegram menu
    user_commands = [
        BotCommand(command="start", description="🏠 Start the bot"),
        BotCommand(command="search", description="🔍 Search by mobile number"),
        BotCommand(command="help", description="📖 Show all commands"),
        BotCommand(command="stats", description="📊 Bot statistics"),
    ]
    await bot.set_my_commands(user_commands, scope=BotCommandScopeAllPrivateChats())
    logger.info("✅ Bot commands registered with Telegram.")

    # Notify admins
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "     ⚡ <b>HiTek DB Bot ONLINE</b> ⚡\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"  🔒 Mode   : <code>{state.bot_mode.upper()}</code>\n"
                f"  👥 Users  : <code>{user_store.user_count}</code>\n"
                f"  ⏱ Limit  : <code>{RATE_LIMIT}s</code>\n\n"
                "Send /admin for command list.",
                parse_mode="HTML",
            )
        except Exception:
            pass

    logger.info("✅ Bot is ready!")


async def on_shutdown(bot: Bot):
    """Called when bot stops."""
    logger = logging.getLogger(__name__)
    logger.info("Shutting down...")
    await db.close()
    state.save_state()
    logger.info("Goodbye! 👋")


# ── Main ───────────────────────────────────────────────────────────
async def main():
    # Setup
    setup_logging()
    logger = logging.getLogger(__name__)

    # Validate config
    errors = validate_config()
    if errors:
        for err in errors:
            logger.error(f"❌ CONFIG ERROR: {err}")
        sys.exit(1)

    # Create bot and dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Register middlewares (order matters: access control first, then anti-flood)
    dp.message.middleware(
        AccessControlMiddleware(
            admin_ids=ADMIN_IDS,
            get_mode_func=lambda: state.bot_mode,
            get_banned_func=user_store.get_banned,
        )
    )
    dp.message.middleware(AntiFloodMiddleware(rate_limit=RATE_LIMIT))

    # Register routers (admin first so admin commands get priority)
    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)

    # Lifecycle hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Start polling
    logger.info("Starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user.")
