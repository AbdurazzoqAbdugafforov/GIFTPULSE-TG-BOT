"""Database initialization and seeding script."""

import asyncio
from app.core.logging import logger
from app.database.session import get_db_session, init_db, close_db
from app.database.repositories.subscription_repo import SubscriptionRepository


async def seed() -> None:
    logger.info("Initializing database tables...")
    await init_db()
    logger.info("Database tables verified.")

    async with get_db_session() as session:
        repo = SubscriptionRepository(session)
        logger.info("Seeding default subscription plans (FREE, PRO, ELITE)...")
        await repo.seed_default_plans()
        logger.info("Subscription plans successfully seeded.")

    await close_db()
    logger.info("Database seeding completed.")


if __name__ == "__main__":
    asyncio.run(seed())
