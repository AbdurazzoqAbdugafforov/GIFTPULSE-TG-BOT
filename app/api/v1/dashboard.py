"""Dashboard overview endpoint for Telegram Mini App."""

from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from app.api.dependencies.auth import get_current_user
from app.core.constants import DATA_ATTRIBUTION_TEXT, DATA_ATTRIBUTION_URL, DATA_LICENSE
from app.database.models.alert import Alert
from app.database.models.user import User
from app.database.models.watchlist import WatchlistEntry
from app.database.session import get_db_session
from app.services.collections.service import CollectionService
from app.services.gift_data.cache import cache_manager
from app.services.gift_data.index_service import IndexService
from app.services.radar.service import RadarService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("")
async def get_dashboard_data(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Fetch aggregated dashboard data for the Mini App home view."""
    async with get_db_session() as session:
        # Index summary
        idx_svc = IndexService(session)
        idx_data = await idx_svc.get_index_overview()

        # Popular collections
        coll_svc = CollectionService(session)
        coll_overview = await coll_svc.get_collections_overview(sort_by="floor_desc", limit=5)

        # Radar summary
        radar_svc = RadarService(session)
        radar_data = await radar_svc.get_market_radar()

        # User active alerts count
        alert_stmt = select(func.count(Alert.id)).where(
            Alert.user_id == current_user.id,
            Alert.status == "ACTIVE",
        )
        active_alerts_count = (await session.execute(alert_stmt)).scalar() or 0

        # User watchlist count
        wl_stmt = select(func.count(WatchlistEntry.id)).where(
            WatchlistEntry.user_id == current_user.id
        )
        watchlist_count = (await session.execute(wl_stmt)).scalar() or 0

    # Ingestion status from cache
    ingestion_status = await cache_manager.get_json("giftpulse:ingestion:status") or {}

    return {
        "index": {
            "name": idx_data.get("name", "GiftPulse Index"),
            "symbol": idx_data.get("symbol", "GPI"),
            "value": idx_data.get("latest_value", 100.0),
            "change_1d_pct": idx_data.get("change_1d_pct", 0.0),
            "change_7d_pct": idx_data.get("change_7d_pct", 0.0),
            "observation_date": idx_data.get("latest_date", "N/A"),
        },
        "popular_collections": coll_overview.get("items", []),
        "top_gainers_1d": radar_data.get("top_gainers_1d", [])[:3],
        "top_losers_1d": radar_data.get("top_losers_1d", [])[:3],
        "active_alerts_count": active_alerts_count,
        "watchlist_count": watchlist_count,
        "data_freshness": ingestion_status.get("data_freshness", "DAILY_CURRENT"),
        "latest_observation_date": ingestion_status.get("latest_observation_date", idx_data.get("latest_date")),
        "attribution": DATA_ATTRIBUTION_TEXT,
        "attribution_url": DATA_ATTRIBUTION_URL,
        "license": DATA_LICENSE,
    }
