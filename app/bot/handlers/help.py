"""Help and support handler for GiftPulse."""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from app.database.models.user import User
from app.localization.i18n import i18n

router = Router(name="help_router")


@router.message(Command("help"))
@router.message(F.text.in_({"ℹ️ Yordam", "ℹ️ Help", "ℹ️ Помощь"}))
@router.message(F.text.contains("Yordam") | F.text.contains("Help") | F.text.contains("Помощь"))
async def handle_help_message(message: Message, db_user: User) -> None:
    """Show help guide and instructions."""
    lang = db_user.language or "uz"
    await message.answer(i18n.get("help_text", lang=lang), parse_mode="HTML", disable_web_page_preview=True)


@router.callback_query(F.data == "menu:help")
async def handle_help_callback(callback: CallbackQuery, db_user: User) -> None:
    lang = db_user.language or "uz"
    await callback.message.answer(i18n.get("help_text", lang=lang), parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()
