"""Alert condition evaluation engine for GiftPulse daily snapshots."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Tuple
from app.core.constants import AlertStatus, AlertType
from app.database.models.alert import Alert


class AlertEvaluator:
    """Evaluates whether a Gift floor alert condition is genuinely met based on daily snapshots."""

    @staticmethod
    def evaluate_daily_snapshot(
        alert: Alert,
        observed_value: Decimal,
        previous_observed_value: Optional[Decimal] = None,
        observation_date: str = "",
        now: Optional[datetime] = None,
    ) -> Tuple[bool, Optional[str], Optional[Decimal]]:
        """Evaluate if newly observed daily floor triggers the alert.
        
        Returns:
            (should_trigger, event_type, new_baseline_if_rearmed)
        """
        if alert.status != AlertStatus.ACTIVE.value:
            return False, None, None

        # Never evaluate the exact same observation date twice
        if alert.last_evaluated_snapshot == observation_date and observation_date:
            return False, None, None

        if now is None:
            now = datetime.now(timezone.utc)

        # Cooldown check for recurring alerts
        if alert.last_triggered_at is not None:
            elapsed = (now - alert.last_triggered_at).total_seconds()
            if elapsed < alert.cooldown_seconds:
                return False, None, None

        prior_value = previous_observed_value if previous_observed_value is not None else alert.baseline_value
        target = alert.target_value

        # --- COLLECTION_FLOOR_ABOVE & MODEL_FLOOR_ABOVE ---
        if alert.alert_type in (AlertType.COLLECTION_FLOOR_ABOVE.value, AlertType.MODEL_FLOOR_ABOVE.value):
            if observed_value < target:
                # Floor fell below target: re-arm recurring alert baseline
                if prior_value is None or prior_value >= target:
                    return False, None, observed_value
                return False, None, None

            # Observed value >= target
            if prior_value is not None and prior_value < target and observed_value >= target:
                return True, "FLOOR_CROSSED_ABOVE", observed_value
            return False, None, None

        # --- COLLECTION_FLOOR_BELOW & MODEL_FLOOR_BELOW ---
        if alert.alert_type in (AlertType.COLLECTION_FLOOR_BELOW.value, AlertType.MODEL_FLOOR_BELOW.value):
            if observed_value > target:
                # Floor rose above target: re-arm
                if prior_value is None or prior_value <= target:
                    return False, None, observed_value
                return False, None, None

            # Observed value <= target
            if prior_value is not None and prior_value > target and observed_value <= target:
                return True, "FLOOR_CROSSED_BELOW", observed_value
            return False, None, None

        # --- COLLECTION_FLOOR_PCT_UP ---
        if alert.alert_type == AlertType.COLLECTION_FLOOR_PCT_UP.value:
            if prior_value is not None and prior_value > 0:
                pct_change = ((observed_value - prior_value) / prior_value) * Decimal("100")
                if pct_change >= target:
                    return True, "FLOOR_PCT_UP", observed_value
            return False, None, None

        # --- COLLECTION_FLOOR_PCT_DOWN ---
        if alert.alert_type == AlertType.COLLECTION_FLOOR_PCT_DOWN.value:
            if prior_value is not None and prior_value > 0:
                pct_change = ((observed_value - prior_value) / prior_value) * Decimal("100")
                # e.g. target is 10 (meaning 10% decrease) or -10
                threshold = -abs(target)
                if pct_change <= threshold:
                    return True, "FLOOR_PCT_DOWN", observed_value
            return False, None, None

        # --- MODEL_FLOOR_PCT_CHANGE ---
        if alert.alert_type == AlertType.MODEL_FLOOR_PCT_CHANGE.value:
            if prior_value is not None and prior_value > 0:
                pct_change = abs(((observed_value - prior_value) / prior_value) * Decimal("100"))
                if pct_change >= abs(target):
                    return True, "MODEL_FLOOR_PCT_CHANGE", observed_value
            return False, None, None

        return False, None, None
