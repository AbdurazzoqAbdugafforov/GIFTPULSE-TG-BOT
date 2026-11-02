"""Core constants for the GiftPulse application."""

from enum import Enum


class PlanType(str, Enum):
    FREE = "FREE"
    PRO = "PRO"
    ELITE = "ELITE"


class AlertType(str, Enum):
    # Collection-level alerts
    COLLECTION_FLOOR_ABOVE = "COLLECTION_FLOOR_ABOVE"
    COLLECTION_FLOOR_BELOW = "COLLECTION_FLOOR_BELOW"
    COLLECTION_FLOOR_PCT_UP = "COLLECTION_FLOOR_PCT_UP"
    COLLECTION_FLOOR_PCT_DOWN = "COLLECTION_FLOOR_PCT_DOWN"

    # Model-level alerts
    MODEL_FLOOR_ABOVE = "MODEL_FLOOR_ABOVE"
    MODEL_FLOOR_BELOW = "MODEL_FLOOR_BELOW"
    MODEL_FLOOR_PCT_CHANGE = "MODEL_FLOOR_PCT_CHANGE"


class AlertStatus(str, Enum):
    ACTIVE = "ACTIVE"
    TRIGGERED = "TRIGGERED"
    PAUSED = "PAUSED"
    DELETED = "DELETED"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


class SupportedLanguage(str, Enum):
    UZ = "uz"
    EN = "en"
    RU = "ru"


class DataFreshnessStatus(str, Enum):
    FRESH = "FRESH"
    DAILY_CURRENT = "DAILY_CURRENT"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"


REDIS_THROTTLE_KEY_PREFIX = "giftpulse:throttle:"

# GiftPulse Market Intelligence Data Constants
DATA_PROVIDER_NAME = "GiftPulse Intelligence"
DATA_ATTRIBUTION_TEXT = "GiftPulse Market Intelligence"
DATA_ATTRIBUTION_URL = ""
DATA_LICENSE = "GiftPulse Analytics Engine"

MARKET_DISCLAIMER = (
    "GiftPulse is an informational analytics application. "
    "It does not buy, sell, transfer, or trade Telegram Gifts. "
    "It does not promise profits, and estimates are not guaranteed market prices. "
    "Daily snapshots are historical daily records, not live marketplace listing events."
)

# Subscription default plan limits
DEFAULT_PLAN_LIMITS = {
    PlanType.FREE: {
        "alert_limit": 3,
        "watchlist_limit": 5,
        "model_alerts": False,
        "extended_charts": False,
        "advanced_radar": False,
        "portfolio_analytics": False,
        "daily_market_reports": False,
        "multiple_portfolios": False,
        "priority_support": False,
    },
    PlanType.PRO: {
        "alert_limit": 30,
        "watchlist_limit": 50,
        "model_alerts": True,
        "extended_charts": True,
        "advanced_radar": True,
        "portfolio_analytics": True,
        "daily_market_reports": True,
        "multiple_portfolios": False,
        "priority_support": False,
    },
    PlanType.ELITE: {
        "alert_limit": 200,
        "watchlist_limit": 200,
        "model_alerts": True,
        "extended_charts": True,
        "advanced_radar": True,
        "portfolio_analytics": True,
        "daily_market_reports": True,
        "multiple_portfolios": True,
        "priority_support": True,
    },
}
