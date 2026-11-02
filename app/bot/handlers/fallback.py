"""Fallback message and callback handler for unhandled user inputs."""

from aiogram import Router
from aiogram.types import CallbackQuery, Message
from app.bot.keyboards.main_menu import get_main_menu_keyboard
from app.core.config import settings
from app.database.models.user import User
from app.localization.i18n import i18n

router = Router(name="fallback_router")


@router.message()
async def handle_fallback_message(message: Message, db_user: User) -> None:
    """Respond to any unhandled user message by showing the main menu."""
    lang = getattr(db_user, "language", None) or settings.DEFAULT_LANGUAGE
    name = message.from_user.first_name if message.from_user else "Foydalanuvchi"
    welcome_text = i18n.get("welcome", lang=lang, name=name)
    await message.answer(
        text=welcome_text,
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


@router.callback_query()
async def handle_fallback_callback(callback: CallbackQuery) -> None:
    """Acknowledge any unhandled callback so the client never hangs with a spinner."""
    try:
        await callback.answer()
    except Exception:
        pass
