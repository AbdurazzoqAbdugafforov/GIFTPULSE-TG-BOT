"""GiftCollection and CollectionFloorSnapshot database models."""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
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
from app.database.models.base import Base, TimestampMixin, utc_now


class GiftCollection(Base, TimestampMixin):
    __tablename__ = "gift_collections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    collection_slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    collection_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    snapshots: Mapped[list["CollectionFloorSnapshot"]] = relationship(
        "CollectionFloorSnapshot",
        back_populates="collection",
        cascade="all, delete-orphan",
        order_by="desc(CollectionFloorSnapshot.observation_date)",
    )
    models: Mapped[list["GiftModel"]] = relationship(
        "GiftModel",
        back_populates="collection",
        cascade="all, delete-orphan",
    )
    watchlist_entries: Mapped[list["WatchlistEntry"]] = relationship(
        "WatchlistEntry",
        back_populates="collection",
        cascade="all, delete-orphan",
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="collection",
        cascade="all, delete-orphan",
    )
    positions: Mapped[list["PortfolioPosition"]] = relationship(
        "PortfolioPosition",
        back_populates="collection",
    )


class CollectionFloorSnapshot(Base):
    __tablename__ = "collection_floor_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    collection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("gift_collections.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    observation_date: Mapped[str] = mapped_column(String(10), index=True, nullable=False)  # YYYY-MM-DD
    floor_value: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    recent_sales: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str] = mapped_column(
        String(128),
        default="GiftPulse Market Intelligence",
        nullable=False,
    )
    source_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    data_confidence: Mapped[str] = mapped_column(String(32), default="CONFIRMED", nullable=False)

    collection: Mapped["GiftCollection"] = relationship("GiftCollection", back_populates="snapshots")

    __table_args__ = (
        UniqueConstraint(
            "collection_id",
            "observation_date",
            name="uq_collection_floor_observation",
        ),
        Index("ix_coll_floor_obs_date", "collection_id", "observation_date"),
    )
