"""User and settings repository."""

from datetime import datetime, timezone
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.constants import SupportedLanguage
from app.database.models.user import User
from app.database.models.settings import UserSettings
from app.database.models.watchlist import WatchlistEntry
from app.database.models.alert import Alert, AlertEvent
from app.database.models.portfolio import Portfolio, PortfolioPosition


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Fetch user by Telegram ID including settings."""
        stmt = (
            select(User)
            .where(User.telegram_id == telegram_id)
            .options(selectinload(User.settings))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        language: str = "uz",
        timezone_str: str = "Asia/Tashkent",
    ) -> tuple[User, bool]:
        """Fetch user or create new user with default settings."""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            # Update info if changed
            user.username = username
            user.first_name = first_name
            user.last_activity_at = datetime.now(timezone.utc)
            await self.session.flush()
            return user, False

        try:
            async with self.session.begin_nested():
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    language=language,
                    timezone=timezone_str,
                    is_active=True,
                )
                self.session.add(user)
                await self.session.flush()

                settings = UserSettings(
                    user_id=user.id,
                    daily_report_enabled=False,
                    daily_report_time="09:00",
                    notifications_enabled=True,
                    preferred_price_unit="GRAM",
                )
                self.session.add(settings)
                await self.session.flush()
                return user, True
        except Exception:
            existing = await self.get_by_telegram_id(telegram_id)
            if existing:
                return existing, False
            raise

    async def update_language(self, user_id: int, language: str) -> None:
        """Update user interface language."""
        stmt = update(User).where(User.id == user_id).values(language=language)
        await self.session.execute(stmt)

    async def update_timezone(self, user_id: int, tz_name: str) -> None:
        """Update user timezone."""
        stmt = update(User).where(User.id == user_id).values(timezone=tz_name)
        await self.session.execute(stmt)

    async def update_last_activity(self, telegram_id: int) -> None:
        """Update last activity timestamp."""
        stmt = (
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(last_activity_at=datetime.now(timezone.utc))
        )
        await self.session.execute(stmt)

    async def toggle_daily_report(self, user_id: int) -> bool:
        """Toggle daily report setting, returns new state."""
        stmt = select(UserSettings).where(UserSettings.user_id == user_id)
        result = await self.session.execute(stmt)
        settings = result.scalar_one_or_none()
        if not settings:
            settings = UserSettings(user_id=user_id, daily_report_enabled=True)
            self.session.add(settings)
            await self.session.flush()
            return True

        settings.daily_report_enabled = not settings.daily_report_enabled
        await self.session.flush()
        return settings.daily_report_enabled

    async def toggle_notifications(self, user_id: int) -> bool:
        """Toggle notifications setting, returns new state."""
        stmt = select(UserSettings).where(UserSettings.user_id == user_id)
        result = await self.session.execute(stmt)
        settings = result.scalar_one_or_none()
        if not settings:
            settings = UserSettings(user_id=user_id, notifications_enabled=True)
            self.session.add(settings)
            await self.session.flush()
            return True

        settings.notifications_enabled = not settings.notifications_enabled
        await self.session.flush()
        return settings.notifications_enabled

    async def delete_user_data(self, telegram_id: int) -> bool:
        """Delete all personal user data (cascade deletes alerts, positions, watchlist)."""
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            return False

        await self.session.delete(user)
        await self.session.flush()
        return True

    async def count_users(self) -> int:
        """Get total registered user count."""
        stmt = select(User.id)
        result = await self.session.execute(stmt)
        return len(result.all())
