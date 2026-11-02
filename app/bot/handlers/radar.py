"""Market Radar bot handler."""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from app.core.constants import DATA_ATTRIBUTION_TEXT, DATA_ATTRIBUTION_URL, MARKET_DISCLAIMER
from app.database.models.user import User
from app.database.session import get_db_session
from app.services.radar.service import RadarService

router = Router(name="radar_router")


def get_radar_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Yangilash", callback_data="radar:refresh"),
                InlineKeyboardButton(text="📈 GiftPulse Index", callback_data="menu:index"),
            ],
            [
                InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="menu:home"),
            ],
        ]
    )


def format_radar_message(radar: dict) -> str:
    gainers_1d = radar.get("top_gainers_1d", [])
    losers_1d = radar.get("top_losers_1d", [])
    gainers_7d = radar.get("top_gainers_7d", [])
    active_sales = radar.get("active_sales_collections", [])
    idx = radar.get("index_summary", {})

    def format_list(items, pct_key="change_1d_pct"):
        if not items:
            return "  <i>Maʼlumot yoʻq</i>"
        lines = []
        for x in items:
            pct = x.get(pct_key, 0.0)
            sign = "+" if pct > 0 else ""
            lines.append(f"  • <b>{x['name']}</b>: {x['floor_gram']:,.1f} GRAM (<code>{sign}{pct}%</code>)")
        return "\n".join(lines)

    g1_str = format_list(gainers_1d, "change_1d_pct")
    l1_str = format_list(losers_1d, "change_1d_pct")
    g7_str = format_list(gainers_7d, "change_7d_pct")

    sales_lines = []
    for s in active_sales:
        sales_lines.append(f"  • <b>{s['name']}</b>: {s['recent_sales']} ta sotuv (Floor: {s['floor_gram']:,.1f} G)")
    sales_str = "\n".join(sales_lines) if sales_lines else "  <i>Maʼlumot yoʻq</i>"

    idx_val = idx.get("value", 100.0)
    idx_1d = idx.get("change_1d_pct", 0.0)
    idx_sign = "+" if idx_1d > 0 else ""

    return (
        f"📡 <b>BOZOR RADARI (GiftPulse Analytics)</b>\n\n"
        f"🏛 <b>GiftPulse Index (GPI):</b> <code>{idx_val:.2f}</code> ({idx_sign}{idx_1d:.2f}%)\n"
        f"Sana: <code>{idx.get('date', 'N/A')}</code>\n\n"
        f"📈 <b>Top Oʻsgan Kolleksiyalar (24s):</b>\n{g1_str}\n\n"
        f"📉 <b>Top Tushgan Kolleksiyalar (24s):</b>\n{l1_str}\n\n"
        f"🚀 <b>Top Oʻsgan Kolleksiyalar (7 kun):</b>\n{g7_str}\n\n"
        f"🔥 <b>Eng Faol Savdolar:</b>\n{sales_str}\n\n"
        f"📊 <i>GiftPulse Market Intelligence</i>\n"
        f"⚠️ <i>{MARKET_DISCLAIMER}</i>"
    )


@router.message(Command("radar"))
@router.message(F.text.in_({"📡 Bozor Radari", "📡 Market Radar", "📡 Радар Рынка"}))
@router.message(F.text.contains("Radar") | F.text.contains("Радар"))
async def handle_radar_message(message: Message, db_user: User) -> None:
    async with get_db_session() as session:
        svc = RadarService(session)
        radar = await svc.get_market_radar()

    text = format_radar_message(radar)
    await message.answer(text=text, reply_markup=get_radar_keyboard(), parse_mode="HTML", disable_web_page_preview=True)


@router.callback_query(F.data.in_(["menu:radar", "radar:refresh"]))
async def handle_radar_callback(callback: CallbackQuery, db_user: User) -> None:
    async with get_db_session() as session:
        svc = RadarService(session)
        radar = await svc.get_market_radar()

    text = format_radar_message(radar)
    await callback.message.edit_text(text=text, reply_markup=get_radar_keyboard(), parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer("Radar yangilandi.")
