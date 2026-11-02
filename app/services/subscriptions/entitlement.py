"""Centralized Entitlement and Subscription limits engine for GiftPulse."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.constants import DEFAULT_PLAN_LIMITS, PlanType
from app.database.models.alert import Alert
from app.database.models.subscription import SubscriptionPlan
from app.database.models.watchlist import WatchlistEntry
from app.database.repositories.subscription_repo import SubscriptionRepository


@dataclass
class UserPlanInfo:
    code: str
    name: str
    alert_limit: int
    watchlist_limit: int
    expires_at: Optional[datetime]
    features: dict[str, Any]


class SubscriptionEntitlement:
    """Authoritative service checking resource limits and plan permissions."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.sub_repo = SubscriptionRepository(session)

    async def get_user_plan(self, user_id: int) -> UserPlanInfo:
        """Resolve current active plan for user, falling back to FREE if none or expired."""
        sub = await self.sub_repo.get_active_subscription(user_id)
        if sub and sub.plan:
            plan = sub.plan
            features = dict(plan.feature_permissions or {})
            return UserPlanInfo(
                code=plan.code,
                name=plan.name,
                alert_limit=plan.alert_limit,
                watchlist_limit=plan.watchlist_limit,
                expires_at=sub.expires_at,
                features=features,
            )

        # Fallback to FREE plan from database
        free_plan = await self.sub_repo.get_plan_by_code(PlanType.FREE.value)
        if free_plan:
            features = dict(free_plan.feature_permissions or {})
            return UserPlanInfo(
                code=free_plan.code,
                name=free_plan.name,
                alert_limit=free_plan.alert_limit,
                watchlist_limit=free_plan.watchlist_limit,
                expires_at=None,
                features=features,
            )

        # Fallback default constants
        defaults = DEFAULT_PLAN_LIMITS[PlanType.FREE]
        return UserPlanInfo(
            code=PlanType.FREE.value,
            name="FREE Plan",
            alert_limit=defaults["alert_limit"],
            watchlist_limit=defaults["watchlist_limit"],
            expires_at=None,
            features=defaults,
        )

    async def get_user_limits(self, user_id: int) -> dict[str, Any]:
        """Return full capability dictionary for user."""
        plan_info = await self.get_user_plan(user_id)
        limits = {
            "plan_code": plan_info.code,
            "plan_name": plan_info.name,
            "expires_at": plan_info.expires_at.isoformat() if plan_info.expires_at else None,
            "alert_limit": plan_info.alert_limit,
            "watchlist_limit": plan_info.watchlist_limit,
        }
        limits.update(plan_info.features)
        return limits

    async def can_create_alert(self, user_id: int, is_model_alert: bool = False) -> tuple[bool, Optional[str]]:
        plan = await self.get_user_plan(user_id)
        if is_model_alert and not plan.features.get("model_alerts", False):
            return False, "Model-level alerts require a PRO or ELITE plan."

        # Count active alerts
        stmt = select(Alert).where(Alert.user_id == user_id, Alert.status == "ACTIVE")
        res = await self.session.execute(stmt)
        active_count = len(res.scalars().all())

        if active_count >= plan.alert_limit:
            return False, f"Alert limit reached ({active_count}/{plan.alert_limit}). Upgrade your plan to add more."
        return True, None

    async def can_add_to_watchlist(self, user_id: int) -> tuple[bool, Optional[str]]:
        plan = await self.get_user_plan(user_id)
        stmt = select(WatchlistEntry).where(WatchlistEntry.user_id == user_id)
        res = await self.session.execute(stmt)
        current_count = len(res.scalars().all())

        if current_count >= plan.watchlist_limit:
            return False, f"Watchlist limit reached ({current_count}/{plan.watchlist_limit}). Upgrade your plan to track more collections."
        return True, None


# Alias for compatibility
EntitlementService = SubscriptionEntitlement
