"""Keyboards for Gift Market, Collections, and Models browsing."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.localization.i18n import i18n


def get_collections_keyboard(
    items: list[dict],
    current_page: int,
    total_pages: int,
    sort_by: str = "floor_desc",
    lang: str = "uz",
) -> InlineKeyboardMarkup:
    """Paginated collection browser keyboard."""
    buttons: list[list[InlineKeyboardButton]] = []

    # 1 collection per row for clarity
    for col in items:
        floor_str = f"{col['floor_gram']:,.0f} G" if col.get("floor_gram") else "N/A"
        c1d = col.get("change_1d_pct", 0.0)
        c_sign = "+" if c1d > 0 else ""
        text = f"🎁 {col['name']} • {floor_str} ({c_sign}{c1d}%)"
        buttons.append([
            InlineKeyboardButton(text=text, callback_data=f"col:view:{col['slug']}")
        ])

    # Sorting options
    buttons.append([
        InlineKeyboardButton(
            text="💰 Floor ↓" if sort_by != "floor_desc" else "✅ Floor ↓",
            callback_data="col:sort:floor_desc",
        ),
        InlineKeyboardButton(
            text="📈 24s ↓" if sort_by != "change_1d_desc" else "✅ 24s ↓",
            callback_data="col:sort:change_1d_desc",
        ),
        InlineKeyboardButton(
            text="🔤 A-Z" if sort_by != "name_asc" else "✅ A-Z",
            callback_data="col:sort:name_asc",
        ),
    ])

    # Pagination navigation
    nav: list[InlineKeyboardButton] = []
    if current_page > 1:
        nav.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"col:page:{current_page - 1}")
        )
    nav.append(
        InlineKeyboardButton(text=f"{current_page}/{max(1, total_pages)}", callback_data="noop")
    )
    if current_page < total_pages:
        nav.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"col:page:{current_page + 1}")
        )
    if nav:
        buttons.append(nav)

    # Return to main menu
    buttons.append([
        InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="menu:home")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_collection_detail_keyboard(
    slug: str,
    is_in_watchlist: bool = False,
    lang: str = "uz",
) -> InlineKeyboardMarkup:
    """Detail view action keyboard."""
    wl_text = "❌ Kuzatuvdan olish" if is_in_watchlist else "⭐ Kuzatuvga qo'shish"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✨ Modellar & Noyoblik", callback_data=f"col:models:{slug}"),
                InlineKeyboardButton(text="🔔 Signal o'rnatish", callback_data=f"alert:new:col:{slug}"),
            ],
            [
                InlineKeyboardButton(text=wl_text, callback_data=f"wl:toggle:{slug}"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Kolleksiyalar ro'yxati", callback_data="menu:collections"),
                InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="menu:home"),
            ],
        ]
    )


def get_models_list_keyboard(
    collection_slug: str,
    models: list[dict],
    current_page: int,
    total_pages: int,
    lang: str = "uz",
) -> InlineKeyboardMarkup:
    """List models within a collection with rarity percentage."""
    buttons: list[list[InlineKeyboardButton]] = []

    for m in models:
        r_str = f" • {m['rarity_pct']}%" if m.get("rarity_pct") is not None else ""
        floor_str = f"{m['floor_gram']:,.0f} G"
        text = f"✨ {m['name']}: {floor_str}{r_str}"
        buttons.append([
            InlineKeyboardButton(text=text, callback_data=f"mod:view:{m['id']}")
        ])

    # Navigation
    nav: list[InlineKeyboardButton] = []
    if current_page > 1:
        nav.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"mod:page:{collection_slug}:{current_page - 1}")
        )
    nav.append(
        InlineKeyboardButton(text=f"{current_page}/{max(1, total_pages)}", callback_data="noop")
    )
    if current_page < total_pages:
        nav.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"mod:page:{collection_slug}:{current_page + 1}")
        )
    if nav:
        buttons.append(nav)

    buttons.append([
        InlineKeyboardButton(text="⬅️ Kolleksiyaga qaytish", callback_data=f"col:view:{collection_slug}"),
        InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="menu:home"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_model_detail_keyboard(
    collection_slug: str,
    model_id: int,
    lang: str = "uz",
) -> InlineKeyboardMarkup:
    """Individual model detail keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔔 Model uchun signal o'rnatish", callback_data=f"alert:new:mod:{model_id}"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Modellar ro'yxati", callback_data=f"col:models:{collection_slug}"),
                InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="menu:home"),
            ],
        ]
    )
