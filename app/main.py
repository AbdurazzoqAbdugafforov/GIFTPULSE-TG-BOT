"""Main application entrypoint for GiftPulse."""

import argparse
import asyncio
import sys
import uvicorn
from app.api.main import app as fastapi_app
from app.bot.bot import create_bot, set_bot_commands, setup_dispatcher
from app.core.config import settings
from app.core.logging import logger
from app.database.repositories.subscription_repo import SubscriptionRepository
from app.database.session import close_db, get_db_session, init_db
from app.workers.ingestion_worker import IngestionWorker
from app.workers.scheduler import BackgroundScheduler


async def ensure_db_ready() -> None:
    """Initialize DB and seed default plans."""
    await init_db()
    async with get_db_session() as session:
        sub_repo = SubscriptionRepository(session)
        await sub_repo.seed_default_plans()


async def run_bot() -> None:
    """Run Aiogram Telegram bot polling process."""
    logger.info("Initializing GiftPulse Telegram Bot...")
    await ensure_db_ready()

    # Periodic data worker so bot always has fresh market snapshots
    worker = IngestionWorker(interval_seconds=3600)
    bot = create_bot()
    dp = setup_dispatcher()

    logger.info("🤖 Bot starting long-polling... Send /start to your bot!")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await set_bot_commands(bot)
        await asyncio.gather(
            worker.start(),
            dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()),
        )
    finally:
        worker.stop()
        await bot.session.close()
        await close_db()


async def run_worker() -> None:
    """Run Ingestion worker and scheduler in background."""
    logger.info("Initializing GiftPulse background workers...")
    await ensure_db_ready()

    worker = IngestionWorker(interval_seconds=3600)
    scheduler = BackgroundScheduler()

    try:
        await asyncio.gather(worker.start(), scheduler.start())
    except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
        worker.stop()
        await scheduler.stop()
        await close_db()


def run_api() -> None:
    """Run FastAPI server for API and Mini App."""
    logger.info(f"Starting GiftPulse FastAPI server on port {settings.PORT}...")
    uvicorn.run(fastapi_app, host="0.0.0.0", port=settings.PORT, log_level=settings.LOG_LEVEL.lower())


async def run_all() -> None:
    """Run FastAPI API server, Telegram Bot, Ingestion Worker, and Scheduler concurrently in a single process."""
    logger.info("Starting GiftPulse in unified local mode (API + Bot + Data Worker)...")
    await ensure_db_ready()

    worker = IngestionWorker(interval_seconds=3600)
    scheduler = BackgroundScheduler()

    bot = create_bot()
    dp = setup_dispatcher()

    config = uvicorn.Config(
        fastapi_app,
        host="0.0.0.0",
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
    )
    server = uvicorn.Server(config)

    logger.info("🚀 GiftPulse is fully online!")
    logger.info(f"📱 Web Mini App: http://localhost:{settings.PORT}")
    logger.info("🤖 Telegram Bot polling started. Send /start to your bot!")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await set_bot_commands(bot)
        await asyncio.gather(
            server.serve(),
            worker.start(),
            scheduler.start(),
            dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()),
        )
    finally:
        worker.stop()
        await scheduler.stop()
        await bot.session.close()
        await close_db()


def main() -> None:
    parser = argparse.ArgumentParser(description="GiftPulse Unified Platform Runner")
    parser.add_argument(
        "mode",
        choices=["bot", "worker", "api", "all"],
        default=None,
        nargs="?",
        help="Service to run (bot, worker, api, all). Default: all",
    )
    parser.add_argument("--bot", action="store_true", help="Run Telegram bot")
    parser.add_argument("--worker", action="store_true", help="Run ingestion workers")
    parser.add_argument("--api", action="store_true", help="Run FastAPI Mini App server")
    parser.add_argument("--all", action="store_true", help="Run all services together")

    args, _ = parser.parse_known_args()

    selected_mode = "all"
    if args.bot:
        selected_mode = "bot"
    elif args.worker:
        selected_mode = "worker"
    elif args.api:
        selected_mode = "api"
    elif args.all:
        selected_mode = "all"
    elif args.mode:
        selected_mode = args.mode

    if selected_mode == "api":
        run_api()
    elif selected_mode == "bot":
        asyncio.run(run_bot())
    elif selected_mode == "worker":
        asyncio.run(run_worker())
    elif selected_mode == "all":
        asyncio.run(run_all())


if __name__ == "__main__":
    main()
