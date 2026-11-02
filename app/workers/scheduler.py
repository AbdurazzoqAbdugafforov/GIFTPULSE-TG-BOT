"""Background scheduler for daily market reports and subscription lifecycle."""

import asyncio
from datetime import datetime, timezone
import pytz
from aiogram import Bot
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from app.core.config import settings
from app.core.constants import DATA_ATTRIBUTION_TEXT, DATA_ATTRIBUTION_URL, DATA_LICENSE
from app.core.logging import logger
from app.database.models.subscription import Subscription
from app.database.models.user import User
from app.database.session import get_db_session
from app.services.gift_data.cache import cache_manager
from app.services.radar.service import RadarService


class BackgroundScheduler:
    """Manages periodic background tasks including daily reports at 09:00 Asia/Tashkent."""

    def __init__(self, bot: Bot | None = None):
        self.bot = bot or (Bot(token=settings.BOT_TOKEN) if settings.BOT_TOKEN else None)
        self._running = False

    async def start(self) -> None:
        """Run periodic check loop every 60 seconds."""
        self._running = True
        logger.info("GiftPulse Scheduler started.")

        while self._running:
            try:
                await self._check_subscription_expirations()
                await self._check_daily_reports()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler tick: {e}")

            await asyncio.sleep(60)

    async def stop(self) -> None:
        self._running = False
        if self.bot:
            await self.bot.session.close()
        logger.info("GiftPulse Scheduler stopped.")

    async def _check_subscription_expirations(self) -> None:
        """Find and expire subscriptions whose expires_at timestamp has passed."""
        now = datetime.now(timezone.utc)
        async with get_db_session() as session:
            stmt = (
                update(Subscription)
                .where(
                    Subscription.status == "ACTIVE",
                    Subscription.expires_at != None,
                    Subscription.expires_at < now,
                )
                .values(status="EXPIRED")
            )
            res = await session.execute(stmt)
            if res.rowcount > 0:
                logger.info(f"Expired {res.rowcount} out-of-date subscriptions.")

    async def _check_daily_reports(self) -> None:
        """Deliver daily market summary to opted-in users at their local scheduled time."""
        if not self.bot:
            return

        async with get_db_session() as session:
            stmt = (
                select(User)
                .options(selectinload(User.settings))
                .where(User.is_active == True)
            )
            users = (await session.execute(stmt)).scalars().all()
            if not users:
                return

            radar_svc = RadarService(session)
            radar_data = await radar_svc.get_market_radar()

            for user in users:
                if not user.settings or not user.settings.daily_report_enabled:
                    continue

                # Check user timezone
                tz_name = user.timezone or settings.DEFAULT_TIMEZONE
                try:
                    user_tz = pytz.timezone(tz_name)
                except Exception:
                    user_tz = pytz.timezone("Asia/Tashkent")

                now_user = datetime.now(user_tz)
                current_time_str = now_user.strftime("%H:%M")
                scheduled_time = user.settings.daily_report_time or "09:00"

                # Check if current minute matches scheduled time
                if current_time_str != scheduled_time:
                    continue

                today_str = now_user.strftime("%Y-%m-%d")
                dedup_cache_key = f"giftpulse:daily_report:{user.id}:{today_str}"
                already_sent = await cache_manager.get_json(dedup_cache_key)
                if already_sent:
                    continue

                # Build localized report
                report_text = self._format_daily_report(user, radar_data, today_str)
                try:
                    await self.bot.send_message(
                        chat_id=user.telegram_id,
                        text=report_text,
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                    )
                    await cache_manager.set_json(dedup_cache_key, {"sent_at": datetime.now(timezone.utc).isoformat()}, ttl=86400)
                except Exception as e:
                    logger.warning(f"Failed to deliver daily report to user {user.telegram_id}: {e}")

    def _format_daily_report(self, user: User, radar: dict, today_str: str) -> str:
        lang = user.language or "uz"
        idx = radar.get("index_summary", {})
        idx_val = idx.get("value", 100.0)
        idx_1d = idx.get("change_1d_pct", 0.0)
        sign = "+" if idx_1d > 0 else ""

        gainers = radar.get("top_gainers_1d", [])[:3]
        losers = radar.get("top_losers_1d", [])[:3]

        gainers_lines = ""
        for g in gainers:
            gainers_lines += f"\n  • <b>{g['name']}</b>: {g['floor_gram']:,.1f} GRAM (<code>+{g['change_1d_pct']}%</code>)"
        if not gainers_lines:
            gainers_lines = "\n  <i>Maʼlumot yoʻq</i>"

        losers_lines = ""
        for l in losers:
            losers_lines += f"\n  • <b>{l['name']}</b>: {l['floor_gram']:,.1f} GRAM (<code>{l['change_1d_pct']}%</code>)"
        if not losers_lines:
            losers_lines = "\n  <i>Maʼlumot yoʻq</i>"

        if lang == "uz":
            return (
                f"📊 <b>KUNLIK TELEGRAM GIFTS BOZOR HISOBOTI</b>\n"
                f"Sana: <code>{today_str}</code> (09:00)\n\n"
                f"🏛 <b>GiftPulse Index (GPI):</b> <code>{idx_val:.2f}</code> ({sign}{idx_1d:.2f}%)\n\n"
                f"📈 <b>Top O'sgan Kolleksiyalar (24s):</b>{gainers_lines}\n\n"
                f"📉 <b>Top Tushgan Kolleksiyalar (24s):</b>{losers_lines}\n\n"
                f"📊 <i>GiftPulse Market Intelligence</i>\n"
                f"⚠️ <i>Bu tahliliy hisobotdir, investitsiya maslahati emas.</i>"
            )
        elif lang == "ru":
            return (
                f"📊 <b>ЕЖЕДНЕВНЫЙ ОТЧЕТ РЫНКА TELEGRAM GIFTS</b>\n"
                f"Дата: <code>{today_str}</code> (09:00)\n\n"
                f"🏛 <b>GiftPulse Index (GPI):</b> <code>{idx_val:.2f}</code> ({sign}{idx_1d:.2f}%)\n\n"
                f"📈 <b>Топ Роста Коллекций (24ч):</b>{gainers_lines}\n\n"
                f"📉 <b>Топ Падения Коллекций (24ч):</b>{losers_lines}\n\n"
                f"📊 <i>GiftPulse Market Intelligence</i>\n"
                f"⚠️ <i>Аналитический отчет, не инвестиционная рекомендация.</i>"
            )
        else:
            return (
                f"📊 <b>DAILY TELEGRAM GIFTS MARKET REPORT</b>\n"
                f"Date: <code>{today_str}</code> (09:00)\n\n"
                f"🏛 <b>GiftPulse Index (GPI):</b> <code>{idx_val:.2f}</code> ({sign}{idx_1d:.2f}%)\n\n"
                f"📈 <b>Top Gaining Collections (24h):</b>{gainers_lines}\n\n"
                f"📉 <b>Top Declining Collections (24h):</b>{losers_lines}\n\n"
                f"📊 <i>GiftPulse Market Intelligence</i>\n"
                f"⚠️ <i>Daily analytics report, not investment advice.</i>"
            )
