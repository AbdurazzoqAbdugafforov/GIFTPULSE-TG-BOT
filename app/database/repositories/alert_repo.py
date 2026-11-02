"""Alert and AlertEvent repository for GiftPulse."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.constants import AlertStatus, NotificationStatus
from app.database.models.alert import Alert, AlertEvent


class AlertRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_alert(
        self,
        user_id: int,
        collection_id: int,
        alert_type: str,
        target_value: Decimal,
        baseline_value: Decimal | None = None,
        model_id: int | None = None,
        is_recurring: bool = False,
        cooldown_seconds: int = 86400,
    ) -> Alert:
        """Create and activate a new alert."""
        alert = Alert(
            user_id=user_id,
            collection_id=collection_id,
            model_id=model_id,
            alert_type=alert_type,
            target_value=target_value,
            baseline_value=baseline_value,
            status=AlertStatus.ACTIVE.value,
            is_recurring=is_recurring,
            cooldown_seconds=cooldown_seconds,
            trigger_count=0,
        )
        self.session.add(alert)
        await self.session.flush()
        return alert

    async def get_by_id(self, alert_id: int, user_id: int | None = None) -> Alert | None:
        """Fetch alert by ID, optionally scoped to a user."""
        stmt = (
            select(Alert)
            .where(Alert.id == alert_id)
            .options(
                selectinload(Alert.user),
                selectinload(Alert.collection),
                selectinload(Alert.model),
            )
        )
        if user_id is not None:
            stmt = stmt.where(Alert.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_alerts(self, user_id: int, status: str | None = None) -> list[Alert]:
        """Fetch alerts belonging to user, optionally filtered by status."""
        stmt = (
            select(Alert)
            .where(Alert.user_id == user_id)
            .options(
                selectinload(Alert.collection),
                selectinload(Alert.model),
            )
            .order_by(Alert.created_at.desc())
        )
        if status:
            stmt = stmt.where(Alert.status == status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def pause_alert(self, alert_id: int, user_id: int) -> bool:
        stmt = (
            update(Alert)
            .where(Alert.id == alert_id, Alert.user_id == user_id)
            .values(status=AlertStatus.PAUSED.value)
        )
        res = await self.session.execute(stmt)
        await self.session.flush()
        return res.rowcount > 0

    async def resume_alert(self, alert_id: int, user_id: int) -> bool:
        stmt = (
            update(Alert)
            .where(Alert.id == alert_id, Alert.user_id == user_id)
            .values(status=AlertStatus.ACTIVE.value)
        )
        res = await self.session.execute(stmt)
        await self.session.flush()
        return res.rowcount > 0

    async def delete_alert(self, alert_id: int, user_id: int) -> bool:
        stmt = delete(Alert).where(Alert.id == alert_id, Alert.user_id == user_id)
        res = await self.session.execute(stmt)
        await self.session.flush()
        return res.rowcount > 0
