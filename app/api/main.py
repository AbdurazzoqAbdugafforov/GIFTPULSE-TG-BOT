"""FastAPI entrypoint for health checks, REST API v1, and Mini App static files for GiftPulse."""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import health
from app.api.v1 import (
    alerts,
    auth,
    dashboard,
    markets,
    portfolio,
    radar,
    settings as settings_route,
    subscription,
    watchlist,
)
from app.core.config import settings
from app.database.session import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="GiftPulse Platform API",
    description="Backend API and Telegram Mini App endpoints for GiftPulse Telegram Gifts analytics",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for Telegram WebApp and local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base health checks
app.include_router(health.router)

# API v1 routes
v1_prefix = "/api/v1"
app.include_router(auth.router, prefix=v1_prefix)
app.include_router(dashboard.router, prefix=v1_prefix)
app.include_router(markets.router, prefix=v1_prefix)
app.include_router(alerts.router, prefix=v1_prefix)
app.include_router(watchlist.router, prefix=v1_prefix)
app.include_router(portfolio.router, prefix=v1_prefix)
app.include_router(radar.router, prefix=v1_prefix)
app.include_router(subscription.router, prefix=v1_prefix)
app.include_router(settings_route.router, prefix=v1_prefix)

# Mount frontend build static directory if built
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
else:
    @app.get("/")
    async def root():
        return {
            "name": "GiftPulse Platform API",
            "version": "1.0.0",
            "status": "online",
            "engine": "GiftPulse Market Intelligence",
        }
