"""Start and onboarding command handler for GiftPulse."""

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    MenuButtonDefault,
    WebAppInfo,
)
from aiogram.fsm.context import FSMContext
from app.core.config import settings
from app.database.models.user import User
from app.database.repositories.user_repo import UserRepository
from app.database.session import get_db_session
from app.bot.keyboards.main_menu import get_main_menu_keyboard, get_main_menu_inline
from app.bot.keyboards.settings_kb import get_language_keyboard
from app.localization.i18n import i18n

router = Router(name="start_router")


def get_mini_app_inline_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Button to launch Telegram Mini App."""
    btn_text = i18n.get("btn_open_miniapp", lang=lang)
    if settings.is_miniapp_https:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=btn_text,
                        web_app=WebAppInfo(url=settings.MINI_APP_URL.strip()),
                    )
                ]
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=btn_text,
                    callback_data="menu:miniapp_info",
                )
            ]
        ]
    )


@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext, db_user: User, is_new_user: bool) -> None:
    """Handle /start command with onboarding or welcome back."""
    await state.clear()
    lang = db_user.language or settings.DEFAULT_LANGUAGE
    name = message.from_user.first_name if message.from_user else "Foydalanuvchi"

    # Set bottom-left chat menu button to launch WebApp only if valid HTTPS is configured
    try:
        if settings.is_miniapp_https:
            await message.bot.set_chat_menu_button(
                chat_id=message.chat.id,
                menu_button=MenuButtonWebApp(text="GiftPulse", web_app=WebAppInfo(url=settings.MINI_APP_URL.strip())),
            )
        else:
            await message.bot.set_chat_menu_button(
                chat_id=message.chat.id,
                menu_button=MenuButtonDefault(),
            )
    except Exception:
        pass

    if is_new_user:
        # Prompt language selection on first visit
        await message.answer(
            text=f"👋 Assalomu alaykum, {name}!\n\nIltimos, tilni tanlang / Please select language / Пожалуйста, выберите язык:",
            reply_markup=get_language_keyboard(),
            parse_mode="HTML",
        )
    else:
        # Welcome message with persistent reply menu + inline action
        welcome_text = i18n.get("welcome", lang=lang, name=name)
        await message.answer(
            text=welcome_text,
            reply_markup=get_main_menu_keyboard(lang),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )


@router.message(F.text.in_({"🏠 Asosiy Menyu", "🏠 Main Menu", "🏠 Главное Меню"}))
@router.message(F.text.contains("Asosiy Menyu") | F.text.contains("Main Menu") | F.text.contains("Главное Меню"))
async def handle_home_message(message: Message, db_user: User) -> None:
    """Return to main menu via reply keyboard button."""
    lang = getattr(db_user, "language", None) or settings.DEFAULT_LANGUAGE
    name = message.from_user.first_name if message.from_user else "Foydalanuvchi"
    welcome_text = i18n.get("welcome", lang=lang, name=name)
    await message.answer(
        text=welcome_text,
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


@router.callback_query(F.data == "menu:home")
async def handle_home_callback(callback: CallbackQuery, db_user: User) -> None:
    """Return to main menu via inline button."""
    lang = getattr(db_user, "language", None) or settings.DEFAULT_LANGUAGE
    name = callback.from_user.first_name if callback.from_user else "Foydalanuvchi"
    welcome_text = i18n.get("welcome", lang=lang, name=name)
    await callback.message.edit_text(
        text=welcome_text,
        reply_markup=get_main_menu_inline(lang),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lang:"))
async def handle_language_choice(callback: CallbackQuery, db_user: User) -> None:
    """Handle language selection callback."""
    chosen_lang = callback.data.split(":")[1]
    async with get_db_session() as session:
        repo = UserRepository(session)
        await repo.update_language(db_user.id, chosen_lang)

    db_user.language = chosen_lang
    await callback.answer()

    name = callback.from_user.first_name if callback.from_user else "User"
    welcome_text = i18n.get("welcome", lang=chosen_lang, name=name)

    # Edit callback message
    await callback.message.edit_text(
        text=welcome_text,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    # Send keyboard
    await callback.message.answer(
        text=i18n.get("lang_changed", lang=chosen_lang),
        reply_markup=get_main_menu_keyboard(chosen_lang),
        parse_mode="HTML",
    )


@router.message(F.text.in_({"🚀 GiftPulse Mini App-ni Ochish", "🚀 Open GiftPulse Mini App", "🚀 Открыть GiftPulse Mini App"}))
@router.message(F.text.contains("Mini App"))
async def handle_miniapp_button_press(message: Message, db_user: User) -> None:
    """Handle click on Mini App reply button when not in HTTPS webapp mode."""
    lang = getattr(db_user, "language", None) or settings.DEFAULT_LANGUAGE
    if lang == "uz":
        text = (
            "ℹ️ <b>GiftPulse Mini App</b>\n\n"
            "Telegram xavfsizlik talablariga ko'ra, Mini App faqat <b>HTTPS</b> havolasi orqali ochiladi.\n\n"
            "Serveringizga domen yoki SSL ulangach, <code>.env</code> faylida quyidagicha sozlang:\n"
            "<code>MINI_APP_URL=https://sizning-domeningiz.com</code>"
        )
    elif lang == "ru":
        text = (
            "ℹ️ <b>GiftPulse Mini App</b>\n\n"
            "По требованиям Telegram, Mini App может открываться только по защищенному протоколу <b>HTTPS</b>.\n\n"
            "После настройки SSL укажите в <code>.env</code>:\n"
            "<code>MINI_APP_URL=https://vash-domen.com</code>"
        )
    else:
        text = (
            "ℹ️ <b>GiftPulse Mini App</b>\n\n"
            "According to Telegram security policies, Mini Apps require a secure <b>HTTPS</b> URL.\n\n"
            "Please configure an HTTPS domain/tunnel and set in <code>.env</code>:\n"
            "<code>MINI_APP_URL=https://your-domain.com</code>"
        )
    await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "menu:miniapp_info")
async def handle_miniapp_info_callback(callback: CallbackQuery, db_user: User) -> None:
    """Handle click on Mini App inline button when HTTPS is not configured."""
    lang = getattr(db_user, "language", None) or settings.DEFAULT_LANGUAGE
    if lang == "uz":
        alert_text = "Mini App faqat HTTPS havola bilan ishlaydi. Iltimos, .env da MINI_APP_URL=https://... sozlang."
    elif lang == "ru":
        alert_text = "Mini App требует протокол HTTPS. Настройте MINI_APP_URL=https://... в .env."
    else:
        alert_text = "Mini App requires HTTPS. Set MINI_APP_URL=https://... in .env."
    await callback.answer(alert_text, show_alert=True)

