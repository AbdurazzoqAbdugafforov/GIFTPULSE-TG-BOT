"""Watchlist bot handlers."""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from app.core.constants import DATA_ATTRIBUTION_TEXT, DATA_ATTRIBUTION_URL
from app.database.models.collection import GiftCollection
from app.database.models.user import User
from app.database.session import get_db_session
from app.services.collections.service import CollectionService
from app.services.watchlist.service import WatchlistService
from sqlalchemy import select

router = Router(name="watchlist_router")


def get_watchlist_keyboard(items: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for item in items:
        slug = item["collection_slug"]
        buttons.append([
            InlineKeyboardButton(
                text=f"📂 {item['collection_name']} ({item['floor_gram']:,.0f} G)",
                callback_data=f"col:view:{slug}",
            ),
            InlineKeyboardButton(
                text="❌ Oʻchirish",
                callback_data=f"wl:remove:{item['collection_id']}",
            ),
        ])

    buttons.append([
        InlineKeyboardButton(text="🎁 Bozorga oʻtish", callback_data="menu:market"),
        InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="menu:home"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("watchlist"))
@router.message(F.text.in_({"⭐ Kuzatuv Ro'yxati", "⭐ My Watchlist", "⭐ Мой Список"}))
@router.message(F.text.contains("Watchlist") | F.text.contains("Kuzatuv") | F.text.contains("Список"))
async def handle_watchlist_message(message: Message, db_user: User) -> None:
    async with get_db_session() as session:
        svc = WatchlistService(session)
        items = await svc.get_user_watchlist(db_user.id)

    if not items:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🎁 Kolleksiyalarni koʻrish", callback_data="menu:market")],
                [InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="menu:home")],
            ]
        )
        await message.answer(
            text="⭐ <b>KUZATUV ROʻYXATINGIZ BOʻSH</b>\n\nKolleksiyalar sahifasidan '⭐ Kuzatuvga qoʻshish' tugmasi orqali qiziqqan Giftlaringizni qoʻshishingiz mumkin.",
            reply_markup=kb,
            parse_mode="HTML",
        )
        return

    text = (
        f"⭐ <b>SIZNING KUZATUV ROʻYXATINGIZ ({len(items)} ta)</b>\n\n"
        f"Har bir kolleksiyaning soʻnggi qayd etilgan floor narxi va 24s oʻzgarishi:"
    )
    await message.answer(text=text, reply_markup=get_watchlist_keyboard(items), parse_mode="HTML", disable_web_page_preview=True)


@router.callback_query(F.data == "menu:watchlist")
async def handle_watchlist_callback(callback: CallbackQuery, db_user: User) -> None:
    async with get_db_session() as session:
        svc = WatchlistService(session)
        items = await svc.get_user_watchlist(db_user.id)

    if not items:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🎁 Kolleksiyalarni koʻrish", callback_data="menu:market")],
                [InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="menu:home")],
            ]
        )
        await callback.message.edit_text(
            text="⭐ <b>KUZATUV ROʻYXATINGIZ BOʻSH</b>\n\nKolleksiyalar sahifasidan '⭐ Kuzatuvga qoʻshish' tugmasi orqali qiziqqan Giftlaringizni qoʻshishingiz mumkin.",
            reply_markup=kb,
            parse_mode="HTML",
        )
        await callback.answer()
        return

    text = (
        f"⭐ <b>SIZNING KUZATUV ROʻYXATINGIZ ({len(items)} ta)</b>\n\n"
        f"Har bir kolleksiyaning soʻnggi qayd etilgan floor narxi va 24s oʻzgarishi:"
    )
    await callback.message.edit_text(text=text, reply_markup=get_watchlist_keyboard(items), parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data.startswith("wl:toggle:"))
async def handle_watchlist_toggle(callback: CallbackQuery, db_user: User) -> None:
    slug = callback.data.split(":")[2]
    async with get_db_session() as session:
        c_stmt = select(GiftCollection).where(GiftCollection.collection_slug == slug)
        col = (await session.execute(c_stmt)).scalar_one_or_none()
        if not col:
            await callback.answer("Kolleksiya topilmadi.", show_alert=True)
            return

        wl_svc = WatchlistService(session)
        is_in_wl = await wl_svc.is_in_watchlist(db_user.id, col.id)
        if is_in_wl:
            await wl_svc.remove_from_watchlist(db_user.id, col.id)
            await callback.answer("❌ Kuzatuvdan oʻchirildi.")
        else:
            success, err = await wl_svc.add_to_watchlist(db_user.id, col.id)
            if not success:
                await callback.answer(err or "Xatolik yuz berdi.", show_alert=True)
                return
            await callback.answer("⭐ Kuzatuvga qoʻshildi!")

        # Refresh collection view keyboard
        from app.bot.keyboards.market_kb import get_collection_detail_keyboard
        new_kb = get_collection_detail_keyboard(slug, is_in_watchlist=not is_in_wl, lang=db_user.language or "uz")
        await callback.message.edit_reply_markup(reply_markup=new_kb)


@router.callback_query(F.data.startswith("wl:remove:"))
async def handle_watchlist_remove(callback: CallbackQuery, db_user: User) -> None:
    col_id = int(callback.data.split(":")[2])
    async with get_db_session() as session:
        wl_svc = WatchlistService(session)
        await wl_svc.remove_from_watchlist(db_user.id, col_id)
        items = await wl_svc.get_user_watchlist(db_user.id)

    await callback.answer("Kolleksiya oʻchirildi.")
    if not items:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🎁 Kolleksiyalarni koʻrish", callback_data="menu:market")],
                [InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="menu:home")],
            ]
        )
        await callback.message.edit_text(
            text="⭐ <b>KUZATUV ROʻYXATINGIZ BOʻSH</b>",
            reply_markup=kb,
            parse_mode="HTML",
        )
    else:
        text = f"⭐ <b>SIZNING KUZATUV ROʻYXATINGIZ ({len(items)} ta)</b>"
        await callback.message.edit_text(text=text, reply_markup=get_watchlist_keyboard(items), parse_mode="HTML", disable_web_page_preview=True)
