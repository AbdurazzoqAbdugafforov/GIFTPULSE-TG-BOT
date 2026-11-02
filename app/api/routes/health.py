"""Health check and readiness API endpoints for GiftPulse."""

from fastapi import APIRouter
from sqlalchemy import text
from app.core.config import settings
from app.database.session import get_db_session
from app.services.gift_data.cache import cache_manager

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Verify application connectivity to database, cache, and GiftPulse services."""
    status = {
        "status": "ok",
        "database": "unknown",
        "cache": "unknown",
        "data_engine": "GiftPulse Intelligence",
        "freshness": "unknown",
    }

    # Database check
    try:
        async with get_db_session() as session:
            await session.execute(text("SELECT 1"))
        status["database"] = "healthy"
    except Exception as e:
        status["database"] = f"unhealthy: {e}"
        status["status"] = "degraded"

    # Cache check
    try:
        is_cache_ok = await cache_manager.is_healthy()
        status["cache"] = "healthy" if is_cache_ok else "in_memory_fallback"
    except Exception as e:
        status["cache"] = f"unhealthy: {e}"
        status["status"] = "degraded"

    # Ingestion status
    try:
        ingestion_status = await cache_manager.get_json("giftpulse:ingestion:status")
        if ingestion_status:
            status["freshness"] = ingestion_status.get("data_freshness", "DAILY_CURRENT")
            status["observation_date"] = ingestion_status.get("latest_observation_date", "N/A")
        else:
            status["freshness"] = "PENDING_FIRST_INGESTION"
    except Exception:
        status["freshness"] = "UNKNOWN"

    return status
