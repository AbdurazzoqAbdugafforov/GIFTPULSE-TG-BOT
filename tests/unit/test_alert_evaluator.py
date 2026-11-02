"""Unit tests for GiftPulse Alert Evaluator engine (TG Gifts daily snapshots)."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from app.core.constants import AlertStatus, AlertType
from app.database.models.alert import Alert
from app.services.alerts.evaluator import AlertEvaluator


def create_gift_alert(
    alert_type: str,
    target_value: Decimal,
    baseline_value: Decimal | None = None,
    collection_id: int = 1,
    model_id: int | None = None,
    is_recurring: bool = False,
    cooldown_seconds: int = 300,
    status: str = AlertStatus.ACTIVE.value,
    last_triggered_at: datetime | None = None,
    last_evaluated_snapshot: str | None = None,
) -> Alert:
    return Alert(
        id=1,
        user_id=10,
        collection_id=collection_id,
        model_id=model_id,
        alert_type=alert_type,
        target_value=target_value,
        baseline_value=baseline_value,
        status=status,
        is_recurring=is_recurring,
        cooldown_seconds=cooldown_seconds,
        last_triggered_at=last_triggered_at,
        last_evaluated_snapshot=last_evaluated_snapshot,
        trigger_count=0,
    )


def test_collection_floor_crosses_above_target():
    """Trigger when collection floor moves from strictly below target to >= target."""
    alert = create_gift_alert(
        alert_type=AlertType.COLLECTION_FLOOR_ABOVE.value,
        target_value=Decimal("150.0"),
        baseline_value=Decimal("140.0"),
    )
    triggered, event_type, new_base = AlertEvaluator.evaluate_daily_snapshot(
        alert=alert,
        observed_value=Decimal("155.0"),
        previous_observed_value=Decimal("140.0"),
        observation_date="2026-11-01",
    )
    assert triggered is True
    assert event_type == "FLOOR_CROSSED_ABOVE"
    assert new_base == Decimal("155.0")


def test_collection_floor_already_above_does_not_retrigger():
    """No trigger if previous observed value was already >= target."""
    alert = create_gift_alert(
        alert_type=AlertType.COLLECTION_FLOOR_ABOVE.value,
        target_value=Decimal("150.0"),
        baseline_value=Decimal("152.0"),
    )
    triggered, event_type, _ = AlertEvaluator.evaluate_daily_snapshot(
        alert=alert,
        observed_value=Decimal("160.0"),
        previous_observed_value=Decimal("152.0"),
        observation_date="2026-11-02",
    )
    assert triggered is False
    assert event_type is None


def test_collection_floor_falls_below_rearms_baseline():
    """When floor drops below target, alert baseline is updated to re-arm future crossing."""
    alert = create_gift_alert(
        alert_type=AlertType.COLLECTION_FLOOR_ABOVE.value,
        target_value=Decimal("150.0"),
        baseline_value=Decimal("155.0"),
    )
    triggered, event_type, new_base = AlertEvaluator.evaluate_daily_snapshot(
        alert=alert,
        observed_value=Decimal("142.0"),
        previous_observed_value=Decimal("155.0"),
        observation_date="2026-11-03",
    )
    assert triggered is False
    assert new_base == Decimal("142.0")


def test_collection_floor_crosses_below_target():
    """Trigger when collection floor moves from strictly above target to <= target."""
    alert = create_gift_alert(
        alert_type=AlertType.COLLECTION_FLOOR_BELOW.value,
        target_value=Decimal("100.0"),
        baseline_value=Decimal("110.0"),
    )
    triggered, event_type, new_base = AlertEvaluator.evaluate_daily_snapshot(
        alert=alert,
        observed_value=Decimal("95.0"),
        previous_observed_value=Decimal("105.0"),
        observation_date="2026-11-01",
    )
    assert triggered is True
    assert event_type == "FLOOR_CROSSED_BELOW"
    assert new_base == Decimal("95.0")


def test_collection_floor_pct_up():
    """Trigger when daily percentage increase >= target percentage."""
    alert = create_gift_alert(
        alert_type=AlertType.COLLECTION_FLOOR_PCT_UP.value,
        target_value=Decimal("10.0"),  # +10%
        baseline_value=Decimal("100.0"),
    )
    # Price rises from 100 to 112 (+12%)
    triggered, event_type, _ = AlertEvaluator.evaluate_daily_snapshot(
        alert=alert,
        observed_value=Decimal("112.0"),
        previous_observed_value=Decimal("100.0"),
        observation_date="2026-11-01",
    )
    assert triggered is True
    assert event_type == "FLOOR_PCT_UP"

    # Price rises only +5% (from 100 to 105) -> No trigger
    triggered, _, _ = AlertEvaluator.evaluate_daily_snapshot(
        alert=alert,
        observed_value=Decimal("105.0"),
        previous_observed_value=Decimal("100.0"),
        observation_date="2026-11-02",
    )
    assert triggered is False


def test_collection_floor_pct_down():
    """Trigger when daily percentage decrease <= -target percentage."""
    alert = create_gift_alert(
        alert_type=AlertType.COLLECTION_FLOOR_PCT_DOWN.value,
        target_value=Decimal("15.0"),  # -15%
        baseline_value=Decimal("200.0"),
    )
    # Floor drops from 200 to 160 (-20%)
    triggered, event_type, _ = AlertEvaluator.evaluate_daily_snapshot(
        alert=alert,
        observed_value=Decimal("160.0"),
        previous_observed_value=Decimal("200.0"),
        observation_date="2026-11-01",
    )
    assert triggered is True
    assert event_type == "FLOOR_PCT_DOWN"


def test_model_floor_pct_change():
    """Model floor percent change triggers in either direction."""
    alert = create_gift_alert(
        alert_type=AlertType.MODEL_FLOOR_PCT_CHANGE.value,
        target_value=Decimal("25.0"),
        model_id=5,
    )
    # +30% movement
    triggered, event_type, _ = AlertEvaluator.evaluate_daily_snapshot(
        alert=alert,
        observed_value=Decimal("130.0"),
        previous_observed_value=Decimal("100.0"),
        observation_date="2026-11-01",
    )
    assert triggered is True
    assert event_type == "MODEL_FLOOR_PCT_CHANGE"

    # -28% movement
    triggered, event_type, _ = AlertEvaluator.evaluate_daily_snapshot(
        alert=alert,
        observed_value=Decimal("72.0"),
        previous_observed_value=Decimal("100.0"),
        observation_date="2026-11-02",
    )
    assert triggered is True


def test_same_observation_date_ignored():
    """Alert must not re-evaluate the exact same observation date."""
    alert = create_gift_alert(
        alert_type=AlertType.COLLECTION_FLOOR_ABOVE.value,
        target_value=Decimal("100.0"),
        baseline_value=Decimal("90.0"),
        last_evaluated_snapshot="2026-11-01",
    )
    triggered, _, _ = AlertEvaluator.evaluate_daily_snapshot(
        alert=alert,
        observed_value=Decimal("120.0"),
        observation_date="2026-11-01",
    )
    assert triggered is False


def test_paused_alert_never_triggers():
    alert = create_gift_alert(
        alert_type=AlertType.COLLECTION_FLOOR_ABOVE.value,
        target_value=Decimal("100.0"),
        baseline_value=Decimal("90.0"),
        status=AlertStatus.PAUSED.value,
    )
    triggered, _, _ = AlertEvaluator.evaluate_daily_snapshot(
        alert=alert,
        observed_value=Decimal("120.0"),
        observation_date="2026-11-01",
    )
    assert triggered is False


def test_cooldown_prevents_immediate_retrigger():
    now = datetime.now(timezone.utc)
    alert = create_gift_alert(
        alert_type=AlertType.COLLECTION_FLOOR_ABOVE.value,
        target_value=Decimal("100.0"),
        baseline_value=Decimal("90.0"),
        is_recurring=True,
        cooldown_seconds=3600,
        last_triggered_at=now - timedelta(seconds=600),  # Only 10 minutes ago
    )
    triggered, _, _ = AlertEvaluator.evaluate_daily_snapshot(
        alert=alert,
        observed_value=Decimal("120.0"),
        previous_observed_value=Decimal("95.0"),
        observation_date="2026-11-02",
        now=now,
    )
    assert triggered is False
