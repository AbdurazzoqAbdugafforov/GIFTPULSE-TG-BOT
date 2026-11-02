"""Watchlist service for managing tracked Gift collections."""

from decimal import Decimal
from typing import Any, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.constants import DATA_ATTRIBUTION_TEXT, DATA_ATTRIBUTION_URL
from app.database.models.collection import CollectionFloorSnapshot, GiftCollection
from app.database.models.watchlist import WatchlistEntry
from app.services.subscriptions.entitlement import SubscriptionEntitlement


class WatchlistService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.entitlement = SubscriptionEntitlement(session)

    async def add_to_watchlist(self, user_id: int, collection_id: int) -> tuple[bool, Optional[str]]:
        """Add a collection to user's watchlist subject to plan limits."""
        # 1. Check if already added
        stmt = select(WatchlistEntry).where(
            WatchlistEntry.user_id == user_id,
            WatchlistEntry.collection_id == collection_id,
        )
        res = await self.session.execute(stmt)
        if res.scalar_one_or_none():
            return True, None

        # 2. Check limits
        limits = await self.entitlement.get_user_limits(user_id)
        limit_val = limits.get("watchlist_limit", 5)

        count_stmt = select(WatchlistEntry).where(WatchlistEntry.user_id == user_id)
        count_res = await self.session.execute(count_stmt)
        current_count = len(count_res.scalars().all())

        if current_count >= limit_val:
            return False, f"Watchlist limit reached ({current_count}/{limit_val}). Upgrade to PRO or ELITE."

        entry = WatchlistEntry(user_id=user_id, collection_id=collection_id)
        self.session.add(entry)
        await self.session.commit()
        return True, None

    async def remove_from_watchlist(self, user_id: int, collection_id: int) -> bool:
        stmt = select(WatchlistEntry).where(
            WatchlistEntry.user_id == user_id,
            WatchlistEntry.collection_id == collection_id,
        )
        res = await self.session.execute(stmt)
        entry = res.scalar_one_or_none()
        if entry:
            await self.session.delete(entry)
            await self.session.commit()
            return True
        return False

    async def get_user_watchlist(self, user_id: int) -> list[dict[str, Any]]:
        """Fetch all collections in user's watchlist with current floors and 1d change."""
        stmt = (
            select(WatchlistEntry)
            .where(WatchlistEntry.user_id == user_id)
            .options(selectinload(WatchlistEntry.collection))
            .order_by(WatchlistEntry.created_at.desc())
        )
        res = await self.session.execute(stmt)
        entries = res.scalars().all()

        items = []
        for e in entries:
            col = e.collection
            if not col:
                continue

            # Fetch latest 2 snapshots
            snap_stmt = (
                select(CollectionFloorSnapshot)
                .where(CollectionFloorSnapshot.collection_id == col.id)
                .order_by(CollectionFloorSnapshot.observation_date.desc())
                .limit(2)
            )
            snaps = list((await self.session.execute(snap_stmt)).scalars().all())

            latest = snaps[0] if snaps else None
            prev = snaps[1] if len(snaps) > 1 else None

            c1d = 0.0
            if latest and prev and prev.floor_value > 0:
                c1d = float(round(((latest.floor_value - prev.floor_value) / prev.floor_value) * Decimal("100"), 2))

            items.append({
                "collection_id": col.id,
                "collection_slug": col.collection_slug,
                "collection_name": col.collection_name,
                "floor_gram": float(latest.floor_value) if latest else 0.0,
                "price_unit": "GRAM",
                "observation_date": latest.observation_date if latest else "N/A",
                "recent_sales": latest.recent_sales if latest else None,
                "change_1d_pct": c1d,
                "added_at": e.created_at.isoformat(),
            })

        return items
