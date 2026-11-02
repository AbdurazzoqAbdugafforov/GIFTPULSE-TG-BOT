"""Gift Market and Collections browser handlers."""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from app.bot.keyboards.market_kb import (
    get_collection_detail_keyboard,
    get_collections_keyboard,
    get_model_detail_keyboard,
    get_models_list_keyboard,
)
from app.database.models.user import User
from app.database.session import get_db_session
from app.localization.i18n import i18n
from app.services.collections.service import CollectionService
from app.services.models.service import ModelService
from app.services.watchlist.service import WatchlistService

router = Router(name="market_router")

PAGE_SIZE = 8


@router.message(Command("market"))
@router.message(Command("collections"))
@router.message(F.text.in_({"🎁 Gift Market", "📂 Kolleksiyalar", "📂 Collections", "📂 Коллекции"}))
@router.message(F.text.contains("Market") | F.text.contains("Kolleksiya") | F.text.contains("Collection") | F.text.contains("Коллекци"))
async def show_market_message(message: Message, db_user: User) -> None:
    """Entry point from reply keyboard or command."""
    lang = db_user.language or "uz"
    async with get_db_session() as session:
        svc = CollectionService(session)
        overview = await svc.get_collections_overview(sort_by="floor_desc", limit=PAGE_SIZE, offset=0)

    items = overview["items"]
    total = overview["total"]
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

    kb = get_collections_keyboard(items, current_page=1, total_pages=total_pages, sort_by="floor_desc", lang=lang)
    text = (
        f"🎁 <b>TELEGRAM GIFTS BOZORI</b>\n\n"
        f"Jami mavjud kolleksiyalar: <b>{total} ta</b>\n\n"
        f"Batafsil koʻrish uchun kolleksiyani tanlang:"
    )
    await message.answer(text=text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)


@router.message(Command("models"))
@router.message(F.text.in_({"✨ Modellar & Noyoblik", "✨ Models & Rarity", "✨ Модели & Редкость"}))
@router.message(F.text.contains("Modellar") | F.text.contains("Models") | F.text.contains("Модели"))
async def show_models_message(message: Message, db_user: User) -> None:
    """Entry point for models & rarity browsing."""
    lang = db_user.language or "uz"
    async with get_db_session() as session:
        svc = CollectionService(session)
        overview = await svc.get_collections_overview(sort_by="floor_desc", limit=PAGE_SIZE, offset=0)

    items = overview["items"]
    total = overview["total"]
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

    kb = get_collections_keyboard(items, current_page=1, total_pages=total_pages, sort_by="floor_desc", lang=lang)
    text = (
        f"✨ <b>GIFT MODELLARI VA NOYOBLIK (RARITY)</b>\n\n"
        f"Modellar va ularning noyoblik darajalarini koʻrish uchun kolleksiyani tanlang:"
    )
    await message.answer(text=text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)


@router.callback_query(F.data.in_(["menu:market", "menu:collections", "menu:models"]))
async def show_market_callback(callback: CallbackQuery, db_user: User) -> None:
    """Show collections list via inline callback."""
    lang = db_user.language or "uz"
    async with get_db_session() as session:
        svc = CollectionService(session)
        overview = await svc.get_collections_overview(sort_by="floor_desc", limit=PAGE_SIZE, offset=0)

    items = overview["items"]
    total = overview["total"]
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

    kb = get_collections_keyboard(items, current_page=1, total_pages=total_pages, sort_by="floor_desc", lang=lang)
    if callback.data == "menu:models":
        text = (
            f"✨ <b>GIFT MODELLARI VA NOYOBLIK (RARITY)</b>\n\n"
            f"Jami mavjud kolleksiyalar: <b>{total} ta</b>\n"
            f"Modellar va ularning noyoblik darajalarini koʻrish uchun kolleksiyani tanlang:"
        )
    else:
        text = (
            f"🎁 <b>TELEGRAM GIFTS BOZORI</b>\n\n"
            f"Jami mavjud kolleksiyalar: <b>{total} ta</b>\n\n"
            f"Batafsil koʻrish uchun kolleksiyani tanlang:"
        )
    await callback.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data.startswith("col:page:"))
async def handle_collection_pagination(callback: CallbackQuery, db_user: User) -> None:
    """Paginate collection list."""
    page = int(callback.data.split(":")[2])
    lang = db_user.language or "uz"
    offset = (page - 1) * PAGE_SIZE

    async with get_db_session() as session:
        svc = CollectionService(session)
        overview = await svc.get_collections_overview(sort_by="floor_desc", limit=PAGE_SIZE, offset=offset)

    items = overview["items"]
    total = overview["total"]
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

    kb = get_collections_keyboard(items, current_page=page, total_pages=total_pages, sort_by="floor_desc", lang=lang)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("col:sort:"))
async def handle_collection_sort(callback: CallbackQuery, db_user: User) -> None:
    """Change sorting order for collections."""
    sort_by = callback.data.split(":")[2]
    lang = db_user.language or "uz"

    async with get_db_session() as session:
        svc = CollectionService(session)
        overview = await svc.get_collections_overview(sort_by=sort_by, limit=PAGE_SIZE, offset=0)

    items = overview["items"]
    total = overview["total"]
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

    kb = get_collections_keyboard(items, current_page=1, total_pages=total_pages, sort_by=sort_by, lang=lang)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("col:view:"))
async def view_collection_details(callback: CallbackQuery, db_user: User) -> None:
    """Show detailed collection screen with floor, 1d/7d change, and actions."""
    slug = callback.data.split(":")[2]
    lang = db_user.language or "uz"

    async with get_db_session() as session:
        svc = CollectionService(session)
        col = await svc.get_collection_details(slug)
        if not col:
            await callback.answer("Kolleksiya topilmadi.", show_alert=True)
            return

        wl_svc = WatchlistService(session)
        is_in_wl = await wl_svc.session.execute(
            select_exists := None  # checked below
        )
        # Check watchlist
        from app.database.models.watchlist import WatchlistEntry
        from sqlalchemy import select
        wl_stmt = select(WatchlistEntry.id).where(
            WatchlistEntry.user_id == db_user.id,
            WatchlistEntry.collection_id == col["id"],
        )
        wl_entry = (await session.execute(wl_stmt)).scalar_one_or_none()
        is_in_wl = wl_entry is not None

    floor_str = f"{col['floor_gram']:,.1f} GRAM" if col.get("floor_gram") else "N/A"
    c1d = col.get("change_1d_pct", 0.0)
    c7d = col.get("change_7d_pct", 0.0)
    c1d_sign = "+" if c1d > 0 else ""
    c7d_sign = "+" if c7d > 0 else ""

    text = (
        f"📂 <b>{col['name']}</b> (<code>{col['slug']}</code>)\n\n"
        f"• <b>Floor narxi:</b> <code>{floor_str}</code>\n"
        f"• <b>24 soatlik oʻzgarish:</b> <code>{c1d_sign}{c1d:.2f}%</code>\n"
        f"• <b>7 kunlik oʻzgarish:</b> <code>{c7d_sign}{c7d:.2f}%</code>\n"
        f"• <b>Yaqinda sotilganlar:</b> {col.get('recent_sales') or 'N/A'}\n"
        f"• <b>Kuzatuv sanasi:</b> <code>{col.get('observation_date')}</code>\n\n"
        f"📊 <i>GiftPulse Market Intelligence</i>\n"
        f"⚠️ <i>Koʻrsatkichlar kunlik statistik qaydlar hisoblanadi.</i>"
    )

    kb = get_collection_detail_keyboard(slug, is_in_watchlist=is_in_wl, lang=lang)
    await callback.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data.startswith("col:models:"))
async def view_collection_models(callback: CallbackQuery, db_user: User) -> None:
    """List models for a given collection."""
    slug = callback.data.split(":")[2]
    lang = db_user.language or "uz"

    async with get_db_session() as session:
        m_svc = ModelService(session)
        result = await m_svc.get_models_for_collection(slug, limit=8, offset=0)

    models = result.get("items", [])
    total = result.get("total", 0)
    col_info = result.get("collection", {})
    col_name = col_info.get("name", slug)
    total_pages = (total + 8 - 1) // 8

    if not models:
        await callback.answer(f"'{col_name}' uchun modellar maʼlumoti hozircha mavjud emas.", show_alert=True)
        return

    text = (
        f"✨ <b>{col_name} — MODELLAR VA NOYOBLIK</b>\n\n"
        f"Jami modellar: <b>{total} ta</b>\n"
        f"Noyoblik foizi modelning barcha sovgʻalar orasidagi ulushini bildiradi.\n\n"
        f"Modelni tanlang:"
    )

    kb = get_models_list_keyboard(slug, models, current_page=1, total_pages=total_pages, lang=lang)
    await callback.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data.startswith("mod:page:"))
async def paginate_collection_models(callback: CallbackQuery, db_user: User) -> None:
    """Paginate models list."""
    parts = callback.data.split(":")
    slug = parts[2]
    page = int(parts[3])
    lang = db_user.language or "uz"
    offset = (page - 1) * 8

    async with get_db_session() as session:
        m_svc = ModelService(session)
        result = await m_svc.get_models_for_collection(slug, limit=8, offset=offset)

    models = result.get("items", [])
    total = result.get("total", 0)
    total_pages = (total + 8 - 1) // 8

    kb = get_models_list_keyboard(slug, models, current_page=page, total_pages=total_pages, lang=lang)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("mod:view:"))
async def view_single_model_detail(callback: CallbackQuery, db_user: User) -> None:
    """View model details and rarity permille."""
    model_id = int(callback.data.split(":")[2])
    lang = db_user.language or "uz"

    async with get_db_session() as session:
        m_svc = ModelService(session)
        model = await m_svc.get_model_details(model_id)

    if not model:
        await callback.answer("Model maʼlumoti topilmadi.", show_alert=True)
        return

    rarity_str = f"<code>{model['rarity_pct']}%</code> ({model['rarity_permille']} ‰)" if model.get("rarity_pct") is not None else "<i>Mavjud emas</i>"
    listings_str = f"<b>{model['buy_now_listings']} ta</b>" if model.get("buy_now_listings") is not None else "<i>Nomaʼlum</i>"

    text = (
        f"✨ <b>{model['name']}</b>\n"
        f"Kolleksiya: <b>{model.get('collection_name')}</b>\n\n"
        f"• <b>Model Floor:</b> <code>{model['floor_gram']:,.1f} GRAM</code>\n"
        f"• <b>Noyoblik (Rarity):</b> {rarity_str}\n"
        f"• <b>Sotuvdagi listinglar:</b> {listings_str}\n"
        f"• <b>Kuzatuv sanasi:</b> <code>{model.get('observation_date')}</code>\n\n"
        f"📊 <i>GiftPulse Analytics Engine</i>"
    )

    kb = get_model_detail_keyboard(model.get("collection_slug", ""), model_id, lang=lang)
    await callback.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()
