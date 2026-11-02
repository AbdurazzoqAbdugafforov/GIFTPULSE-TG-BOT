"""Inline keyboards for user settings."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.localization.i18n import i18n


def get_settings_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Settings menu inline buttons."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get("btn_change_lang", lang=lang),
                    callback_data="set:lang",
                ),
                InlineKeyboardButton(
                    text=i18n.get("btn_change_tz", lang=lang),
                    callback_data="set:tz",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=i18n.get("btn_delete_data", lang=lang),
                    callback_data="set:delete_data",
                )
            ],
        ]
    )


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Language selection keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇿 O'zbekcha (Lotin)", callback_data="lang:uz")],
            [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
        ]
    )


def get_timezone_keyboard() -> InlineKeyboardMarkup:
    """Common timezones selection keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇿 Toshkent (UTC+5)", callback_data="tz:Asia/Tashkent")],
            [InlineKeyboardButton(text="🇦🇪 Dubai (UTC+4)", callback_data="tz:Asia/Dubai")],
            [InlineKeyboardButton(text="🇷🇺 Moskva (UTC+3)", callback_data="tz:Europe/Moscow")],
            [InlineKeyboardButton(text="🇹🇷 Istanbul (UTC+3)", callback_data="tz:Europe/Istanbul")],
            [InlineKeyboardButton(text="🇬🇧 London (UTC+0)", callback_data="tz:Europe/London")],
        ]
    )


def get_delete_confirm_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Confirmation keyboard for permanent data deletion."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚠️ " + i18n.get("btn_confirm", lang=lang),
                    callback_data="set:confirm_delete",
                ),
                InlineKeyboardButton(
                    text=i18n.get("btn_cancel", lang=lang),
                    callback_data="set:cancel_delete",
                ),
            ]
        ]
    )
