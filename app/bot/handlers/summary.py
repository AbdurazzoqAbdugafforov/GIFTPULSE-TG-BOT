"""Daily Market Summary settings and opt-in handler."""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from app.database.models.user import User
from app.database.repositories.user_repo import UserRepository
from app.database.session import get_db_session
from app.localization.i18n import i18n

router = Router(name="summary_router")


@router.message(F.text.in_({"📰 Kunlik Hisobot", "📰 Daily Summary", "📰 Ежедневный Отчет"}))
@router.message(Command("summary"))
async def handle_summary_menu(message: Message, db_user: User) -> None:
    """Render daily market summary status and toggle option."""
    await render_summary_status(message, db_user, is_callback=False)


@router.callback_query(F.data == "summary:toggle")
async def handle_summary_toggle(callback: CallbackQuery, db_user: User) -> None:
    """Toggle daily market summary on or off."""
    lang = db_user.language or "uz"

    async with get_db_session() as session:
        repo = UserRepository(session)
        new_state = await repo.toggle_daily_summary(db_user.id)

    feedback = i18n.get("summary_enabled" if new_state else "summary_disabled", lang=lang)
    await callback.answer(feedback, show_alert=True)
    await render_summary_status(callback.message, db_user, is_callback=True)


async def render_summary_status(message: Message, db_user: User, is_callback: bool = False) -> None:
    """Display summary status."""
    lang = db_user.language or "uz"

    async with get_db_session() as session:
        repo = UserRepository(session)
        user = await repo.get_by_telegram_id(db_user.telegram_id)
        is_enabled = user.settings.daily_summary_enabled if user and user.settings else False

    status_str = "🟢 Yoqilgan (Faol)" if is_enabled else "🔴 O'chirilgan"

    text = i18n.get("summary_title", lang=lang, status=status_str)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get("btn_toggle_summary", lang=lang),
                    callback_data="summary:toggle",
                )
            ]
        ]
    )

    if is_callback:
        await message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")
