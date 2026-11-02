"""Payment repository for handling manual subscription payments."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.constants import PaymentStatus
from app.database.models.payment import Payment
from app.database.models.subscription import SubscriptionPlan
from app.database.models.user import User


class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_payment_request(
        self,
        user_id: int,
        plan_id: int,
        amount: Decimal,
        currency: str = "UZS",
        transaction_reference: str | None = None,
        receipt_file_id: str | None = None,
    ) -> Payment:
        """Create a new pending payment request."""
        payment = Payment(
            user_id=user_id,
            plan_id=plan_id,
            amount=amount,
            currency=currency,
            transaction_reference=transaction_reference,
            receipt_file_id=receipt_file_id,
            status=PaymentStatus.PENDING.value,
        )
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def get_by_id(self, payment_id: int) -> Payment | None:
        """Fetch payment by ID with user and plan loaded."""
        stmt = (
            select(Payment)
            .where(Payment.id == payment_id)
            .options(selectinload(Payment.user), selectinload(Payment.plan))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_pending_payments(self, limit: int = 20) -> list[Payment]:
        """Fetch list of pending payment requests for admin review."""
        stmt = (
            select(Payment)
            .where(Payment.status == PaymentStatus.PENDING.value)
            .options(selectinload(Payment.user), selectinload(Payment.plan))
            .order_by(Payment.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_pending_payments(self) -> int:
        """Count pending payment requests."""
        stmt = select(func.count(Payment.id)).where(Payment.status == PaymentStatus.PENDING.value)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def approve_payment(self, payment_id: int, admin_telegram_id: int) -> Payment | None:
        """Approve payment request atomically.
        Returns the updated Payment or None if payment not found or not in PENDING state.
        """
        payment = await self.get_by_id(payment_id)
        if not payment or payment.status != PaymentStatus.PENDING.value:
            return None

        payment.status = PaymentStatus.APPROVED.value
        payment.reviewed_by = admin_telegram_id
        payment.reviewed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return payment

    async def reject_payment(
        self,
        payment_id: int,
        admin_telegram_id: int,
        reason: str | None = None,
    ) -> Payment | None:
        """Reject payment request."""
        payment = await self.get_by_id(payment_id)
        if not payment or payment.status != PaymentStatus.PENDING.value:
            return None

        payment.status = PaymentStatus.REJECTED.value
        payment.reviewed_by = admin_telegram_id
        payment.reviewed_at = datetime.now(timezone.utc)
        payment.rejection_reason = reason or "Payment could not be verified."
        await self.session.flush()
        return payment
