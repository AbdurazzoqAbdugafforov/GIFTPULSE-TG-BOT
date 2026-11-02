"""Market Radar API endpoint."""

from typing import Any
from fastapi import APIRouter, Depends
from app.api.dependencies.auth import get_current_user
from app.database.models.user import User
from app.database.session import get_db_session
from app.services.radar.service import RadarService

router = APIRouter(prefix="/radar", tags=["Radar"])


@router.get("")
async def get_market_radar(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Fetch market radar ranking top 1d/7d gainers, losers, and recent sales."""
    async with get_db_session() as session:
        svc = RadarService(session)
        return await svc.get_market_radar()
