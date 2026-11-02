"""Subscription and manual payment flow handlers."""

from decimal import Decimal
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, PhotoSize
from aiogram.fsm.context import FSMContext
from app.core.config import settings
from app.core.constants import PlanType
from app.database.models.user import User
from app.database.repositories.subscription_repo import SubscriptionRepository
from app.database.session import get_db_session
from app.bot.states.payment_states import SubmitPaymentSG
from app.bot.keyboards.subscription_kb import get_subscription_keyboard, get_payment_submit_keyboard
from app.localization.i18n import i18n
from app.services.payments.service import PaymentService
from app.services.subscriptions.entitlement import EntitlementService

router = Router(name="subscription_router")


@router.message(F.text.in_({"💎 Obuna", "💎 Subscription", "💎 Подписка", "💎 Obuna (PRO / ELITE)", "💎 Subscription (PRO/ELITE)", "💎 Подписка (PRO / ELITE)"}) | F.text.contains("Obuna") | F.text.contains("Subscription") | F.text.contains("Подписка"))
@router.message(Command("subscription"))
@router.callback_query(F.data == "menu:subscription")
async def handle_subscription_menu(event: Message | CallbackQuery, state: FSMContext, db_user: User) -> None:
    """Render subscription overview."""
    await state.clear()
    if isinstance(event, CallbackQuery):
        await render_subscription_info(event.message, db_user, is_callback=True)
        await event.answer()
    else:
        await render_subscription_info(event, db_user, is_callback=False)


@router.callback_query(F.data == "sub:refresh")
async def handle_subscription_refresh(callback: CallbackQuery, db_user: User) -> None:
    """Refresh subscription status."""
    await render_subscription_info(callback.message, db_user, is_callback=True)
    await callback.answer("🔄 Yangilandi" if db_user.language == "uz" else "🔄 Refreshed")


async def render_subscription_info(message: Message, db_user: User, is_callback: bool = False) -> None:
    """Display user plan details."""
    lang = db_user.language or "uz"

    async with get_db_session() as session:
        ent = EntitlementService(session)
        plan_info = await ent.get_user_plan(db_user.id)
        sub_repo = SubscriptionRepository(session)
        pro_plan = await sub_repo.get_plan_by_code(PlanType.PRO.value)
        elite_plan = await sub_repo.get_plan_by_code(PlanType.ELITE.value)

    pro_price = f"{pro_plan.price:,.0f}" if pro_plan else f"{settings.PRO_PLAN_PRICE:,}"
    elite_price = f"{elite_plan.price:,.0f}" if elite_plan else f"{settings.ELITE_PLAN_PRICE:,}"

    if plan_info.expires_at:
        exp_str = plan_info.expires_at.strftime("%Y-%m-%d %H:%M UTC")
    else:
        exp_str = "Cheksiz (Lifetime)" if plan_info.code == PlanType.FREE.value else "Nomaʼlum"

    text = i18n.get(
        "subscription_title",
        lang=lang,
        current_plan=f"{plan_info.name} ({plan_info.code})",
        expires_at=exp_str,
        pro_price=pro_price,
        elite_price=elite_price,
    )

    kb = get_subscription_keyboard(lang=lang)
    if is_callback:
        await message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("sub:choose:"))
async def handle_plan_choice(callback: CallbackQuery, state: FSMContext, db_user: User) -> None:
    """Display payment instructions for chosen plan."""
    plan_code = callback.data.split(":")[2].upper()
    lang = db_user.language or "uz"

    async with get_db_session() as session:
        sub_repo = SubscriptionRepository(session)
        plan = await sub_repo.get_plan_by_code(plan_code)

    if not plan:
        await callback.answer("Tarif topilmadi.", show_alert=True)
        return

    await state.update_data(chosen_plan_code=plan_code)
    await state.set_state(SubmitPaymentSG.waiting_for_proof)

    amount_str = f"{plan.price:,.0f}"

    text = i18n.get(
        "payment_instructions",
        lang=lang,
        plan_name=plan.name,
        amount=amount_str,
        card_number=settings.PAYMENT_CARD_NUMBER,
        card_holder=settings.PAYMENT_CARD_HOLDER,
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=get_payment_submit_keyboard(lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(SubmitPaymentSG.waiting_for_proof, F.photo)
async def handle_receipt_photo(message: Message, state: FSMContext, bot: Bot, db_user: User) -> None:
    """Handle uploaded photo receipt."""
    lang = db_user.language or "uz"
    data = await state.get_data()
    plan_code = data.get("chosen_plan_code", PlanType.PRO.value)

    # Highest resolution photo file_id
    photo = message.photo[-1]
    file_id = photo.file_id

    caption = message.caption or "Skrinshot"

    async with get_db_session() as session:
        pay_svc = PaymentService(session, bot=bot)
        await pay_svc.submit_payment_request(
            user_id=db_user.id,
            plan_code=plan_code,
            transaction_reference=caption,
            receipt_file_id=file_id,
        )

    await state.clear()
    await message.answer(i18n.get("payment_submitted", lang=lang), parse_mode="HTML")


@router.message(SubmitPaymentSG.waiting_for_proof, F.text)
async def handle_receipt_text(message: Message, state: FSMContext, bot: Bot, db_user: User) -> None:
    """Handle text transaction reference."""
    lang = db_user.language or "uz"
    data = await state.get_data()
    plan_code = data.get("chosen_plan_code", PlanType.PRO.value)
    ref = (message.text or "").strip()

    async with get_db_session() as session:
        pay_svc = PaymentService(session, bot=bot)
        await pay_svc.submit_payment_request(
            user_id=db_user.id,
            plan_code=plan_code,
            transaction_reference=ref,
            receipt_file_id=None,
        )

    await state.clear()
    await message.answer(i18n.get("payment_submitted", lang=lang), parse_mode="HTML")


@router.callback_query(F.data == "sub:cancel_payment")
async def handle_cancel_payment(callback: CallbackQuery, state: FSMContext, db_user: User) -> None:
    """Cancel payment flow."""
    await state.clear()
    lang = db_user.language or "uz"
    await callback.message.edit_text(i18n.get("operation_cancelled", lang=lang))
    await callback.answer()
