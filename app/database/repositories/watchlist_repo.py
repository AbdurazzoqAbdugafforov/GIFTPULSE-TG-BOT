"""Watchlist repository for GiftPulse."""

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database.models.watchlist import WatchlistEntry


class WatchlistRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_entries(self, user_id: int) -> list[WatchlistEntry]:
        """Fetch list of all collection entries saved by user."""
        stmt = (
            select(WatchlistEntry)
            .where(WatchlistEntry.user_id == user_id)
            .options(selectinload(WatchlistEntry.collection))
            .order_by(WatchlistEntry.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_user_entries(self, user_id: int) -> int:
        """Count how many collections user has in watchlist."""
        stmt = select(func.count(WatchlistEntry.id)).where(WatchlistEntry.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def is_in_watchlist(self, user_id: int, collection_id: int) -> bool:
        """Check if collection is already in user watchlist."""
        stmt = (
            select(WatchlistEntry.id)
            .where(WatchlistEntry.user_id == user_id, WatchlistEntry.collection_id == collection_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def add_collection(self, user_id: int, collection_id: int) -> bool:
        """Add collection to watchlist. Returns True if added, False if already present."""
        if await self.is_in_watchlist(user_id, collection_id):
            return False
        entry = WatchlistEntry(user_id=user_id, collection_id=collection_id)
        self.session.add(entry)
        await self.session.flush()
        return True

    async def remove_collection(self, user_id: int, collection_id: int) -> bool:
        """Remove collection from watchlist. Returns True if deleted."""
        stmt = (
            delete(WatchlistEntry)
            .where(WatchlistEntry.user_id == user_id, WatchlistEntry.collection_id == collection_id)
        )
        res = await self.session.execute(stmt)
        await self.session.flush()
        return res.rowcount > 0
