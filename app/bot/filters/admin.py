"""Custom filter to check if a Telegram user is an authorized administrator."""

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from app.core.config import settings


class IsAdmin(BaseFilter):
    """Filter that passes only for authorized admin Telegram user IDs."""

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user_id = event.from_user.id if event.from_user else None
        if not user_id:
            return False
        return settings.is_admin(user_id)
