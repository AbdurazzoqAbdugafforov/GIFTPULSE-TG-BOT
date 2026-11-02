"""Market Radar analytics service for GiftPulse."""

from decimal import Decimal
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.constants import DATA_ATTRIBUTION_TEXT, DATA_ATTRIBUTION_URL, DATA_LICENSE, MARKET_DISCLAIMER
from app.services.collections.service import CollectionService
from app.services.gift_data.cache import cache_manager
from app.services.gift_data.index_service import IndexService


class RadarService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.coll_svc = CollectionService(session)
        self.index_svc = IndexService(session)

    async def get_market_radar(self) -> dict[str, Any]:
        """Generate comprehensive market radar analytics based on recorded daily observations."""
        cached = await cache_manager.get_json("giftpulse:radar:summary")
        if cached:
            return cached

        # Fetch all collections overview
        overview = await self.coll_svc.get_collections_overview(limit=300)
        items = overview.get("items", [])

        # Filter out items with valid changes
        valid_1d = [it for it in items if it.get("change_1d_pct") is not None]
        valid_7d = [it for it in items if it.get("change_7d_pct") is not None]

        # 1. Top 1D Gainers and Losers
        sorted_1d = sorted(valid_1d, key=lambda x: x["change_1d_pct"], reverse=True)
        top_gainers_1d = [x for x in sorted_1d if x["change_1d_pct"] > 0][:5]
        top_losers_1d = [x for x in reversed(sorted_1d) if x["change_1d_pct"] < 0][:5]

        # 2. Top 7D Gainers and Losers
        sorted_7d = sorted(valid_7d, key=lambda x: x["change_7d_pct"], reverse=True)
        top_gainers_7d = [x for x in sorted_7d if x["change_7d_pct"] > 0][:5]
        top_losers_7d = [x for x in reversed(sorted_7d) if x["change_7d_pct"] < 0][:5]

        # 3. Collections with notable recent sales activity
        sales_active = [it for it in items if it.get("recent_sales") and str(it["recent_sales"]) not in ("0", "None")]
        # Sort by recent sales if numeric or "60+"
        def sales_sort_key(item: dict) -> int:
            val = str(item.get("recent_sales", "0")).replace("+", "").strip()
            return int(val) if val.isdigit() else 0
        sales_active.sort(key=sales_sort_key, reverse=True)
        top_active_sales = sales_active[:5]

        # 4. Fetch index overview for market sentiment
        index_data = await self.index_svc.get_index_overview()

        radar_data = {
            "top_gainers_1d": top_gainers_1d,
            "top_losers_1d": top_losers_1d,
            "top_gainers_7d": top_gainers_7d,
            "top_losers_7d": top_losers_7d,
            "active_sales_collections": top_active_sales,
            "index_summary": {
                "value": index_data.get("latest_value"),
                "change_1d_pct": index_data.get("change_1d_pct"),
                "change_7d_pct": index_data.get("change_7d_pct"),
                "date": index_data.get("latest_date"),
            },
            "disclaimer": MARKET_DISCLAIMER,
            "attribution": DATA_ATTRIBUTION_TEXT,
            "attribution_url": DATA_ATTRIBUTION_URL,
            "license": DATA_LICENSE,
        }

        # Cache for 10 minutes
        await cache_manager.set_json("giftpulse:radar:summary", radar_data, ttl=600)
        return radar_data
