"""Portfolio API endpoints for Telegram Mini App."""

from decimal import Decimal
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.api.dependencies.auth import get_current_user
from app.database.models.user import User
from app.database.session import get_db_session
from app.services.portfolio.service import PortfolioService

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


class AddPositionRequest(BaseModel):
    collection_id: int
    model_id: Optional[int] = None
    quantity: Decimal = Field(default=Decimal("1.0"), gt=0)
    purchase_price: Decimal = Field(..., gt=0)
    purchase_date: Optional[str] = None
    notes: Optional[str] = None


@router.get("")
async def get_portfolio_summary(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Calculate portfolio estimated value, profit/loss, and asset allocation."""
    async with get_db_session() as session:
        svc = PortfolioService(session)
        return await svc.calculate_summary(current_user.id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_portfolio_position(
    payload: AddPositionRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Add a gift holding to personal portfolio."""
    async with get_db_session() as session:
        svc = PortfolioService(session)
        port = await svc.get_or_create_default_portfolio(current_user.id)
        pos = await svc.add_position(
            portfolio_id=port.id,
            collection_id=payload.collection_id,
            model_id=payload.model_id,
            quantity=payload.quantity,
            purchase_price=payload.purchase_price,
            purchase_date=payload.purchase_date,
            notes=payload.notes,
        )
        return {
            "id": pos.id,
            "portfolio_id": pos.portfolio_id,
            "collection_id": pos.collection_id,
            "model_id": pos.model_id,
            "quantity": float(pos.quantity),
            "purchase_price": float(pos.purchase_price),
        }


@router.delete("/{position_id}")
async def delete_portfolio_position(
    position_id: int,
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Delete a position from user's portfolio."""
    async with get_db_session() as session:
        svc = PortfolioService(session)
        success = await svc.delete_position(position_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Position not found")
        return {"status": "DELETED"}
