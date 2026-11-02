"""Market data endpoints for Collections, Models, and GiftPulse Index."""

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.dependencies.auth import get_current_user
from app.database.models.user import User
from app.database.session import get_db_session
from app.services.collections.service import CollectionService
from app.services.gift_data.index_service import IndexService
from app.services.models.service import ModelService

router = APIRouter(prefix="/markets", tags=["Markets"])


@router.get("")
@router.get("/collections")
async def list_collections(
    search: Optional[str] = Query(None, description="Search collection name or slug"),
    sort_by: str = Query("floor_desc", description="floor_desc, floor_asc, change_1d_desc, change_1d_asc, name_asc"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Browse collections with latest floor prices, 24h & 7d changes."""
    async with get_db_session() as session:
        svc = CollectionService(session)
        return await svc.get_collections_overview(
            search=search,
            sort_by=sort_by,
            limit=limit,
            offset=offset,
        )


@router.get("/{slug}")
@router.get("/collections/{slug}")
async def get_collection_details(
    slug: str,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get collection details with complete historical chart observations."""
    async with get_db_session() as session:
        svc = CollectionService(session)
        col = await svc.get_collection_details(slug)
        if not col:
            raise HTTPException(status_code=404, detail="Collection not found")
        return col


@router.get("/{slug}/models")
@router.get("/collections/{slug}/models")
async def list_collection_models(
    slug: str,
    search: Optional[str] = Query(None),
    sort_by: str = Query("floor_desc", description="floor_desc, floor_asc, rarity_asc, rarity_desc, name_asc"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """List gift models in collection with floor prices and rarity percentages."""
    async with get_db_session() as session:
        svc = ModelService(session)
        return await svc.get_models_for_collection(
            collection_slug_or_id=slug,
            search=search,
            sort_by=sort_by,
            limit=limit,
            offset=offset,
        )


@router.get("/models/{model_id}")
async def get_model_details(
    model_id: int,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get single model details with history."""
    async with get_db_session() as session:
        svc = ModelService(session)
        model = await svc.get_model_details(model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        return model


@router.get("/index")
async def get_index_data(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get GiftPulse Index (GPI) latest value, series, and constituents."""
    async with get_db_session() as session:
        svc = IndexService(session)
        return await svc.get_index_overview()
