"""Subscription and payment REST API endpoints."""

from decimal import Decimal
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.api.dependencies.auth import get_current_user
from app.core.config import settings
from app.database.models.user import User
from app.database.repositories.subscription_repo import SubscriptionRepository
from app.database.session import get_db_session
from app.services.payments.service import PaymentService
from app.services.subscriptions.entitlement import EntitlementService

router = APIRouter(prefix="/subscription", tags=["Subscription"])


class SubmitPaymentPayload(BaseModel):
    plan_code: str = Field(..., description="PRO or ELITE")
    transaction_reference: str = Field(..., min_length=3, description="Bank receipt reference or note")


@router.get("")
async def get_subscription_details(user: User = Depends(get_current_user)) -> Any:
    """Return user active plan and all subscription tiers."""
    async with get_db_session() as session:
        ent = EntitlementService(session)
        user_plan = await ent.get_user_plan(user.id)
        sub_repo = SubscriptionRepository(session)
        all_plans = await sub_repo.get_all_plans()

    tiers = []
    for p in all_plans:
        tiers.append({
            "code": p.code,
            "name": p.name,
            "price": str(p.price),
            "currency": p.currency,
            "duration_days": p.duration_days,
            "alert_limit": p.alert_limit,
            "watchlist_limit": p.watchlist_limit,
            "features": p.feature_permissions or {},
        })

    return {
        "current_plan": {
            "code": user_plan.code,
            "name": user_plan.name,
            "alert_limit": user_plan.alert_limit,
            "watchlist_limit": user_plan.watchlist_limit,
            "expires_at": user_plan.expires_at.isoformat() if user_plan.expires_at else None,
        },
        "available_plans": tiers,
        "payment_instructions": {
            "card_number": settings.PAYMENT_CARD_NUMBER,
            "card_holder": settings.PAYMENT_CARD_HOLDER,
        },
    }


@router.post("/payment", status_code=status.HTTP_201_CREATED)
async def submit_payment(
    body: SubmitPaymentPayload,
    user: User = Depends(get_current_user),
) -> Any:
    """Submit a manual payment verification request from the Mini App."""
    async with get_db_session() as session:
        pay_svc = PaymentService(session, bot=None)
        try:
            payment = await pay_svc.submit_payment_request(
                user_id=user.id,
                plan_code=body.plan_code.upper(),
                transaction_reference=body.transaction_reference,
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "id": payment.id,
        "status": payment.status,
        "amount": str(payment.amount),
        "currency": payment.currency,
        "message": "Payment submitted for administrator review.",
    }
