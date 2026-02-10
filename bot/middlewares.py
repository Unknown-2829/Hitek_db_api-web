"""
Aiogram 3.x Middlewares
- AntiFloodMiddleware: rate-limits users to 1 search per N seconds
- AccessControlMiddleware: enforces public/private bot mode
"""

import time
import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

logger = logging.getLogger(__name__)


class AntiFloodMiddleware(BaseMiddleware):
    """
    Rate limiter: drops messages if user sends too fast.
    Only applies to search-related messages (not /start, /help, etc).
    """

    EXEMPT_COMMANDS = {"/start", "/help", "/admin", "/stats", "/getmode"}

    def __init__(self, rate_limit: int = 2):
        self.rate_limit = rate_limit
        self._user_timestamps: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        # Skip rate limit for exempt commands
        if event.text and any(event.text.startswith(cmd) for cmd in self.EXEMPT_COMMANDS):
            return await handler(event, data)

        user_id = event.from_user.id
        now = time.time()
        last_time = self._user_timestamps.get(user_id, 0)

        if now - last_time < self.rate_limit:
            remaining = round(self.rate_limit - (now - last_time), 1)
            await event.reply(
                f"⏳ <b>Slow down!</b> Wait <code>{remaining}s</code> before next search.",
                parse_mode="HTML",
            )
            logger.info(f"Rate limited user {user_id}")
            return  # Drop the message

        self._user_timestamps[user_id] = now
        return await handler(event, data)


class AccessControlMiddleware(BaseMiddleware):
    """
    Enforces bot access mode (public/private).
    In private mode, only admins can use the bot.
    """

    def __init__(self, admin_ids: set[int], get_mode_func, get_banned_func):
        self.admin_ids = admin_ids
        self.get_mode = get_mode_func  # callable returning current mode
        self.get_banned = get_banned_func  # callable returning banned set

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id

        # Admins always have access
        if user_id in self.admin_ids:
            return await handler(event, data)

        # Check banned users
        if user_id in self.get_banned():
            await event.reply(
                "🚫 <b>You have been banned from using this bot.</b>",
                parse_mode="HTML",
            )
            return

        # Check bot mode
        if self.get_mode() == "private":
            await event.reply(
                "🔒 <b>This bot is currently in private mode.</b>\n"
                "Only authorized users can access it.",
                parse_mode="HTML",
            )
            return

        return await handler(event, data)
