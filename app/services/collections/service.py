"""Collection service for GiftPulse market analytics."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.constants import DATA_ATTRIBUTION_TEXT, DATA_ATTRIBUTION_URL, DATA_LICENSE
from app.database.models.collection import CollectionFloorSnapshot, GiftCollection
from app.services.gift_data.cache import cache_manager


class CollectionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_collections_overview(
        self,
        search: Optional[str] = None,
        sort_by: str = "floor_desc",  # floor_desc, floor_asc, change_1d_desc, change_1d_asc, name_asc
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Fetch collections with latest floor price and 1d/7d percentage changes."""
        # 1. Base query for collections
        query = select(GiftCollection).where(GiftCollection.is_active == True)
        if search:
            query = query.where(
                (GiftCollection.collection_name.ilike(f"%{search}%"))
                | (GiftCollection.collection_slug.ilike(f"%{search}%"))
            )

        res = await self.session.execute(query)
        collections = list(res.scalars().all())

        if not collections:
            return {"items": [], "total": 0, "attribution": DATA_ATTRIBUTION_TEXT}

        col_ids = [c.id for c in collections]

        # 2. Fetch recent snapshots for all collections
        snap_stmt = (
            select(CollectionFloorSnapshot)
            .where(CollectionFloorSnapshot.collection_id.in_(col_ids))
            .order_by(CollectionFloorSnapshot.observation_date.desc())
        )
        snap_res = await self.session.execute(snap_stmt)
        all_snaps = snap_res.scalars().all()

        snaps_by_col: dict[int, list[CollectionFloorSnapshot]] = {}
        for s in all_snaps:
            snaps_by_col.setdefault(s.collection_id, []).append(s)

        items = []
        for col in collections:
            snaps = snaps_by_col.get(col.id, [])
            if not snaps:
                continue

            latest = snaps[0]
            prev_1d = snaps[1] if len(snaps) > 1 else None
            prev_7d = snaps[7] if len(snaps) > 7 else (snaps[-1] if len(snaps) > 1 else None)

            change_1d_pct = None
            if prev_1d and prev_1d.floor_value > 0:
                change_1d_pct = round(
                    ((latest.floor_value - prev_1d.floor_value) / prev_1d.floor_value) * Decimal("100"),
                    2,
                )

            change_7d_pct = None
            if prev_7d and prev_7d.floor_value > 0:
                change_7d_pct = round(
                    ((latest.floor_value - prev_7d.floor_value) / prev_7d.floor_value) * Decimal("100"),
                    2,
                )

            items.append({
                "id": col.id,
                "slug": col.collection_slug,
                "name": col.collection_name,
                "floor_gram": float(latest.floor_value),
                "price_unit": "GRAM",
                "observation_date": latest.observation_date,
                "recent_sales": latest.recent_sales,
                "change_1d_pct": float(change_1d_pct) if change_1d_pct is not None else 0.0,
                "change_7d_pct": float(change_7d_pct) if change_7d_pct is not None else 0.0,
                "history_points_count": len(snaps),
            })

        # 3. Sorting
        if sort_by == "floor_desc":
            items.sort(key=lambda x: x["floor_gram"], reverse=True)
        elif sort_by == "floor_asc":
            items.sort(key=lambda x: x["floor_gram"])
        elif sort_by == "change_1d_desc":
            items.sort(key=lambda x: x["change_1d_pct"], reverse=True)
        elif sort_by == "change_1d_asc":
            items.sort(key=lambda x: x["change_1d_pct"])
        elif sort_by == "name_asc":
            items.sort(key=lambda x: x["name"].lower())

        total = len(items)
        paginated_items = items[offset : offset + limit]

        return {
            "items": paginated_items,
            "total": total,
            "attribution": DATA_ATTRIBUTION_TEXT,
            "attribution_url": DATA_ATTRIBUTION_URL,
            "license": DATA_LICENSE,
        }

    async def get_collection_details(self, slug_or_id: str | int) -> Optional[dict[str, Any]]:
        """Fetch in-depth collection details with complete historical chart data."""
        stmt = select(GiftCollection)
        if isinstance(slug_or_id, int) or (isinstance(slug_or_id, str) and slug_or_id.isdigit()):
            stmt = stmt.where(GiftCollection.id == int(slug_or_id))
        else:
            stmt = stmt.where(GiftCollection.collection_slug == str(slug_or_id).lower())

        res = await self.session.execute(stmt)
        col = res.scalar_one_or_none()
        if not col:
            return None

        # Fetch snapshots ordered by date ascending for charts
        snap_stmt = (
            select(CollectionFloorSnapshot)
            .where(CollectionFloorSnapshot.collection_id == col.id)
            .order_by(CollectionFloorSnapshot.observation_date.asc())
        )
        snap_res = await self.session.execute(snap_stmt)
        snaps = list(snap_res.scalars().all())

        if not snaps:
            return {
                "id": col.id,
                "slug": col.collection_slug,
                "name": col.collection_name,
                "floor_gram": None,
                "history": [],
                "attribution": DATA_ATTRIBUTION_TEXT,
                "attribution_url": DATA_ATTRIBUTION_URL,
            }

        latest = snaps[-1]
        prev_1d = snaps[-2] if len(snaps) >= 2 else None
        prev_7d = snaps[-8] if len(snaps) >= 8 else (snaps[0] if len(snaps) > 1 else None)

        change_1d_pct = None
        if prev_1d and prev_1d.floor_value > 0:
            change_1d_pct = round(
                ((latest.floor_value - prev_1d.floor_value) / prev_1d.floor_value) * Decimal("100"), 2
            )

        change_7d_pct = None
        if prev_7d and prev_7d.floor_value > 0:
            change_7d_pct = round(
                ((latest.floor_value - prev_7d.floor_value) / prev_7d.floor_value) * Decimal("100"), 2
            )

        history_chart = [
            {
                "date": s.observation_date,
                "floor_gram": float(s.floor_value),
                "recent_sales": s.recent_sales,
            }
            for s in snaps
        ]

        return {
            "id": col.id,
            "slug": col.collection_slug,
            "name": col.collection_name,
            "floor_gram": float(latest.floor_value),
            "price_unit": "GRAM",
            "observation_date": latest.observation_date,
            "recent_sales": latest.recent_sales,
            "change_1d_pct": float(change_1d_pct) if change_1d_pct is not None else 0.0,
            "change_7d_pct": float(change_7d_pct) if change_7d_pct is not None else 0.0,
            "source": latest.source,
            "data_confidence": latest.data_confidence,
            "history": history_chart,
            "attribution": DATA_ATTRIBUTION_TEXT,
            "attribution_url": DATA_ATTRIBUTION_URL,
            "license": DATA_LICENSE,
        }
