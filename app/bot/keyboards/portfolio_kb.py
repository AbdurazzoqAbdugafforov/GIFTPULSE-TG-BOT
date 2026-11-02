"""Inline keyboards for portfolio tracker."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.database.models.portfolio import PortfolioPosition
from app.localization.i18n import i18n


def get_portfolio_keyboard(positions: list[PortfolioPosition], lang: str = "uz") -> InlineKeyboardMarkup:
    """Action buttons for portfolio positions."""
    buttons: list[list[InlineKeyboardButton]] = []

    # Position delete shortcuts
    for pos in positions:
        buttons.append([
            InlineKeyboardButton(text=f"🪙 {pos.symbol} ({pos.quantity})", callback_data="noop"),
            InlineKeyboardButton(text="🗑", callback_data=f"port:delete:{pos.id}"),
        ])

    buttons.append([
        InlineKeyboardButton(
            text=i18n.get("btn_add_position", lang=lang),
            callback_data="port:add",
        ),
        InlineKeyboardButton(
            text=i18n.get("btn_refresh", lang=lang),
            callback_data="port:refresh",
        ),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
