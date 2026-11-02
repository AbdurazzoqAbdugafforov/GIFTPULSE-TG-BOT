"""Inline keyboards for Live Prices and Coin details."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.localization.i18n import i18n


def get_prices_list_keyboard(
    symbols: list[str],
    current_page: int,
    total_pages: int,
    lang: str = "uz",
) -> InlineKeyboardMarkup:
    """Paginated list of coins."""
    buttons: list[list[InlineKeyboardButton]] = []

    # 2 coins per row
    row: list[InlineKeyboardButton] = []
    for s in symbols:
        clean = s.replace("USDT", "")
        row.append(InlineKeyboardButton(text=f"🪙 {clean}", callback_data=f"price:view:{s}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Search button
    buttons.append([
        InlineKeyboardButton(
            text="🔍 " + i18n.get("prices_search_prompt", lang=lang)[:20] + "...",
            callback_data="price:search",
        )
    ])

    # Pagination navigation
    nav: list[InlineKeyboardButton] = []
    if current_page > 1:
        nav.append(
            InlineKeyboardButton(text=i18n.get("btn_prev", lang=lang), callback_data=f"price:page:{current_page - 1}")
        )
    nav.append(
        InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="noop")
    )
    if current_page < total_pages:
        nav.append(
            InlineKeyboardButton(text=i18n.get("btn_next", lang=lang), callback_data=f"price:page:{current_page + 1}")
        )
    if nav:
        buttons.append(nav)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_coin_detail_keyboard(
    symbol: str,
    is_in_watchlist: bool,
    lang: str = "uz",
) -> InlineKeyboardMarkup:
    """Action buttons for coin details."""
    wl_text = (
        i18n.get("btn_remove_watchlist", lang=lang)
        if is_in_watchlist
        else i18n.get("btn_add_watchlist", lang=lang)
    )
    wl_action = f"price:wl_remove:{symbol}" if is_in_watchlist else f"price:wl_add:{symbol}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=wl_text, callback_data=wl_action),
                InlineKeyboardButton(
                    text=i18n.get("btn_create_alert", lang=lang),
                    callback_data=f"alert:new_for:{symbol}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=i18n.get("btn_refresh", lang=lang),
                    callback_data=f"price:refresh:{symbol}",
                ),
                InlineKeyboardButton(
                    text=i18n.get("btn_back", lang=lang),
                    callback_data="price:page:1",
                ),
            ],
        ]
    )
