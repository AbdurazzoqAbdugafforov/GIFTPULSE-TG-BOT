"""Portfolio and PortfolioPosition database models."""

from decimal import Decimal
from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base, TimestampMixin


class Portfolio(Base, TimestampMixin):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(64), default="Main Portfolio", nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="portfolios")
    positions: Mapped[list["PortfolioPosition"]] = relationship(
        "PortfolioPosition",
        back_populates="portfolio",
        cascade="all, delete-orphan",
    )


class PortfolioPosition(Base, TimestampMixin):
    __tablename__ = "portfolio_positions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("portfolios.id", ondelete="CASCADE"),
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
        ForeignKey("gift_models.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("1.0"), nullable=False)
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    purchase_date: Mapped[str | None] = mapped_column(String(10), nullable=True)  # YYYY-MM-DD
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="positions")
    collection: Mapped["GiftCollection"] = relationship("GiftCollection", back_populates="positions")
    model: Mapped["GiftModel | None"] = relationship("GiftModel", back_populates="positions")
