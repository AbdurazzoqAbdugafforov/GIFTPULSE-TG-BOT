"""Main menu keyboards for GiftPulse with WebApp and navigation support."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from app.core.config import settings
from app.localization.i18n import i18n


def get_main_menu_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Create persistent main reply keyboard."""
    miniapp_button = KeyboardButton(
        text=i18n.get("btn_open_miniapp", lang=lang),
        web_app=WebAppInfo(url=settings.MINI_APP_URL),
    )
    return ReplyKeyboardMarkup(
        keyboard=[
            [miniapp_button],
            [
                KeyboardButton(text=i18n.get("btn_gift_market", lang=lang)),
                KeyboardButton(text=i18n.get("btn_collections", lang=lang)),
            ],
            [
                KeyboardButton(text=i18n.get("btn_models_rarity", lang=lang)),
                KeyboardButton(text=i18n.get("btn_alerts", lang=lang)),
            ],
            [
                KeyboardButton(text=i18n.get("btn_watchlist", lang=lang)),
                KeyboardButton(text=i18n.get("btn_portfolio", lang=lang)),
            ],
            [
                KeyboardButton(text=i18n.get("btn_radar", lang=lang)),
                KeyboardButton(text=i18n.get("btn_index", lang=lang)),
            ],
            [
                KeyboardButton(text=i18n.get("btn_subscription", lang=lang)),
                KeyboardButton(text=i18n.get("btn_settings", lang=lang)),
            ],
            [
                KeyboardButton(text=i18n.get("btn_help", lang=lang)),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def get_main_menu_inline(lang: str = "uz") -> InlineKeyboardMarkup:
    """Create inline keyboard version of main menu."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get("btn_open_miniapp", lang=lang),
                    web_app=WebAppInfo(url=settings.MINI_APP_URL),
                ),
            ],
            [
                InlineKeyboardButton(text=i18n.get("btn_gift_market", lang=lang), callback_data="menu:market"),
                InlineKeyboardButton(text=i18n.get("btn_collections", lang=lang), callback_data="menu:collections"),
            ],
            [
                InlineKeyboardButton(text=i18n.get("btn_models_rarity", lang=lang), callback_data="menu:models"),
                InlineKeyboardButton(text=i18n.get("btn_alerts", lang=lang), callback_data="menu:alerts"),
            ],
            [
                InlineKeyboardButton(text=i18n.get("btn_watchlist", lang=lang), callback_data="menu:watchlist"),
                InlineKeyboardButton(text=i18n.get("btn_portfolio", lang=lang), callback_data="menu:portfolio"),
            ],
            [
                InlineKeyboardButton(text=i18n.get("btn_radar", lang=lang), callback_data="menu:radar"),
                InlineKeyboardButton(text=i18n.get("btn_index", lang=lang), callback_data="menu:index"),
            ],
            [
                InlineKeyboardButton(text=i18n.get("btn_subscription", lang=lang), callback_data="menu:subscription"),
                InlineKeyboardButton(text=i18n.get("btn_settings", lang=lang), callback_data="menu:settings"),
            ],
            [
                InlineKeyboardButton(text=i18n.get("btn_help", lang=lang), callback_data="menu:help"),
            ],
        ]
    )
