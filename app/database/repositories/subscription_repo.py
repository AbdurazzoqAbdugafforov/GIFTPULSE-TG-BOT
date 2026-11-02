"""Subscription and SubscriptionPlan repository."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.config import settings
from app.core.constants import DEFAULT_PLAN_LIMITS, PlanType
from app.database.models.subscription import Subscription, SubscriptionPlan


class SubscriptionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_plan_by_code(self, code: str) -> SubscriptionPlan | None:
        """Fetch subscription plan by its unique code (FREE, PRO, ELITE)."""
        stmt = select(SubscriptionPlan).where(SubscriptionPlan.code == code.upper())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_plans(self) -> list[SubscriptionPlan]:
        """Fetch all plans."""
        stmt = select(SubscriptionPlan).order_by(SubscriptionPlan.price.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_subscription(self, user_id: int) -> Subscription | None:
        """Fetch currently active subscription for user.
        If subscription has expired, marks it EXPIRED and returns None.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(Subscription)
            .where(Subscription.user_id == user_id, Subscription.status == "ACTIVE")
            .options(selectinload(Subscription.plan))
            .order_by(Subscription.created_at.desc())
        )
        result = await self.session.execute(stmt)
        subs = result.scalars().all()

        for sub in subs:
            if sub.expires_at is not None:
                expires_at = sub.expires_at
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                if expires_at < now:
                    sub.status = "EXPIRED"
                    await self.session.flush()
                else:
                    return sub
            else:
                return sub

        return None

    async def activate_subscription(
        self,
        user_id: int,
        plan_id: int,
        duration_days: int = 30,
    ) -> Subscription:
        """Activate subscription for user, retiring any prior active subscription."""
        now = datetime.now(timezone.utc)
        # Retain previous active subscriptions by marking them UPGRADED/SUPERSEDED
        stmt = (
            update(Subscription)
            .where(Subscription.user_id == user_id, Subscription.status == "ACTIVE")
            .values(status="SUPERSEDED")
        )
        await self.session.execute(stmt)

        expires_at = now + timedelta(days=duration_days) if duration_days > 0 else None

        sub = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            status="ACTIVE",
            starts_at=now,
            expires_at=expires_at,
        )
        self.session.add(sub)
        await self.session.flush()
        return sub

    async def seed_default_plans(self) -> None:
        """Seed default FREE, PRO, and ELITE subscription plans if not existing."""
        plans_data = [
            {
                "code": PlanType.FREE.value,
                "name": "FREE Plan",
                "price": Decimal("0.00"),
                "currency": "UZS",
                "duration_days": 3650,  # Permanent free
                "alert_limit": DEFAULT_PLAN_LIMITS[PlanType.FREE]["alert_limit"],
                "watchlist_limit": DEFAULT_PLAN_LIMITS[PlanType.FREE]["watchlist_limit"],
                "feature_permissions": DEFAULT_PLAN_LIMITS[PlanType.FREE],
                "is_active": True,
            },
            {
                "code": PlanType.PRO.value,
                "name": "PRO Plan",
                "price": Decimal(str(settings.PRO_PLAN_PRICE)),
                "currency": "UZS",
                "duration_days": 30,
                "alert_limit": DEFAULT_PLAN_LIMITS[PlanType.PRO]["alert_limit"],
                "watchlist_limit": DEFAULT_PLAN_LIMITS[PlanType.PRO]["watchlist_limit"],
                "feature_permissions": DEFAULT_PLAN_LIMITS[PlanType.PRO],
                "is_active": True,
            },
            {
                "code": PlanType.ELITE.value,
                "name": "ELITE Plan",
                "price": Decimal(str(settings.ELITE_PLAN_PRICE)),
                "currency": "UZS",
                "duration_days": 30,
                "alert_limit": DEFAULT_PLAN_LIMITS[PlanType.ELITE]["alert_limit"],
                "watchlist_limit": DEFAULT_PLAN_LIMITS[PlanType.ELITE]["watchlist_limit"],
                "feature_permissions": DEFAULT_PLAN_LIMITS[PlanType.ELITE],
                "is_active": True,
            },
        ]

        for p_data in plans_data:
            existing = await self.get_plan_by_code(p_data["code"])
            if not existing:
                plan = SubscriptionPlan(**p_data)
                self.session.add(plan)
        await self.session.flush()

    async def update_plan_price(self, code: str, new_price: Decimal) -> bool:
        """Update price of a plan in database."""
        stmt = (
            update(SubscriptionPlan)
            .where(SubscriptionPlan.code == code.upper())
            .values(price=new_price)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def update_plan_limits(
        self,
        code: str,
        alert_limit: int,
        watchlist_limit: int,
    ) -> bool:
        """Update alert and watchlist limits of a plan."""
        stmt = (
            update(SubscriptionPlan)
            .where(SubscriptionPlan.code == code.upper())
            .values(alert_limit=alert_limit, watchlist_limit=watchlist_limit)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
