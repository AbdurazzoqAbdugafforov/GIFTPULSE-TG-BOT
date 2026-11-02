"""Alerts API endpoints for Telegram Mini App."""

from decimal import Decimal
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.api.dependencies.auth import get_current_user
from app.database.models.user import User
from app.database.session import get_db_session
from app.services.alerts.engine import AlertEngine

router = APIRouter(prefix="/alerts", tags=["Alerts"])


class CreateAlertRequest(BaseModel):
    collection_id: int
    model_id: Optional[int] = None
    alert_type: str
    target_value: Decimal = Field(..., gt=0)
    is_recurring: bool = False


@router.get("")
async def list_user_alerts(current_user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
    """Fetch all active and paused alerts configured by user."""
    async with get_db_session() as session:
        engine = AlertEngine(session)
        return await engine.get_user_alerts(current_user.id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user_alert(
    payload: CreateAlertRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Create a new daily floor alert."""
    async with get_db_session() as session:
        engine = AlertEngine(session)
        alert, err = await engine.create_alert(
            user_id=current_user.id,
            collection_id=payload.collection_id,
            model_id=payload.model_id,
            alert_type=payload.alert_type,
            target_value=payload.target_value,
            is_recurring=payload.is_recurring,
        )
        if not alert:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

        return {
            "id": alert.id,
            "collection_id": alert.collection_id,
            "model_id": alert.model_id,
            "alert_type": alert.alert_type,
            "target_value": float(alert.target_value),
            "status": alert.status,
            "is_recurring": alert.is_recurring,
        }


@router.put("/{alert_id}/pause")
async def pause_user_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    async with get_db_session() as session:
        engine = AlertEngine(session)
        success = await engine.pause_alert(alert_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found or not active")
        return {"status": "PAUSED"}


@router.put("/{alert_id}/resume")
async def resume_user_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    async with get_db_session() as session:
        engine = AlertEngine(session)
        success = await engine.resume_alert(alert_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found or not paused")
        return {"status": "ACTIVE"}


@router.delete("/{alert_id}")
async def delete_user_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    async with get_db_session() as session:
        engine = AlertEngine(session)
        success = await engine.delete_alert(alert_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"status": "DELETED"}
