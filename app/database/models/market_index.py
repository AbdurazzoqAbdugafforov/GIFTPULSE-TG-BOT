"""MarketIndexSnapshot database model."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from sqlalchemy import DateTime, Integer, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database.models.base import Base, utc_now


class MarketIndexSnapshot(Base):
    __tablename__ = "market_index_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    observation_date: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)  # YYYY-MM-DD
    index_value: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    change_pct: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    constituents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    constituents_data: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    source: Mapped[str] = mapped_column(
        String(128),
        default="GiftPulse Market Intelligence",
        nullable=False,
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
