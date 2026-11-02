"""Watchlist API endpoints for Telegram Mini App."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.api.dependencies.auth import get_current_user
from app.database.models.user import User
from app.database.session import get_db_session
from app.services.watchlist.service import WatchlistService

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


class AddWatchlistRequest(BaseModel):
    collection_id: int


@router.get("")
async def get_watchlist(current_user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
    """Fetch user's tracked collections with latest floor prices and 24h change."""
    async with get_db_session() as session:
        svc = WatchlistService(session)
        return await svc.get_user_watchlist(current_user.id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    payload: AddWatchlistRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Add collection to user's watchlist."""
    async with get_db_session() as session:
        svc = WatchlistService(session)
        success, err = await svc.add_to_watchlist(current_user.id, payload.collection_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
        return {"status": "ADDED"}


@router.delete("/{collection_id}")
async def remove_from_watchlist(
    collection_id: int,
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Remove collection from watchlist."""
    async with get_db_session() as session:
        svc = WatchlistService(session)
        success = await svc.remove_from_watchlist(current_user.id, collection_id)
        if not success:
            raise HTTPException(status_code=404, detail="Collection not in watchlist")
        return {"status": "REMOVED"}
