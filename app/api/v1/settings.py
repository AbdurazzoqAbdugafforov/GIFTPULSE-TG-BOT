"""User settings REST API endpoints for GiftPulse."""

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.api.dependencies.auth import get_current_user
from app.database.models.user import User
from app.database.repositories.user_repo import UserRepository
from app.database.session import get_db_session

router = APIRouter(prefix="/settings", tags=["Settings"])


class UpdateSettingsRequest(BaseModel):
    language: Optional[str] = Field(None, pattern="^(uz|en|ru)$")
    timezone: Optional[str] = Field(None, max_length=64)
    daily_report_enabled: Optional[bool] = Field(None)
    notifications_enabled: Optional[bool] = Field(None)


@router.get("")
async def get_settings(user: User = Depends(get_current_user)) -> Any:
    """Return user configuration."""
    async with get_db_session() as session:
        repo = UserRepository(session)
        db_user = await repo.get_by_telegram_id(user.telegram_id)

    return {
        "language": db_user.language if db_user else "uz",
        "timezone": db_user.timezone if db_user else "Asia/Tashkent",
        "daily_report_enabled": db_user.settings.daily_report_enabled if db_user and db_user.settings else False,
        "notifications_enabled": db_user.settings.notifications_enabled if db_user and db_user.settings else True,
    }


@router.patch("")
async def update_settings(
    body: UpdateSettingsRequest,
    user: User = Depends(get_current_user),
) -> Any:
    """Update language, timezone, or report preferences."""
    async with get_db_session() as session:
        repo = UserRepository(session)
        if body.language:
            await repo.update_language(user.id, body.language)
        if body.timezone:
            await repo.update_timezone(user.id, body.timezone)
        db_user = await repo.get_by_telegram_id(user.telegram_id)
        if db_user and db_user.settings:
            if body.daily_report_enabled is not None:
                db_user.settings.daily_report_enabled = body.daily_report_enabled
            if body.notifications_enabled is not None:
                db_user.settings.notifications_enabled = body.notifications_enabled
            await session.commit()

    return {"status": "updated"}


@router.post("/delete-data")
async def delete_my_data(user: User = Depends(get_current_user)) -> Any:
    """Permanently delete all personal user records and alerts."""
    async with get_db_session() as session:
        repo = UserRepository(session)
        await repo.delete_user_data(user.telegram_id)
        await session.commit()
    return {"status": "DELETED"}
