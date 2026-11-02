"""Start and onboarding command handler for GiftPulse."""

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
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
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=btn_text,
                    web_app=WebAppInfo(url=settings.MINI_APP_URL),
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

    # Set bottom-left chat menu button to launch WebApp
    try:
        await message.bot.set_chat_menu_button(
            chat_id=message.chat.id,
            menu_button=MenuButtonWebApp(text="GiftPulse", web_app=WebAppInfo(url=settings.MINI_APP_URL)),
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
