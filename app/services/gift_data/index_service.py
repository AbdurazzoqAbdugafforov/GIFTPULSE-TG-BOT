"""Index service for TG Gifts Index (TGGI) analytics."""

from decimal import Decimal
from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.constants import DATA_ATTRIBUTION_TEXT, DATA_ATTRIBUTION_URL, DATA_LICENSE
from app.database.models.market_index import MarketIndexSnapshot
from app.services.gift_data.cache import cache_manager


class IndexService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_index_overview(self) -> dict[str, Any]:
        """Fetch latest index snapshot, historical series, and constituents."""
        # 1. Try cache first
        cached = await cache_manager.get_json("giftpulse:index:latest")
        if cached:
            return cached

        # 2. Query database
        stmt = (
            select(MarketIndexSnapshot)
            .order_by(MarketIndexSnapshot.observation_date.desc())
            .limit(90)
        )
        res = await self.session.execute(stmt)
        snapshots = list(res.scalars().all())

        if not snapshots:
            return {
                "name": "GiftPulse Index",
                "symbol": "GPI",
                "latest_value": 100.0,
                "latest_date": "N/A",
                "change_1d_pct": 0.0,
                "change_7d_pct": 0.0,
                "constituents_count": 0,
                "series": [],
                "constituents": [],
                "attribution": DATA_ATTRIBUTION_TEXT,
                "attribution_url": DATA_ATTRIBUTION_URL,
                "license": DATA_LICENSE,
            }

        latest = snapshots[0]
        prev_7d = snapshots[7] if len(snapshots) > 7 else (snapshots[-1] if len(snapshots) > 1 else None)
        c7d = 0.0
        if prev_7d and prev_7d.index_value > 0:
            c7d = float(round(((latest.index_value - prev_7d.index_value) / prev_7d.index_value) * Decimal("100"), 2))

        # Sort series ascending for chart
        series_points = [
            {
                "date": s.observation_date,
                "value": float(s.index_value),
                "change_pct": float(s.change_pct) if s.change_pct is not None else 0.0,
                "constituents": s.constituents,
            }
            for s in reversed(snapshots)
        ]

        result = {
            "name": "GiftPulse Index",
            "symbol": "GPI",
            "method_version": "1.0",
            "unit": "index points",
            "source": "GiftPulse Market Intelligence",
            "license": DATA_LICENSE,
            "latest_value": float(latest.index_value),
            "latest_date": latest.observation_date,
            "change_1d_pct": float(latest.change_pct) if latest.change_pct is not None else 0.0,
            "change_7d_pct": c7d,
            "constituents_count": latest.constituents or 0,
            "series": series_points,
            "constituents": latest.constituents_data or [],
            "attribution": DATA_ATTRIBUTION_TEXT,
            "attribution_url": DATA_ATTRIBUTION_URL,
        }

        # Cache for 15 mins
        await cache_manager.set_json("giftpulse:index:latest", result, ttl=900)
        return result
