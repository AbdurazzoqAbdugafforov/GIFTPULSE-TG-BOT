"""Telegram Mini App authentication endpoint using HMAC validation."""

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.logging import logger
from app.core.security import create_access_token, validate_telegram_init_data
from app.database.models.user import User
from app.database.repositories.user_repo import UserRepository
from app.database.session import get_db_session
from app.api.dependencies.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


class TelegramAuthRequest(BaseModel):
    init_data: str = Field(..., description="Raw initData string from Telegram.WebApp.initData")


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    first_name: Optional[str]
    username: Optional[str]
    language: str
    timezone: str


class TelegramAuthResponse(BaseModel):
    token: str
    user: UserResponse


@router.post("/telegram", response_model=TelegramAuthResponse)
async def auth_telegram(body: TelegramAuthRequest, response: Response) -> Any:
    """Validate Telegram initData signature, authenticate or register user, and issue session."""
    try:
        validated = validate_telegram_init_data(body.init_data, bot_token=settings.BOT_TOKEN)
    except ValueError as e:
        logger.warning(f"Telegram auth failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Telegram authentication: {e}",
        )

    tg_user = validated.get("user")
    if not tg_user or "id" not in tg_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User information not found in initData",
        )

    tg_id = int(tg_user["id"])
    username = tg_user.get("username")
    first_name = tg_user.get("first_name")
    lang_code = tg_user.get("language_code", settings.DEFAULT_LANGUAGE)
    if lang_code not in ("uz", "en", "ru"):
        lang_code = settings.DEFAULT_LANGUAGE

    async with get_db_session() as session:
        repo = UserRepository(session)
        user, _ = await repo.get_or_create(
            telegram_id=tg_id,
            username=username,
            first_name=first_name,
            language=lang_code,
            timezone_str=settings.DEFAULT_TIMEZONE,
        )

    token = create_access_token(user.id, user.telegram_id)

    # Set secure HttpOnly cookie for same-origin browser sessions
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=False,  # Set to True in HTTPS production
        samesite="lax",
        max_age=settings.SESSION_EXPIRE_HOURS * 3600,
    )

    return {
        "token": token,
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "first_name": user.first_name,
            "username": user.username,
            "language": user.language,
            "timezone": user.timezone,
        },
    }


@router.post("/guest", response_model=TelegramAuthResponse)
async def auth_guest(response: Response) -> Any:
    """Issue guest session for web browsers and standalone previews."""
    guest_tg_id = 999999000
    async with get_db_session() as session:
        repo = UserRepository(session)
        user, _ = await repo.get_or_create(
            telegram_id=guest_tg_id,
            username="giftpulse_guest",
            first_name="GiftPulse User",
            language=settings.DEFAULT_LANGUAGE,
            timezone_str=settings.DEFAULT_TIMEZONE,
        )

    token = create_access_token(user.id, user.telegram_id)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.SESSION_EXPIRE_HOURS * 3600,
    )
    return {
        "token": token,
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "first_name": user.first_name,
            "username": user.username,
            "language": user.language,
            "timezone": user.timezone,
        },
    }


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)) -> Any:
    """Return profile and plan details of currently authenticated user."""
    from app.services.subscriptions.entitlement import EntitlementService
    async with get_db_session() as session:
        ent = EntitlementService(session)
        plan_info = await ent.get_user_plan(user.id)

    return {
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "first_name": user.first_name,
            "username": user.username,
            "language": user.language,
            "timezone": user.timezone,
        },
        "plan": {
            "code": plan_info.code,
            "name": plan_info.name,
            "alert_limit": plan_info.alert_limit,
            "watchlist_limit": plan_info.watchlist_limit,
            "expires_at": plan_info.expires_at.isoformat() if plan_info.expires_at else None,
        },
    }


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    """Clear session cookie."""
    response.delete_cookie(key="session_token")
    return {"status": "logged_out"}
