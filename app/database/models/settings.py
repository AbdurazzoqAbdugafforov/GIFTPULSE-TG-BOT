"""User settings database model."""

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base, TimestampMixin


class UserSettings(Base, TimestampMixin):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    daily_report_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    daily_report_time: Mapped[str] = mapped_column(String(8), default="09:00", nullable=False)
    preferred_price_unit: Mapped[str] = mapped_column(String(10), default="GRAM", nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="settings")
