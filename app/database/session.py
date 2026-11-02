"""Asynchronous database session management with automatic SQLite fallback."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings
from app.core.logging import logger
from app.database.models.base import Base


def _build_engine(url: str) -> AsyncEngine:
    """Build async engine adapted for SQLite or PostgreSQL."""
    if url.startswith("sqlite"):
        return create_async_engine(
            url,
            echo=False,
            connect_args={"check_same_thread": False},
        )
    return create_async_engine(
        url,
        echo=False,
        pool_pre_ping=True,
        pool_size=15,
        max_overflow=25,
        pool_recycle=1800,
    )


# Active engine & session maker
engine: AsyncEngine = _build_engine(settings.DATABASE_URL)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an asynchronous transactional session."""
    session: AsyncSession = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_db() -> None:
    """Create all tables in database with automatic fallback to SQLite on local connection failure."""
    global engine, async_session_factory
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        db_type = "SQLite" if settings.DATABASE_URL.startswith("sqlite") else "PostgreSQL"
        logger.info(f"Database initialized and tables verified ({db_type}).")
    except Exception as exc:
        if not settings.DATABASE_URL.startswith("sqlite"):
            logger.warning(
                f"PostgreSQL connection failed ({exc}). "
                f"Falling back to local SQLite database ('giftpulse.db') for zero-config operation."
            )
            try:
                await engine.dispose()
            except Exception:
                pass
            fallback_url = "sqlite+aiosqlite:///giftpulse.db"
            engine = _build_engine(fallback_url)
            async_session_factory.configure(bind=engine)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Local SQLite database initialized successfully (giftpulse.db).")
        else:
            raise


async def close_db() -> None:
    """Dispose of engine connections."""
    await engine.dispose()
