"""Model service for GiftPulse models and rarity analytics."""

from decimal import Decimal
from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.constants import DATA_ATTRIBUTION_TEXT, DATA_ATTRIBUTION_URL, DATA_LICENSE
from app.database.models.collection import GiftCollection
from app.database.models.model_item import GiftModel, ModelFloorSnapshot


class ModelService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_models_for_collection(
        self,
        collection_slug_or_id: str | int,
        search: Optional[str] = None,
        sort_by: str = "floor_desc",  # floor_desc, floor_asc, rarity_asc, rarity_desc, name_asc
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Fetch models for a collection with latest floor, rarity permille/pct, and listings."""
        # Find collection
        stmt = select(GiftCollection)
        if isinstance(collection_slug_or_id, int) or (isinstance(collection_slug_or_id, str) and collection_slug_or_id.isdigit()):
            stmt = stmt.where(GiftCollection.id == int(collection_slug_or_id))
        else:
            stmt = stmt.where(GiftCollection.collection_slug == str(collection_slug_or_id).lower())

        c_res = await self.session.execute(stmt)
        col = c_res.scalar_one_or_none()
        if not col:
            return {"items": [], "total": 0, "collection": None}

        # Query models
        m_query = select(GiftModel).where(GiftModel.collection_id == col.id)
        if search:
            m_query = m_query.where(GiftModel.model_name.ilike(f"%{search}%"))

        m_res = await self.session.execute(m_query)
        models = list(m_res.scalars().all())

        if not models:
            return {
                "items": [],
                "total": 0,
                "collection": {"id": col.id, "slug": col.collection_slug, "name": col.collection_name},
                "attribution": DATA_ATTRIBUTION_TEXT,
            }

        m_ids = [m.id for m in models]
        snap_stmt = (
            select(ModelFloorSnapshot)
            .where(ModelFloorSnapshot.model_id.in_(m_ids))
            .order_by(ModelFloorSnapshot.observation_date.desc())
        )
        snap_res = await self.session.execute(snap_stmt)
        all_snaps = snap_res.scalars().all()

        snaps_by_model: dict[int, list[ModelFloorSnapshot]] = {}
        for s in all_snaps:
            snaps_by_model.setdefault(s.model_id, []).append(s)

        items = []
        for m in models:
            snaps = snaps_by_model.get(m.id, [])
            if not snaps:
                continue

            latest = snaps[0]
            prev = snaps[1] if len(snaps) > 1 else None

            change_1d_pct = None
            if prev and prev.floor_value > 0:
                change_1d_pct = round(
                    ((latest.floor_value - prev.floor_value) / prev.floor_value) * Decimal("100"), 2
                )

            # Rarity permille to percentage: percentage = rarity_permille / 10
            rarity_permille = float(latest.rarity_permille) if latest.rarity_permille is not None else None
            rarity_pct = round(rarity_permille / 10.0, 2) if rarity_permille is not None else None

            items.append({
                "id": m.id,
                "collection_id": col.id,
                "collection_slug": col.collection_slug,
                "collection_name": col.collection_name,
                "name": m.model_name,
                "slug": m.model_slug,
                "floor_gram": float(latest.floor_value),
                "price_unit": "GRAM",
                "rarity_permille": rarity_permille,
                "rarity_pct": rarity_pct,
                "buy_now_listings": latest.buy_now_listings,
                "observation_date": latest.observation_date,
                "change_1d_pct": float(change_1d_pct) if change_1d_pct is not None else 0.0,
                "history_points_count": len(snaps),
            })

        # Sorting
        if sort_by == "floor_desc":
            items.sort(key=lambda x: x["floor_gram"], reverse=True)
        elif sort_by == "floor_asc":
            items.sort(key=lambda x: x["floor_gram"])
        elif sort_by == "rarity_asc":
            # Lowest rarity percentage first (rarest)
            items.sort(key=lambda x: (x["rarity_pct"] is None, x["rarity_pct"]))
        elif sort_by == "rarity_desc":
            items.sort(key=lambda x: (x["rarity_pct"] is None, x["rarity_pct"]), reverse=True)
        elif sort_by == "name_asc":
            items.sort(key=lambda x: x["name"].lower())

        total = len(items)
        paginated_items = items[offset : offset + limit]

        return {
            "collection": {"id": col.id, "slug": col.collection_slug, "name": col.collection_name},
            "items": paginated_items,
            "total": total,
            "attribution": DATA_ATTRIBUTION_TEXT,
            "attribution_url": DATA_ATTRIBUTION_URL,
            "license": DATA_LICENSE,
        }

    async def get_model_details(self, model_id: int) -> Optional[dict[str, Any]]:
        """Fetch model details with full historical trend."""
        stmt = select(GiftModel).where(GiftModel.id == model_id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        if not model:
            return None

        # Fetch collection
        c_stmt = select(GiftCollection).where(GiftCollection.id == model.collection_id)
        c_res = await self.session.execute(c_stmt)
        col = c_res.scalar_one_or_none()

        snap_stmt = (
            select(ModelFloorSnapshot)
            .where(ModelFloorSnapshot.model_id == model.id)
            .order_by(ModelFloorSnapshot.observation_date.asc())
        )
        snap_res = await self.session.execute(snap_stmt)
        snaps = list(snap_res.scalars().all())

        if not snaps:
            return {
                "id": model.id,
                "name": model.model_name,
                "history": [],
                "attribution": DATA_ATTRIBUTION_TEXT,
                "attribution_url": DATA_ATTRIBUTION_URL,
            }

        latest = snaps[-1]
        prev = snaps[-2] if len(snaps) >= 2 else None

        change_1d_pct = None
        if prev and prev.floor_value > 0:
            change_1d_pct = round(
                ((latest.floor_value - prev.floor_value) / prev.floor_value) * Decimal("100"), 2
            )

        rarity_permille = float(latest.rarity_permille) if latest.rarity_permille is not None else None
        rarity_pct = round(rarity_permille / 10.0, 2) if rarity_permille is not None else None

        history_chart = [
            {
                "date": s.observation_date,
                "floor_gram": float(s.floor_value),
                "buy_now_listings": s.buy_now_listings,
            }
            for s in snaps
        ]

        return {
            "id": model.id,
            "collection_id": col.id if col else None,
            "collection_slug": col.collection_slug if col else "",
            "collection_name": col.collection_name if col else "",
            "name": model.model_name,
            "slug": model.model_slug,
            "floor_gram": float(latest.floor_value),
            "price_unit": "GRAM",
            "rarity_permille": rarity_permille,
            "rarity_pct": rarity_pct,
            "buy_now_listings": latest.buy_now_listings,
            "observation_date": latest.observation_date,
            "change_1d_pct": float(change_1d_pct) if change_1d_pct is not None else 0.0,
            "history": history_chart,
            "attribution": DATA_ATTRIBUTION_TEXT,
            "attribution_url": DATA_ATTRIBUTION_URL,
            "license": DATA_LICENSE,
        }
