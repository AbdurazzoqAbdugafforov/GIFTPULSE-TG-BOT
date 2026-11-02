"""Alert and AlertEvent database models."""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.constants import AlertStatus, NotificationStatus
from app.database.models.base import Base, TimestampMixin, utc_now


class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    collection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("gift_collections.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    model_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("gift_models.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    alert_type: Mapped[str] = mapped_column(String(48), nullable=False)  # AlertType
    target_value: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    baseline_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default=AlertStatus.ACTIVE.value,
        index=True,
        nullable=False,
    )
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=86400, nullable=False)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_evaluated_snapshot: Mapped[str | None] = mapped_column(String(10), nullable=True)  # YYYY-MM-DD
    trigger_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="alerts")
    collection: Mapped["GiftCollection"] = relationship("GiftCollection", back_populates="alerts")
    model: Mapped["GiftModel | None"] = relationship("GiftModel", back_populates="alerts")
    events: Mapped[list["AlertEvent"]] = relationship(
        "AlertEvent",
        back_populates="alert",
        cascade="all, delete-orphan",
    )


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    alert_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("alerts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    observed_value: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    target_value: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    observation_date: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    deduplication_key: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    notification_status: Mapped[str] = mapped_column(
        String(20),
        default=NotificationStatus.PENDING.value,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    alert: Mapped["Alert"] = relationship("Alert", back_populates="events")
