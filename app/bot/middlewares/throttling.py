"""Rate limiting middleware using Redis throttle tokens."""

from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.security import check_rate_limit
from app.localization.i18n import i18n


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, redis_client: aioredis.Redis | None = None):
        super().__init__()
        self.redis = redis_client

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        # Allow admins to bypass rate limit
        if settings.is_admin(user.id):
            return await handler(event, data)

        allowed = await check_rate_limit(
            redis_client=self.redis,
            user_id=user.id,
            max_calls=settings.RATE_LIMIT_CALLS_PER_MINUTE,
            window_seconds=60,
        )

        if not allowed:
            lang = data.get("user_lang", settings.DEFAULT_LANGUAGE)
            msg = i18n.get("rate_limit_exceeded", lang=lang)
            if hasattr(event, "answer"):
                try:
                    await event.answer(msg, show_alert=True)
                except Exception:
                    pass
            elif hasattr(event, "reply"):
                try:
                    await event.reply(msg)
                except Exception:
                    pass
            return None

        return await handler(event, data)
