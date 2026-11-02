"""Price Alerts bot handlers."""

from decimal import Decimal
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from app.core.constants import AlertStatus, AlertType
from app.database.models.collection import GiftCollection
from app.database.models.user import User
from app.database.session import get_db_session
from app.services.alerts.engine import AlertEngine
from sqlalchemy import select

router = Router(name="alerts_router")


class CreateAlertState(StatesGroup):
    waiting_for_collection = State()
    waiting_for_type = State()
    waiting_for_target = State()
    waiting_for_recurring = State()


def get_alerts_keyboard(alerts: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for a in alerts:
        a_id = a["id"]
        cname = a["collection_name"]
        mname = f" ({a['model_name']})" if a.get("model_name") else ""
        t_val = a["target_value"]
        status_icon = "🟢" if a["status"] == "ACTIVE" else ("🟡" if a["status"] == "PAUSED" else "🔴")
        action_btn = (
            InlineKeyboardButton(text="⏸ Pauza", callback_data=f"alert:pause:{a_id}")
            if a["status"] == "ACTIVE"
            else InlineKeyboardButton(text="▶️ Davom", callback_data=f"alert:resume:{a_id}")
        )
        buttons.append([
            InlineKeyboardButton(text=f"{status_icon} {cname}{mname}: {t_val} G", callback_data=f"alert:view:{a_id}"),
            action_btn,
            InlineKeyboardButton(text="🗑", callback_data=f"alert:del:{a_id}"),
        ])

    buttons.append([
        InlineKeyboardButton(text="➕ Yangi Signal Oʻrnatish", callback_data="alert:create"),
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="alert:refresh"),
    ])
    buttons.append([
        InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="menu:home"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("alerts"))
@router.message(F.text.in_({"🔔 Narx Signallari", "🔔 Price Alerts", "🔔 Сигналы Цен"}))
@router.message(F.text.contains("Alert") | F.text.contains("Signal") | F.text.contains("Сигнал"))
async def handle_alerts_message(message: Message, db_user: User) -> None:
    async with get_db_session() as session:
        engine = AlertEngine(session)
        alerts = await engine.get_user_alerts(db_user.id)

    if not alerts:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Yangi Signal Oʻrnatish", callback_data="alert:create")],
                [InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="menu:home")],
            ]
        )
        await message.answer(
            text="🔔 <b>NARX SIGNALLARI (ALERTS)</b>\n\nSizda hozircha faol narx signallari yoʻq.\nYangi kunlik snapshot chiqqanda avtomatik xabar olish uchun signal oʻrnating.",
            reply_markup=kb,
            parse_mode="HTML",
        )
        return

    text = f"🔔 <b>SIZNING NARX SIGNALLARINGIZ ({len(alerts)} ta)</b>\n\nSignallar yangi kunlik snapshot yuklanganda avtomatik tekshiriladi:"
    await message.answer(text=text, reply_markup=get_alerts_keyboard(alerts), parse_mode="HTML")


@router.callback_query(F.data.in_(["menu:alerts", "alert:refresh"]))
async def handle_alerts_callback(callback: CallbackQuery, db_user: User) -> None:
    async with get_db_session() as session:
        engine = AlertEngine(session)
        alerts = await engine.get_user_alerts(db_user.id)

    if not alerts:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Yangi Signal Oʻrnatish", callback_data="alert:create")],
                [InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="menu:home")],
            ]
        )
        await callback.message.edit_text(
            text="🔔 <b>NARX SIGNALLARI (ALERTS)</b>\n\nSizda hozircha faol narx signallari yoʻq.",
            reply_markup=kb,
            parse_mode="HTML",
        )
        await callback.answer()
        return

    text = f"🔔 <b>SIZNING NARX SIGNALLARINGIZ ({len(alerts)} ta)</b>\n\nSignallar yangi kunlik snapshot yuklanganda avtomatik tekshiriladi:"
    await callback.message.edit_text(text=text, reply_markup=get_alerts_keyboard(alerts), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("alert:pause:"))
async def handle_pause_alert(callback: CallbackQuery, db_user: User) -> None:
    alert_id = int(callback.data.split(":")[2])
    async with get_db_session() as session:
        engine = AlertEngine(session)
        await engine.pause_alert(alert_id, db_user.id)
        alerts = await engine.get_user_alerts(db_user.id)

    await callback.answer("Signal toʻxtatildi (pauza).")
    await callback.message.edit_reply_markup(reply_markup=get_alerts_keyboard(alerts))


@router.callback_query(F.data.startswith("alert:resume:"))
async def handle_resume_alert(callback: CallbackQuery, db_user: User) -> None:
    alert_id = int(callback.data.split(":")[2])
    async with get_db_session() as session:
        engine = AlertEngine(session)
        await engine.resume_alert(alert_id, db_user.id)
        alerts = await engine.get_user_alerts(db_user.id)

    await callback.answer("Signal faollashtirildi!")
    await callback.message.edit_reply_markup(reply_markup=get_alerts_keyboard(alerts))


@router.callback_query(F.data.startswith("alert:del:"))
async def handle_delete_alert(callback: CallbackQuery, db_user: User) -> None:
    alert_id = int(callback.data.split(":")[2])
    async with get_db_session() as session:
        engine = AlertEngine(session)
        await engine.delete_alert(alert_id, db_user.id)
        alerts = await engine.get_user_alerts(db_user.id)

    await callback.answer("Signal oʻchirildi.")
    await callback.message.edit_reply_markup(reply_markup=get_alerts_keyboard(alerts))


@router.callback_query(F.data == "alert:create")
async def handle_create_alert_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CreateAlertState.waiting_for_collection)
    await callback.message.answer(
        "📝 Signal oʻrnatish uchun kolleksiya nomini yoki slugini yozing (masalan: <code>algorithmcup</code>):",
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("alert:new:col:"))
async def handle_quick_alert_create(callback: CallbackQuery, state: FSMContext) -> None:
    slug = callback.data.split(":")[3]
    async with get_db_session() as session:
        stmt = select(GiftCollection).where(GiftCollection.collection_slug == slug)
        col = (await session.execute(stmt)).scalar_one_or_none()

    if not col:
        await callback.answer("Kolleksiya topilmadi.", show_alert=True)
        return

    await state.update_data(collection_id=col.id, collection_name=col.collection_name, model_id=None)
    await state.set_state(CreateAlertState.waiting_for_type)

    type_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📈 Floor oshganda (Above)", callback_data="atype:COLLECTION_FLOOR_ABOVE"),
                InlineKeyboardButton(text="📉 Floor tushganda (Below)", callback_data="atype:COLLECTION_FLOOR_BELOW"),
            ],
            [
                InlineKeyboardButton(text="🚀 Foiz oshganda (+% Up)", callback_data="atype:COLLECTION_FLOOR_PCT_UP"),
                InlineKeyboardButton(text="🔻 Foiz tushganda (-% Down)", callback_data="atype:COLLECTION_FLOOR_PCT_DOWN"),
            ],
        ]
    )
    await callback.message.answer(
        f"🎯 <b>{col.collection_name}</b> uchun signal turini tanlang:",
        reply_markup=type_kb,
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(CreateAlertState.waiting_for_collection)
async def process_alert_collection(message: Message, state: FSMContext) -> None:
    col_input = message.text.strip().lower()
    async with get_db_session() as session:
        stmt = select(GiftCollection).where(
            (GiftCollection.collection_slug == col_input)
            | (GiftCollection.collection_name.ilike(f"%{col_input}%"))
        )
        col = (await session.execute(stmt)).scalar_one_or_none()

    if not col:
        await message.answer("❌ Kolleksiya topilmadi. Iltimos, qaytadan yozing:")
        return

    await state.update_data(collection_id=col.id, collection_name=col.collection_name, model_id=None)
    await state.set_state(CreateAlertState.waiting_for_type)

    type_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📈 Floor oshganda (Above)", callback_data="atype:COLLECTION_FLOOR_ABOVE"),
                InlineKeyboardButton(text="📉 Floor tushganda (Below)", callback_data="atype:COLLECTION_FLOOR_BELOW"),
            ],
            [
                InlineKeyboardButton(text="🚀 Foiz oshganda (+% Up)", callback_data="atype:COLLECTION_FLOOR_PCT_UP"),
                InlineKeyboardButton(text="🔻 Foiz tushganda (-% Down)", callback_data="atype:COLLECTION_FLOOR_PCT_DOWN"),
            ],
        ]
    )
    await message.answer(
        f"🎯 <b>{col.collection_name}</b> uchun signal turini tanlang:",
        reply_markup=type_kb,
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("atype:"))
async def process_alert_type(callback: CallbackQuery, state: FSMContext) -> None:
    alert_type = callback.data.split(":")[1]
    await state.update_data(alert_type=alert_type)
    await state.set_state(CreateAlertState.waiting_for_target)

    hint = "GRAM qiymatini kiriting (masalan: 200)" if "FLOOR_" in alert_type and "PCT" not in alert_type else "Oʻzgarish foizini kiriting (masalan: 10)"
    await callback.message.answer(
        f"🎯 Maqsadli darajani kiriting:\n\n<i>{hint}</i>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(CreateAlertState.waiting_for_target)
async def process_alert_target(message: Message, state: FSMContext, db_user: User) -> None:
    try:
        val = Decimal(message.text.strip().replace(",", "."))
        if val <= 0:
            raise ValueError()
    except Exception:
        await message.answer("❌ Notoʻgʻri qiymat. Iltimos, musbat son kiriting:")
        return

    data = await state.get_data()
    await state.clear()

    async with get_db_session() as session:
        engine = AlertEngine(session)
        alert, err = await engine.create_alert(
            user_id=db_user.id,
            collection_id=data["collection_id"],
            model_id=data.get("model_id"),
            alert_type=data["alert_type"],
            target_value=val,
            is_recurring=False,
        )

    if not alert:
        await message.answer(f"❌ Signal yaratilmadi: {err}")
        return

    await message.answer(
        f"✅ <b>Signal muvaffaqiyatli yaratildi!</b>\n\n"
        f"Kolleksiya: <b>{data['collection_name']}</b>\n"
        f"Turi: <code>{data['alert_type']}</code>\n"
        f"Maqsad: <code>{val}</code>\n\n"
        f"Yangi kunlik snapshot qayd etilganda bot sizga xabar yuboradi.",
        parse_mode="HTML",
    )
