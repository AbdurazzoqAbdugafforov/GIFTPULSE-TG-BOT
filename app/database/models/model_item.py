"""GiftModel and ModelFloorSnapshot database models."""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
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


class GiftModel(Base, TimestampMixin):
    __tablename__ = "gift_models"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    collection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("gift_collections.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    model_slug: Mapped[str | None] = mapped_column(String(128), nullable=True)

    collection: Mapped["GiftCollection"] = relationship("GiftCollection", back_populates="models")
    snapshots: Mapped[list["ModelFloorSnapshot"]] = relationship(
        "ModelFloorSnapshot",
        back_populates="model",
        cascade="all, delete-orphan",
        order_by="desc(ModelFloorSnapshot.observation_date)",
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="model",
        cascade="all, delete-orphan",
    )
    positions: Mapped[list["PortfolioPosition"]] = relationship(
        "PortfolioPosition",
        back_populates="model",
    )

    __table_args__ = (
        UniqueConstraint("collection_id", "model_name", name="uq_model_collection_name"),
    )


class ModelFloorSnapshot(Base):
    __tablename__ = "model_floor_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    model_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("gift_models.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    observation_date: Mapped[str] = mapped_column(String(10), index=True, nullable=False)  # YYYY-MM-DD
    floor_value: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    rarity_permille: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    buy_now_listings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    model: Mapped["GiftModel"] = relationship("GiftModel", back_populates="snapshots")

    __table_args__ = (
        UniqueConstraint("model_id", "observation_date", name="uq_model_floor_observation"),
        Index("ix_model_floor_obs_date", "model_id", "observation_date"),
    )
