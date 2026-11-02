"""User auto-registration and activity tracking middleware."""

from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from app.core.config import settings
from app.database.models.user import User as DbUser
from app.database.session import get_db_session
from app.database.repositories.user_repo import UserRepository


class UserTrackingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user")
        if not tg_user:
            return await handler(event, data)

        try:
            async with get_db_session() as session:
                repo = UserRepository(session)
                db_user, is_new = await repo.get_or_create(
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name,
                    language=settings.DEFAULT_LANGUAGE,
                    timezone_str=settings.DEFAULT_TIMEZONE,
                )
                data["db_user"] = db_user
                data["is_new_user"] = is_new
                data["user_lang"] = db_user.language or settings.DEFAULT_LANGUAGE
        except Exception:
            # Fallback user so message handling is never blocked
            data["db_user"] = DbUser(
                id=1,
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name or "Foydalanuvchi",
                language=settings.DEFAULT_LANGUAGE,
                timezone=settings.DEFAULT_TIMEZONE,
            )
            data["is_new_user"] = False
            data["user_lang"] = settings.DEFAULT_LANGUAGE

        return await handler(event, data)
