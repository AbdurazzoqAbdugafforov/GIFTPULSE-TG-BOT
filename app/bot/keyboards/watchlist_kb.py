"""Inline keyboards for managing user watchlist."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.localization.i18n import i18n


def get_watchlist_keyboard(symbols: list[str], lang: str = "uz") -> InlineKeyboardMarkup:
    """Keyboard listing watchlist coins with quick navigation and delete options."""
    buttons: list[list[InlineKeyboardButton]] = []

    for s in symbols:
        clean = s.replace("USDT", "")
        buttons.append([
            InlineKeyboardButton(text=f"🪙 {clean} / USDT", callback_data=f"price:view:{s}"),
            InlineKeyboardButton(text="🗑", callback_data=f"wl:delete:{s}"),
        ])

    buttons.append([
        InlineKeyboardButton(
            text="🔍 " + i18n.get("prices_search_prompt", lang=lang)[:20] + "...",
            callback_data="price:search",
        ),
        InlineKeyboardButton(
            text=i18n.get("btn_refresh", lang=lang),
            callback_data="wl:refresh",
        ),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
