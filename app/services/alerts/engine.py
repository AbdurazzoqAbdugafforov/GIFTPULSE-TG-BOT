"""Centralized Alert Engine evaluating daily snapshots and dispatching notifications."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.constants import AlertStatus, NotificationStatus, PlanType
from app.core.logging import logger
from app.database.models.alert import Alert, AlertEvent
from app.database.models.collection import CollectionFloorSnapshot, GiftCollection
from app.database.models.model_item import GiftModel, ModelFloorSnapshot
from app.database.models.user import User
from app.services.alerts.evaluator import AlertEvaluator
from app.services.alerts.notifier import AlertNotifier
from app.services.subscriptions.entitlement import SubscriptionEntitlement


class AlertEngine:
    def __init__(self, session: AsyncSession, notifier: Optional[AlertNotifier] = None):
        self.session = session
        self.notifier = notifier or AlertNotifier()
        self.entitlement = SubscriptionEntitlement(session)

    async def create_alert(
        self,
        user_id: int,
        collection_id: int,
        alert_type: str,
        target_value: Decimal,
        is_recurring: bool = False,
        model_id: Optional[int] = None,
        cooldown_seconds: int = 86400,
    ) -> tuple[Optional[Alert], Optional[str]]:
        """Create a new alert after validating subscription limits and plan entitlements."""
        # 1. Check user entitlement
        limits = await self.entitlement.get_user_limits(user_id)
        alert_limit = limits.get("alert_limit", 3)

        # Count active alerts
        stmt = select(Alert).where(Alert.user_id == user_id, Alert.status == AlertStatus.ACTIVE.value)
        res = await self.session.execute(stmt)
        active_count = len(res.scalars().all())

        if active_count >= alert_limit:
            return None, f"Alert limit reached ({active_count}/{alert_limit}). Upgrade to PRO or ELITE to create more alerts."

        if model_id is not None and not limits.get("model_alerts", False):
            return None, "Model-level alerts require a PRO or ELITE subscription."

        # 2. Determine current baseline value
        baseline_val = None
        if model_id:
            m_snap_stmt = (
                select(ModelFloorSnapshot)
                .where(ModelFloorSnapshot.model_id == model_id)
                .order_by(ModelFloorSnapshot.observation_date.desc())
                .limit(1)
            )
            m_res = await self.session.execute(m_snap_stmt)
            m_snap = m_res.scalar_one_or_none()
            if m_snap:
                baseline_val = m_snap.floor_value
        else:
            c_snap_stmt = (
                select(CollectionFloorSnapshot)
                .where(CollectionFloorSnapshot.collection_id == collection_id)
                .order_by(CollectionFloorSnapshot.observation_date.desc())
                .limit(1)
            )
            c_res = await self.session.execute(c_snap_stmt)
            c_snap = c_res.scalar_one_or_none()
            if c_snap:
                baseline_val = c_snap.floor_value

        alert = Alert(
            user_id=user_id,
            collection_id=collection_id,
            model_id=model_id,
            alert_type=alert_type,
            target_value=target_value,
            baseline_value=baseline_val,
            status=AlertStatus.ACTIVE.value,
            is_recurring=is_recurring,
            cooldown_seconds=cooldown_seconds,
        )
        self.session.add(alert)
        await self.session.flush()
        return alert, None

    async def evaluate_centralized_snapshots(self, observation_date: Optional[str] = None) -> int:
        """Centrally evaluate all active alerts against newly ingested daily observations.
        Returns total count of triggered alert events.
        """
        stmt = (
            select(Alert)
            .where(Alert.status == AlertStatus.ACTIVE.value)
            .options(
                selectinload(Alert.user),
                selectinload(Alert.collection),
                selectinload(Alert.model),
            )
        )
        res = await self.session.execute(stmt)
        alerts = list(res.scalars().all())

        if not alerts:
            return 0

        triggered_count = 0
        now = datetime.now(timezone.utc)

        for alert in alerts:
            # 1. Obtain current and previous observation
            current_obs = None
            prev_obs = None
            obs_date_str = ""

            if alert.model_id:
                m_stmt = (
                    select(ModelFloorSnapshot)
                    .where(ModelFloorSnapshot.model_id == alert.model_id)
                    .order_by(ModelFloorSnapshot.observation_date.desc())
                    .limit(2)
                )
                m_snaps = list((await self.session.execute(m_stmt)).scalars().all())
                if m_snaps:
                    current_obs = m_snaps[0].floor_value
                    obs_date_str = m_snaps[0].observation_date
                    if len(m_snaps) > 1:
                        prev_obs = m_snaps[1].floor_value
            else:
                c_stmt = (
                    select(CollectionFloorSnapshot)
                    .where(CollectionFloorSnapshot.collection_id == alert.collection_id)
                    .order_by(CollectionFloorSnapshot.observation_date.desc())
                    .limit(2)
                )
                c_snaps = list((await self.session.execute(c_stmt)).scalars().all())
                if c_snaps:
                    current_obs = c_snaps[0].floor_value
                    obs_date_str = c_snaps[0].observation_date
                    if len(c_snaps) > 1:
                        prev_obs = c_snaps[1].floor_value

            if current_obs is None:
                continue

            # Prior reference value
            reference_prev = prev_obs if prev_obs is not None else alert.baseline_value

            # Evaluate crossing
            should_trigger, event_type, new_baseline = AlertEvaluator.evaluate_daily_snapshot(
                alert=alert,
                observed_value=current_obs,
                previous_observed_value=reference_prev,
                observation_date=obs_date_str,
                now=now,
            )

            # Update baseline if re-armed
            if new_baseline is not None:
                alert.baseline_value = new_baseline

            # Mark snapshot as evaluated to avoid redundant work
            alert.last_evaluated_snapshot = obs_date_str

            if should_trigger:
                # Idempotency key per alert event: alert_id + observation_date + target_value
                dedup_key = f"evt_{alert.id}_{obs_date_str}_{alert.target_value}"
                
                # Check duplicate
                dup_stmt = select(AlertEvent).where(AlertEvent.deduplication_key == dedup_key)
                existing_evt = (await self.session.execute(dup_stmt)).scalar_one_or_none()

                if not existing_evt:
                    event = AlertEvent(
                        alert_id=alert.id,
                        user_id=alert.user_id,
                        observed_value=current_obs,
                        target_value=alert.target_value,
                        observation_date=obs_date_str,
                        deduplication_key=dedup_key,
                        notification_status=NotificationStatus.PENDING.value,
                    )
                    self.session.add(event)
                    await self.session.flush()

                    # Update alert state
                    alert.trigger_count += 1
                    alert.last_triggered_at = now

                    if not alert.is_recurring:
                        alert.status = AlertStatus.TRIGGERED.value
                    else:
                        alert.baseline_value = current_obs

                    # Deliver notification via Telegram
                    if alert.user and alert.collection:
                        await self.notifier.send_alert_notification(
                            alert=alert,
                            event=event,
                            collection=alert.collection,
                            model=alert.model,
                            user=alert.user,
                        )

                    triggered_count += 1

        await self.session.commit()
        return triggered_count

    async def get_user_alerts(self, user_id: int) -> list[dict]:
        """Fetch all alerts for a user with collection and model details."""
        stmt = (
            select(Alert)
            .where(Alert.user_id == user_id, Alert.status != AlertStatus.DELETED.value)
            .options(selectinload(Alert.collection), selectinload(Alert.model))
            .order_by(Alert.created_at.desc())
        )
        res = await self.session.execute(stmt)
        alerts = res.scalars().all()

        return [
            {
                "id": a.id,
                "collection_id": a.collection_id,
                "collection_name": a.collection.collection_name if a.collection else "",
                "collection_slug": a.collection.collection_slug if a.collection else "",
                "model_id": a.model_id,
                "model_name": a.model.model_name if a.model else None,
                "alert_type": a.alert_type,
                "target_value": float(a.target_value),
                "baseline_value": float(a.baseline_value) if a.baseline_value is not None else None,
                "status": a.status,
                "is_recurring": a.is_recurring,
                "trigger_count": a.trigger_count,
                "last_triggered_at": a.last_triggered_at.isoformat() if a.last_triggered_at else None,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alerts
        ]

    async def pause_alert(self, alert_id: int, user_id: int) -> bool:
        stmt = select(Alert).where(Alert.id == alert_id, Alert.user_id == user_id)
        alert = (await self.session.execute(stmt)).scalar_one_or_none()
        if alert and alert.status == AlertStatus.ACTIVE.value:
            alert.status = AlertStatus.PAUSED.value
            await self.session.commit()
            return True
        return False

    async def resume_alert(self, alert_id: int, user_id: int) -> bool:
        stmt = select(Alert).where(Alert.id == alert_id, Alert.user_id == user_id)
        alert = (await self.session.execute(stmt)).scalar_one_or_none()
        if alert and alert.status == AlertStatus.PAUSED.value:
            alert.status = AlertStatus.ACTIVE.value
            await self.session.commit()
            return True
        return False

    async def delete_alert(self, alert_id: int, user_id: int) -> bool:
        stmt = select(Alert).where(Alert.id == alert_id, Alert.user_id == user_id)
        alert = (await self.session.execute(stmt)).scalar_one_or_none()
        if alert:
            alert.status = AlertStatus.DELETED.value
            await self.session.commit()
            return True
        return False
