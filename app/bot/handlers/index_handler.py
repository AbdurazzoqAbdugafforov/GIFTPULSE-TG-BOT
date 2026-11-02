"""GiftPulse Index (GPI) bot handler."""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from app.database.models.user import User
from app.database.session import get_db_session
from app.services.gift_data.index_service import IndexService

router = Router(name="index_router")


def get_index_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Yangilash", callback_data="index:refresh"),
                InlineKeyboardButton(text="📡 Bozor Radari", callback_data="menu:radar"),
            ],
            [
                InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="menu:home"),
            ],
        ]
    )


def format_index_message(idx: dict) -> str:
    latest_val = idx.get("latest_value", 100.0)
    c1d = idx.get("change_1d_pct", 0.0)
    c7d = idx.get("change_7d_pct", 0.0)
    c1d_sign = "+" if c1d > 0 else ""
    c7d_sign = "+" if c7d > 0 else ""

    constituents = idx.get("constituents", [])
    top_constituents = constituents[:5]
    c_lines = []
    for c in top_constituents:
        w = c.get("weight_pct", 0.0)
        c_lines.append(f"  • <b>{c.get('name')}</b>: {c.get('floor_gram')} G (vazni: {w}%)")
    c_str = "\n".join(c_lines) if c_lines else "  <i>Mavjud emas</i>"

    return (
        f"📈 <b>GIFTPULSE INDEX (GPI)</b>\n\n"
        f"• <b>Indeks qiymati:</b> <code>{latest_val:.2f}</code>\n"
        f"• <b>24 soatlik oʻzgarish:</b> <code>{c1d_sign}{c1d:.2f}%</code>\n"
        f"• <b>7 kunlik oʻzgarish:</b> <code>{c7d_sign}{c7d:.2f}%</code>\n"
        f"• <b>Tarkibidagi kolleksiyalar:</b> <b>{idx.get('constituents_count', 0)} ta</b>\n"
        f"• <b>Kuzatuv sanasi:</b> <code>{idx.get('latest_date', 'N/A')}</code>\n\n"
        f"🏛 <b>Asosiy tarkibiy qismlar:</b>\n{c_str}\n\n"
        f"📊 <i>GiftPulse Market Intelligence</i>\n"
        f"⚠️ <i>Bozor kapitallashuvi va likvidlik asosida hisoblangan umumiy indeks.</i>"
    )


@router.message(Command("index"))
@router.message(F.text.in_({"📈 GiftPulse Index", "📈 Индекс GiftPulse", "📈 GiftPulse Index (GPI)", "📈 Индекс GiftPulse (GPI)"}))
@router.message(F.text.contains("Index") | F.text.contains("Индекс") | F.text.contains("GPI"))
async def handle_index_message(message: Message, db_user: User) -> None:
    async with get_db_session() as session:
        svc = IndexService(session)
        idx = await svc.get_index_overview()

    text = format_index_message(idx)
    await message.answer(text=text, reply_markup=get_index_keyboard(), parse_mode="HTML", disable_web_page_preview=True)


@router.callback_query(F.data.in_(["menu:index", "index:refresh"]))
async def handle_index_callback(callback: CallbackQuery, db_user: User) -> None:
    async with get_db_session() as session:
        svc = IndexService(session)
        idx = await svc.get_index_overview()

    text = format_index_message(idx)
    await callback.message.edit_text(text=text, reply_markup=get_index_keyboard(), parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer("Indeks yangilandi.")
