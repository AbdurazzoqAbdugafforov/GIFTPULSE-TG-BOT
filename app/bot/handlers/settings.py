"""Settings and user data privacy handlers for GiftPulse."""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from app.database.models.user import User
from app.database.repositories.user_repo import UserRepository
from app.database.session import get_db_session
from app.bot.keyboards.settings_kb import (
    get_language_keyboard,
    get_timezone_keyboard,
    get_delete_confirm_keyboard,
)
from app.localization.i18n import i18n

router = Router(name="settings_router")


def get_giftpulse_settings_keyboard(daily_report: bool, notifications: bool, lang: str = "uz") -> InlineKeyboardMarkup:
    report_icon = "✅" if daily_report else "❌"
    notif_icon = "✅" if notifications else "❌"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌐 Tilni o'zgartirish (Language)", callback_data="set:lang"),
            ],
            [
                InlineKeyboardButton(text=f"📊 Kunlik bozor hisoboti (09:00): {report_icon}", callback_data="set:toggle_report"),
            ],
            [
                InlineKeyboardButton(text=f"🔔 Xabarnomalar: {notif_icon}", callback_data="set:toggle_notif"),
            ],
            [
                InlineKeyboardButton(text="🕒 Vaqt mintaqasi (Timezone)", callback_data="set:tz"),
            ],
            [
                InlineKeyboardButton(text="🗑 Shaxsiy ma'lumotlarni o'chirish", callback_data="set:delete_data"),
            ],
            [
                InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="menu:home"),
            ],
        ]
    )


@router.message(F.text.in_({"⚙️ Sozlamalar", "⚙️ Settings", "⚙️ Настройки"}))
@router.message(F.text.contains("Sozlamalar") | F.text.contains("Settings") | F.text.contains("Настройки"))
@router.message(Command("settings"))
@router.callback_query(F.data == "menu:settings")
async def handle_settings_menu(event: Message | CallbackQuery, db_user: User) -> None:
    """Render settings dashboard."""
    await render_settings(event, db_user)


async def render_settings(event: Message | CallbackQuery, db_user: User) -> None:
    """Render user settings overview."""
    lang = db_user.language or "uz"

    async with get_db_session() as session:
        repo = UserRepository(session)
        user = await repo.get_by_telegram_id(db_user.telegram_id)

    daily_on = user and user.settings and user.settings.daily_report_enabled
    notif_on = user and user.settings and user.settings.notifications_enabled

    daily_str = "Yoqilgan (09:00)" if daily_on else "O'chirilgan"
    notif_str = "Yoqilgan" if notif_on else "O'chirilgan"

    text = (
        f"⚙️ <b>GIFTPULSE SOZLAMALARI</b>\n\n"
        f"• <b>Til:</b> <code>{db_user.language.upper()}</code>\n"
        f"• <b>Vaqt mintaqasi:</b> <code>{db_user.timezone}</code>\n"
        f"• <b>Narx signallari:</b> {notif_str}\n"
        f"• <b>Kunlik hisobot:</b> {daily_str}\n\n"
        f"Quyidagi tugmalar orqali parametrlarni moslashtirishingiz mumkin:"
    )

    kb = get_giftpulse_settings_keyboard(daily_report=daily_on, notifications=notif_on, lang=lang)
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "set:toggle_report")
async def handle_toggle_report(callback: CallbackQuery, db_user: User) -> None:
    async with get_db_session() as session:
        repo = UserRepository(session)
        new_state = await repo.toggle_daily_report(db_user.id)

    state_str = "yoqildi" if new_state else "o'chirildi"
    await callback.answer(f"Kunlik bozor hisoboti {state_str}.")
    await render_settings(callback, db_user)


@router.callback_query(F.data == "set:toggle_notif")
async def handle_toggle_notif(callback: CallbackQuery, db_user: User) -> None:
    async with get_db_session() as session:
        repo = UserRepository(session)
        new_state = await repo.toggle_notifications(db_user.id)

    state_str = "yoqildi" if new_state else "o'chirildi"
    await callback.answer(f"Bildirishnomalar {state_str}.")
    await render_settings(callback, db_user)


@router.callback_query(F.data == "set:lang")
async def handle_settings_lang(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🌐 Iltimos, tilni tanlang / Please choose a language / Выберите язык:",
        reply_markup=get_language_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "set:tz")
async def handle_settings_tz(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🕒 Qaysi vaqt mintaqasida yashaysiz? Tanlang:",
        reply_markup=get_timezone_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("tz:"))
async def handle_tz_choice(callback: CallbackQuery, db_user: User) -> None:
    tz_name = callback.data.split(":", 1)[1]
    async with get_db_session() as session:
        repo = UserRepository(session)
        await repo.update_timezone(db_user.id, tz_name)

    db_user.timezone = tz_name
    await callback.answer(f"Vaqt mintaqasi saqlandi: {tz_name}")
    await render_settings(callback, db_user)


@router.callback_query(F.data == "set:delete_data")
@router.message(Command("delete_my_data"))
async def handle_delete_data_prompt(event: Message | CallbackQuery, db_user: User) -> None:
    lang = db_user.language or "uz"
    prompt = (
        "⚠️ <b>Diqqat!</b>\n\n"
        "Shaxsiy ma'lumotlaringizni o'chirish barcha faol narx signallari, "
        "kuzatuv ro'yxati va investitsiya portfelingizni butunlay o'chiradi.\n\n"
        "Haqiqatan ham davom etishni xohlaysizmi?"
    )
    kb = get_delete_confirm_keyboard(lang=lang)
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(prompt, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(prompt, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "set:confirm_delete")
async def handle_delete_data_confirm(callback: CallbackQuery, db_user: User) -> None:
    async with get_db_session() as session:
        repo = UserRepository(session)
        await repo.delete_user_data(db_user.telegram_id)

    await callback.message.edit_text("✅ Barcha shaxsiy ma'lumotlaringiz muvaffaqiyatli o'chirildi.", parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "set:cancel_delete")
async def handle_delete_data_cancel(callback: CallbackQuery, db_user: User) -> None:
    await render_settings(callback, db_user)
    await callback.answer()
