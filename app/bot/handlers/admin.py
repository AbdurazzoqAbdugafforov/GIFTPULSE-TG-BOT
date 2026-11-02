"""Administrator management dashboard and payment review handlers for GiftPulse."""

import asyncio
from decimal import Decimal
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from sqlalchemy import func, select
from app.bot.filters.admin import IsAdmin
from app.bot.states.admin_states import AdminBroadcastSG
from app.core.config import settings
from app.core.logging import logger
from app.database.models.alert import Alert, AlertEvent
from app.database.models.collection import GiftCollection
from app.database.models.ingestion import IngestionRun
from app.database.models.model_item import GiftModel
from app.database.models.payment import Payment
from app.database.models.subscription import Subscription
from app.database.models.user import User
from app.database.session import get_db_session
from app.services.gift_data.cache import cache_manager
from app.services.gift_data.ingestion import IngestionService
from app.services.payments.service import PaymentService

router = Router(name="admin_router")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


def get_admin_dashboard_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Platforma Statistikasi", callback_data="admin:stats"),
                InlineKeyboardButton(text="💳 Kutilayotgan To'lovlar", callback_data="admin:payments"),
            ],
            [
                InlineKeyboardButton(text="🔄 Datani Yangilash (Ingest)", callback_data="admin:ingest_now"),
                InlineKeyboardButton(text="📢 Xabar Tarqatish (Broadcast)", callback_data="admin:broadcast"),
            ],
            [
                InlineKeyboardButton(text="🔄 Panelni Yangilash", callback_data="admin:refresh"),
            ],
        ]
    )


@router.message(Command("admin"))
async def handle_admin_dashboard(message: Message) -> None:
    await message.answer(
        "🛡 <b>GiftPulse Administrator Boshqaruv Paneli</b>\n\nQuyidagi amallardan birini tanlang:",
        reply_markup=get_admin_dashboard_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin:refresh")
async def handle_admin_refresh(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🛡 <b>GiftPulse Administrator Boshqaruv Paneli</b>\n\nQuyidagi amallardan birini tanlang:",
        reply_markup=get_admin_dashboard_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer("🔄 Yangilandi")


@router.callback_query(F.data == "admin:stats")
async def handle_admin_stats(callback: CallbackQuery) -> None:
    async with get_db_session() as session:
        # Users count
        user_count = (await session.execute(select(func.count(User.id)))).scalar() or 0
        
        # Subscriptions count
        sub_stmt = select(Subscription.status, func.count(Subscription.id)).group_by(Subscription.status)
        sub_counts = dict((await session.execute(sub_stmt)).all())

        # Alerts count
        alert_stmt = select(Alert.status, func.count(Alert.id)).group_by(Alert.status)
        alert_counts = dict((await session.execute(alert_stmt)).all())

        # Collections and Models count
        coll_count = (await session.execute(select(func.count(GiftCollection.id)))).scalar() or 0
        mod_count = (await session.execute(select(func.count(GiftModel.id)))).scalar() or 0

        # Latest ingestion run
        run_stmt = select(IngestionRun).order_by(IngestionRun.fetched_at.desc()).limit(1)
        last_run = (await session.execute(run_stmt)).scalar_one_or_none()

    cache_status = await cache_manager.get_json("giftpulse:ingestion:status") or {}
    obs_date = cache_status.get("latest_observation_date", "N/A")
    data_fresh = cache_status.get("data_freshness", "N/A")

    active_alerts = alert_counts.get("ACTIVE", 0)
    triggered_alerts = alert_counts.get("TRIGGERED", 0)

    text = (
        f"📊 <b>GIFTPULSE PLATFORMA STATISTIKASI</b>\n\n"
        f"👤 <b>Jami foydalanuvchilar:</b> <code>{user_count} ta</code>\n"
        f"💎 <b>Faol obunalar:</b> <code>{sub_counts.get('ACTIVE', 0)} ta</code>\n\n"
        f"🔔 <b>Faol signallar:</b> <code>{active_alerts} ta</code>\n"
        f"⚡️ <b>Ishlagan signallar:</b> <code>{triggered_alerts} ta</code>\n\n"
        f"🎁 <b>Kolleksiyalar soni:</b> <code>{coll_count} ta</code>\n"
        f"✨ <b>Modellar soni:</b> <code>{mod_count} ta</code>\n\n"
        f"🌐 <b>Soʻnggi snapshot sanasi:</b> <code>{obs_date}</code>\n"
        f"📡 <b>Maʼlumot holati:</b> <code>{data_fresh}</code>\n"
        f"⏱ <b>Soʻnggi Ingestion:</b> <code>{last_run.status if last_run else 'N/A'}</code> ({last_run.fetched_at.strftime('%Y-%m-%d %H:%M') if last_run else 'N/A'})\n\n"
        f"📊 <i>GiftPulse Market Intelligence</i>"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin:stats")],
            [InlineKeyboardButton(text="⬅️ Panelga qaytish", callback_data="admin:refresh")],
        ]
    )
    await callback.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin:ingest_now")
async def handle_manual_ingest(callback: CallbackQuery) -> None:
    await callback.answer("⏳ Ingestion boshlandi...", show_alert=False)
    await callback.message.answer("⏳ <i>Bozor maʼlumotlarini yangilash boshlandi...</i>", parse_mode="HTML")

    async with get_db_session() as session:
        svc = IngestionService(session)
        result = await svc.ingest_all(trigger_alerts=True)

    await callback.message.answer(
        f"✅ <b>Ingestion muvaffaqiyatli yakunlandi!</b>\n\n"
        f"• Snapshot sanasi: <code>{result.get('observation_date')}</code>\n"
        f"• Kolleksiyalar: <code>{result.get('floors', {}).get('status')}</code>\n"
        f"• Modellar: <code>{result.get('models', {}).get('status')}</code>\n"
        f"• Indeks: <code>{result.get('index', {}).get('status')}</code>\n"
        f"• Ishlagan signallar: <b>{result.get('alerts_triggered', 0)} ta</b>",
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin:payments")
async def handle_pending_payments(callback: CallbackQuery) -> None:
    async with get_db_session() as session:
        stmt = (
            select(Payment)
            .where(Payment.status == "PENDING")
            .order_by(Payment.created_at.desc())
            .limit(10)
        )
        payments = list((await session.execute(stmt)).scalars().all())

    if not payments:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Panelga qaytish", callback_data="admin:refresh")]]
        )
        await callback.message.edit_text("✅ <b>Hozirda kutilayotgan toʻlovlar yoʻq.</b>", reply_markup=kb, parse_mode="HTML")
        await callback.answer()
        return

    text = f"💳 <b>KUTILAYOTGAN TOʻLOVLAR ({len(payments)} ta):</b>\n\n"
    buttons = []
    for p in payments:
        text += (
            f"• <b>Toʻlov #{p.id}:</b> Foydalanuvchi <code>{p.user_id}</code> | "
            f"Summa: <code>{p.amount:,.0f} {p.currency}</code>\n"
            f"Chek/Ref: <code>{p.transaction_reference or 'Fayl biriktirilgan'}</code>\n\n"
        )
        buttons.append([
            InlineKeyboardButton(text=f"✅ #{p.id} Tasdiqlash", callback_data=f"admin:pay:approve:{p.id}"),
            InlineKeyboardButton(text=f"❌ #{p.id} Rad etish", callback_data=f"admin:pay:reject:{p.id}"),
        ])

    buttons.append([InlineKeyboardButton(text="⬅️ Panelga qaytish", callback_data="admin:refresh")])
    await callback.message.edit_text(text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin:pay:approve:"))
async def handle_approve_payment(callback: CallbackQuery, bot: Bot) -> None:
    pay_id = int(callback.data.split(":")[3])
    admin_id = callback.from_user.id

    async with get_db_session() as session:
        svc = PaymentService(session, bot=bot)
        success = await svc.approve_payment(pay_id, admin_id)

    if success:
        await callback.answer("✅ Toʻlov tasdiqlandi va obuna yoqildi!", show_alert=True)
        await callback.message.edit_text(f"✅ <b>Toʻlov #{pay_id} tasdiqlandi.</b>", parse_mode="HTML")
    else:
        await callback.answer("❌ Xatolik yuz berdi.", show_alert=True)


@router.callback_query(F.data.startswith("admin:pay:reject:"))
async def handle_reject_payment(callback: CallbackQuery, bot: Bot) -> None:
    pay_id = int(callback.data.split(":")[3])
    admin_id = callback.from_user.id

    async with get_db_session() as session:
        svc = PaymentService(session, bot=bot)
        success = await svc.reject_payment(pay_id, admin_id, reason="Admin tomonidan tekshirilmadi yoki chek yaroqsiz.")

    if success:
        await callback.answer("❌ Toʻlov rad etildi.", show_alert=True)
        await callback.message.edit_text(f"❌ <b>Toʻlov #{pay_id} rad etildi.</b>", parse_mode="HTML")
    else:
        await callback.answer("❌ Xatolik yuz berdi.", show_alert=True)


@router.callback_query(F.data == "admin:broadcast")
async def handle_broadcast_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminBroadcastSG.waiting_for_message)
    await callback.message.answer(
        "📢 <b>Barcha foydalanuvchilarga yuboriladigan xabar matnini kiriting:</b>\n\n<i>Bekor qilish uchun /cancel deb yozing.</i>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminBroadcastSG.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext, bot: Bot) -> None:
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Xabar tarqatish bekor qilindi.")
        return

    text_to_send = message.text
    await state.clear()
    await message.answer("🚀 <i>Xabar tarqatish boshlandi...</i>", parse_mode="HTML")

    async with get_db_session() as session:
        users = (await session.execute(select(User.telegram_id).where(User.is_active == True))).scalars().all()

    sent = 0
    failed = 0
    for tid in users:
        try:
            await bot.send_message(chat_id=tid, text=text_to_send, parse_mode="HTML")
            sent += 1
            await asyncio.sleep(0.05)  # Avoid rate limit
        except Exception:
            failed += 1

    await message.answer(f"✅ <b>Xabar tarqatish yakunlandi!</b>\n\nYuborildi: {sent} ta\nYetib bormadi: {failed} ta", parse_mode="HTML")
