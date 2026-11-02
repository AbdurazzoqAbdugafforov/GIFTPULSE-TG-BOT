"""Aiogram 3.x Telegram Bot setup and router registration for GiftPulse."""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import logger
from app.bot.middlewares.throttling import ThrottlingMiddleware
from app.bot.middlewares.user_tracking import UserTrackingMiddleware
from app.bot.handlers import (
    start,
    prices,
    alerts,
    watchlist,
    portfolio,
    radar,
    index_handler,
    subscription,
    settings as settings_handler,
    help as help_handler,
    admin,
    fallback,
)


def create_bot() -> Bot:
    """Create configured Aiogram Bot instance."""
    return Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def setup_dispatcher(redis_client: aioredis.Redis | None = None) -> Dispatcher:
    """Create and configure Aiogram Dispatcher with middlewares and routers."""
    dp = Dispatcher(storage=MemoryStorage())

    # Register Middlewares
    dp.message.middleware(ThrottlingMiddleware(redis_client))
    dp.callback_query.middleware(ThrottlingMiddleware(redis_client))

    dp.message.middleware(UserTrackingMiddleware())
    dp.callback_query.middleware(UserTrackingMiddleware())

    # Register Handlers
    dp.include_router(start.router)
    dp.include_router(prices.router)
    dp.include_router(alerts.router)
    dp.include_router(watchlist.router)
    dp.include_router(portfolio.router)
    dp.include_router(radar.router)
    dp.include_router(index_handler.router)
    dp.include_router(subscription.router)
    dp.include_router(settings_handler.router)
    dp.include_router(help_handler.router)
    dp.include_router(admin.router)
    dp.include_router(fallback.router)

    logger.info("Aiogram dispatcher and GiftPulse routers registered successfully.")
    return dp


async def set_bot_commands(bot: Bot) -> None:
    """Set official Telegram Bot menu commands for maximum convenience."""
    commands = [
        BotCommand(command="start", description="🚀 GiftPulse-ni ishga tushirish"),
        BotCommand(command="market", description="🎁 Gift bozori va kolleksiyalar"),
        BotCommand(command="models", description="✨ Modellar va noyoblik (rarity)"),
        BotCommand(command="radar", description="📡 Bozor radari (24s top oʻzgarishlar)"),
        BotCommand(command="index", description="📈 GiftPulse Index (GPI)"),
        BotCommand(command="portfolio", description="💼 Shaxsiy portfelim"),
        BotCommand(command="alerts", description="🔔 Narx signallari"),
        BotCommand(command="watchlist", description="⭐ Kuzatuv roʻyxati"),
        BotCommand(command="subscription", description="💎 PRO / ELITE obuna"),
        BotCommand(command="settings", description="⚙️ Sozlamalar"),
        BotCommand(command="help", description="ℹ️ Yordam va maʼlumotlar"),
    ]
    try:
        await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
        logger.info("Bot commands successfully registered with Telegram API.")
    except Exception as e:
        logger.warning(f"Could not register bot commands: {e}")
