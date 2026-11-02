"""Pytest shared fixtures and database setup."""

import asyncio
from decimal import Decimal
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.database.models.base import Base
from app.database.models import User, UserSettings, SubscriptionPlan, Alert
from app.core.constants import PlanType, AlertType, AlertStatus

# In-memory async SQLite engine for isolated repository tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create in-memory SQLite database tables and provide clean test session."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async_session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
