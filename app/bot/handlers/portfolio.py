"""Portfolio tracker bot handlers."""

from decimal import Decimal
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from app.core.constants import DATA_ATTRIBUTION_TEXT, DATA_ATTRIBUTION_URL, MARKET_DISCLAIMER
from app.database.models.collection import GiftCollection
from app.database.models.user import User
from app.database.session import get_db_session
from app.services.portfolio.service import PortfolioService
from sqlalchemy import select

router = Router(name="portfolio_router")


class AddPositionState(StatesGroup):
    waiting_for_collection = State()
    waiting_for_quantity = State()
    waiting_for_price = State()


def get_portfolio_keyboard(positions: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for p in positions:
        pos_id = p["id"]
        cname = p["collection_name"]
        mname = f" ({p['model_name']})" if p.get("model_name") else ""
        text = f"{cname}{mname}: {p['quantity']} dona | PnL: {p['pnl_pct']:+.1f}%"
        buttons.append([
            InlineKeyboardButton(text=f"📌 {text}", callback_data=f"port:view:{pos_id}"),
            InlineKeyboardButton(text="🗑", callback_data=f"port:del:{pos_id}"),
        ])

    buttons.append([
        InlineKeyboardButton(text="➕ Gift Qoʻshish", callback_data="port:add"),
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="port:refresh"),
    ])
    buttons.append([
        InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="menu:home"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def format_portfolio_text(summary: dict) -> str:
    est_val = summary.get("total_estimated_value", 0.0)
    cost = summary.get("total_cost_basis", 0.0)
    pnl = summary.get("total_unrealized_pnl", 0.0)
    pnl_pct = summary.get("total_pnl_pct", 0.0)
    sign = "+" if pnl > 0 else ""

    warnings = summary.get("warnings", [])
    warn_text = ""
    if warnings:
        warn_text = "\n\n⚠️ <b>Ogohlantirishlar:</b>\n" + "\n".join(f"• <i>{w}</i>" for w in warnings[:2])

    return (
        f"💼 <b>SHAXSIY GIFTLAR PORTFELI</b>\n\n"
        f"• <b>Umumiy taxminiy qiymat:</b> <code>{est_val:,.1f} GRAM</code>\n"
        f"• <b>Xarid xarajati:</b> <code>{cost:,.1f} GRAM</code>\n"
        f"• <b>Kutilayotgan PnL:</b> <code>{sign}{pnl:,.1f} GRAM ({pnl_pct:+.2f}%)</code>"
        f"{warn_text}\n\n"
        f"📊 <i>GiftPulse Market Intelligence</i>\n"
        f"⚠️ <i>{MARKET_DISCLAIMER}</i>"
    )


@router.message(Command("portfolio"))
@router.message(F.text.in_({"💼 Portfelim", "💼 My Portfolio", "💼 Мой Портфель"}))
@router.message(F.text.contains("Portfolio") | F.text.contains("Portfel") | F.text.contains("Портфель"))
async def handle_portfolio_message(message: Message, db_user: User) -> None:
    async with get_db_session() as session:
        svc = PortfolioService(session)
        summary = await svc.calculate_summary(db_user.id)

    text = format_portfolio_text(summary)
    kb = get_portfolio_keyboard(summary.get("positions", []))
    await message.answer(text=text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)


@router.callback_query(F.data.in_(["menu:portfolio", "port:refresh"]))
async def handle_portfolio_callback(callback: CallbackQuery, db_user: User) -> None:
    async with get_db_session() as session:
        svc = PortfolioService(session)
        summary = await svc.calculate_summary(db_user.id)

    text = format_portfolio_text(summary)
    kb = get_portfolio_keyboard(summary.get("positions", []))
    await callback.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data.startswith("port:del:"))
async def handle_delete_position(callback: CallbackQuery, db_user: User) -> None:
    pos_id = int(callback.data.split(":")[2])
    async with get_db_session() as session:
        svc = PortfolioService(session)
        await svc.delete_position(pos_id, db_user.id)
        summary = await svc.calculate_summary(db_user.id)

    await callback.answer("Pozitsiya oʻchirildi.")
    text = format_portfolio_text(summary)
    kb = get_portfolio_keyboard(summary.get("positions", []))
    await callback.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)


@router.callback_query(F.data == "port:add")
async def handle_add_position_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Prompt user for collection name/slug to add."""
    await state.set_state(AddPositionState.waiting_for_collection)
    await callback.message.answer(
        "📝 Portfelga qoʻshish uchun kolleksiya nomini yoki slugini kiriting (masalan: <code>algorithmcup</code>):",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AddPositionState.waiting_for_collection)
async def process_collection_input(message: Message, state: FSMContext) -> None:
    col_input = message.text.strip().lower()
    async with get_db_session() as session:
        stmt = select(GiftCollection).where(
            (GiftCollection.collection_slug == col_input)
            | (GiftCollection.collection_name.ilike(f"%{col_input}%"))
        )
        col = (await session.execute(stmt)).scalar_one_or_none()

    if not col:
        await message.answer("❌ Kolleksiya topilmadi. Qaytadan urinib koʻring yoki bekor qiling.")
        return

    await state.update_data(collection_id=col.id, collection_name=col.collection_name)
    await state.set_state(AddPositionState.waiting_for_quantity)
    await message.answer(f"✅ Tanlandi: <b>{col.collection_name}</b>\n\nSovgʻalar sonini kiriting (masalan: <code>1</code>):", parse_mode="HTML")


@router.message(AddPositionState.waiting_for_quantity)
async def process_quantity_input(message: Message, state: FSMContext) -> None:
    try:
        qty = Decimal(message.text.strip().replace(",", "."))
        if qty <= 0:
            raise ValueError()
    except Exception:
        await message.answer("❌ Notoʻgʻri miqdor. Iltimos, musbat son kiriting (masalan: 1):")
        return

    await state.update_data(quantity=str(qty))
    await state.set_state(AddPositionState.waiting_for_price)
    await message.answer("💰 Bir dona sovgʻa xarid narxini kiriting (GRAM da, masalan: <code>150</code>):", parse_mode="HTML")


@router.message(AddPositionState.waiting_for_price)
async def process_price_input(message: Message, state: FSMContext, db_user: User) -> None:
    try:
        price = Decimal(message.text.strip().replace(",", "."))
        if price <= 0:
            raise ValueError()
    except Exception:
        await message.answer("❌ Notoʻgʻri narx. Iltimos, musbat son kiriting:")
        return

    data = await state.get_data()
    await state.clear()

    async with get_db_session() as session:
        svc = PortfolioService(session)
        port = await svc.get_or_create_default_portfolio(db_user.id)
        await svc.add_position(
            portfolio_id=port.id,
            collection_id=data["collection_id"],
            quantity=Decimal(data["quantity"]),
            purchase_price=price,
        )
        summary = await svc.calculate_summary(db_user.id)

    await message.answer("🎉 <b>Gift muvaffaqiyatli portfelga qoʻshildi!</b>", parse_mode="HTML")
    text = format_portfolio_text(summary)
    kb = get_portfolio_keyboard(summary.get("positions", []))
    await message.answer(text=text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)
