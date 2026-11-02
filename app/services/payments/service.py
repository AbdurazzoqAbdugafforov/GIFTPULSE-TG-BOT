"""Payment service handling manual verification, admin notifications, and activation."""

from decimal import Decimal
from typing import Optional
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.logging import logger
from app.database.models.payment import Payment
from app.database.repositories.audit_repo import AuditRepository
from app.database.repositories.payment_repo import PaymentRepository
from app.database.repositories.subscription_repo import SubscriptionRepository
from app.database.repositories.user_repo import UserRepository
from app.localization.i18n import i18n


class PaymentService:
    """Manages the lifecycle of manual transfer subscription requests."""

    def __init__(self, session: AsyncSession, bot: Optional[Bot] = None):
        self.session = session
        self.bot = bot
        self.payment_repo = PaymentRepository(session)
        self.sub_repo = SubscriptionRepository(session)
        self.audit_repo = AuditRepository(session)
        self.user_repo = UserRepository(session)

    async def submit_payment_request(
        self,
        user_id: int,
        plan_code: str,
        transaction_reference: Optional[str] = None,
        receipt_file_id: Optional[str] = None,
    ) -> Payment:
        """Create pending payment record and alert authorized administrators."""
        plan = await self.sub_repo.get_plan_by_code(plan_code)
        if not plan:
            raise ValueError(f"Plan {plan_code} not found.")

        payment = await self.payment_repo.create_payment_request(
            user_id=user_id,
            plan_id=plan.id,
            amount=plan.price,
            currency=plan.currency,
            transaction_reference=transaction_reference,
            receipt_file_id=receipt_file_id,
        )

        # Notify admins
        if self.bot and settings.ADMIN_IDS:
            admin_text = (
                f"💰 <b>Yangi To'lov So'rovi #{payment.id}</b>\n\n"
                f"👤 <b>Foydalanuvchi ID:</b> <code>{user_id}</code>\n"
                f"💎 <b>Tarif:</b> {plan.name} ({plan.code})\n"
                f"💵 <b>Summa:</b> {payment.amount:,.0f} {payment.currency}\n"
                f"🧾 <b>Chek/Ref:</b> <code>{transaction_reference or 'Fayl biriktirilgan'}</code>\n"
            )

            admin_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Tasdiqlash",
                            callback_data=f"admin:pay:approve:{payment.id}",
                        ),
                        InlineKeyboardButton(
                            text="❌ Rad etish",
                            callback_data=f"admin:pay:reject:{payment.id}",
                        ),
                    ]
                ]
            )

            for admin_id in settings.ADMIN_IDS:
                try:
                    if receipt_file_id:
                        await self.bot.send_photo(
                            chat_id=admin_id,
                            photo=receipt_file_id,
                            caption=admin_text,
                            parse_mode="HTML",
                            reply_markup=admin_kb,
                        )
                    else:
                        await self.bot.send_message(
                            chat_id=admin_id,
                            text=admin_text,
                            parse_mode="HTML",
                            reply_markup=admin_kb,
                        )
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id} about payment #{payment.id}: {e}")

        return payment

    async def approve_payment(self, payment_id: int, admin_telegram_id: int) -> bool:
        """Approve payment, activate 30-day subscription, and notify user."""
        payment = await self.payment_repo.approve_payment(payment_id, admin_telegram_id)
        if not payment:
            return False

        # Activate subscription
        await self.sub_repo.activate_subscription(
            user_id=payment.user_id,
            plan_id=payment.plan_id,
            duration_days=payment.plan.duration_days,
        )

        # Audit log
        await self.audit_repo.log_action(
            actor_telegram_id=admin_telegram_id,
            action="PAYMENT_APPROVED",
            target_type="payment",
            target_id=payment.id,
            metadata={
                "user_id": payment.user_id,
                "plan_code": payment.plan.code,
                "amount": str(payment.amount),
            },
        )

        # Notify user
        if self.bot and payment.user:
            lang = payment.user.language or "uz"
            msg = (
                f"🎉 <b>To'lov tasdiqlandi!</b>\n\n"
                f"Sizning <b>{payment.plan.name}</b> obunangiz 30 kunga faollashtirildi.\n"
                f"GiftPulse imkoniyatlaridan unumli foydalaning!"
                if lang == "uz"
                else f"🎉 <b>Payment approved!</b>\n\nYour <b>{payment.plan.name}</b> plan has been activated for 30 days."
            )
            try:
                await self.bot.send_message(
                    chat_id=payment.user.telegram_id,
                    text=msg,
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.warning(f"Could not deliver payment approval notification to user: {e}")

        return True

    async def reject_payment(
        self,
        payment_id: int,
        admin_telegram_id: int,
        reason: Optional[str] = None,
    ) -> bool:
        """Reject payment and notify user."""
        payment = await self.payment_repo.reject_payment(payment_id, admin_telegram_id, reason)
        if not payment:
            return False

        await self.audit_repo.log_action(
            actor_telegram_id=admin_telegram_id,
            action="PAYMENT_REJECTED",
            target_type="payment",
            target_id=payment.id,
            metadata={"reason": reason or "Unverified"},
        )

        if self.bot and payment.user:
            lang = payment.user.language or "uz"
            msg = (
                f"❌ <b>To'lov rad etildi.</b>\n\n"
                f"Sabab: {payment.rejection_reason}\n"
                f"Agar savollaringiz bo'lsa, adminga murojaat qiling."
                if lang == "uz"
                else f"❌ <b>Payment rejected.</b>\n\nReason: {payment.rejection_reason}"
            )
            try:
                await self.bot.send_message(
                    chat_id=payment.user.telegram_id,
                    text=msg,
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.warning(f"Could not deliver rejection notification: {e}")

        return True
