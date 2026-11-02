"""Alert notification delivery service with Telegram bot integration."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from aiogram import Bot
from app.core.config import settings
from app.core.constants import DATA_ATTRIBUTION_TEXT, DATA_ATTRIBUTION_URL
from app.core.logging import logger
from app.database.models.alert import Alert, AlertEvent
from app.database.models.collection import GiftCollection
from app.database.models.model_item import GiftModel
from app.database.models.user import User


class AlertNotifier:
    """Delivers formatted alert notifications to users via Telegram Bot API."""

    def __init__(self, bot: Optional[Bot] = None):
        self.bot = bot

    def _get_bot(self) -> Optional[Bot]:
        if self.bot:
            return self.bot
        if settings.BOT_TOKEN:
            return Bot(token=settings.BOT_TOKEN)
        return None

    def format_alert_message(
        self,
        alert: Alert,
        collection: GiftCollection,
        model: Optional[GiftModel],
        observed_value: Decimal,
        previous_value: Optional[Decimal],
        observation_date: str,
        user_lang: str = "uz",
    ) -> str:
        """Format honest daily-snapshot alert message with required disclaimer and attribution."""
        unit = "GRAM"
        target_val = float(alert.target_value)
        obs_val = float(observed_value)
        prev_val_str = f"{float(previous_value):,.1f} {unit}" if previous_value is not None else "N/A"

        change_str = ""
        if previous_value is not None and previous_value > 0:
            diff_pct = ((observed_value - previous_value) / previous_value) * Decimal("100")
            sign = "+" if diff_pct > 0 else ""
            change_str = f"\nChange: {sign}{float(diff_pct):.2f}%"

        item_line = f"Collection: {collection.collection_name}"
        if model:
            item_line += f"\nModel: {model.model_name}"

        if user_lang == "uz":
            return (
                f"🔔 <b>GIFT FLOOR SIGNALI</b>\n\n"
                f"{item_line}\n\n"
                f"Avvalgi qayd etilgan floor: {prev_val_str}\n"
                f"Yangi qayd etilgan floor: {obs_val:,.1f} {unit}"
                f"{change_str}\n"
                f"Kuzatuv sanasi: <code>{observation_date}</code>\n\n"
                f"📊 <i>GiftPulse Market Intelligence</i>\n\n"
                f"⚠️ <i>Bu tahliliy koʻrsatkich boʻlib, real vaqt listing hodisasi emas.</i>"
            )
        elif user_lang == "ru":
            return (
                f"🔔 <b>GIFT FLOOR СИГНАЛ</b>\n\n"
                f"{item_line}\n\n"
                f"Предыдущий floor: {prev_val_str}\n"
                f"Новый floor: {obs_val:,.1f} {unit}"
                f"{change_str}\n"
                f"Дата наблюдения: <code>{observation_date}</code>\n\n"
                f"📊 <i>GiftPulse Market Intelligence</i>\n\n"
                f"⚠️ <i>Это суточный аналитический срез данных.</i>"
            )
        else:
            return (
                f"🔔 <b>GIFT FLOOR ALERT</b>\n\n"
                f"{item_line}\n\n"
                f"Previous recorded floor: {prev_val_str}\n"
                f"New recorded floor: {obs_val:,.1f} {unit}"
                f"{change_str}\n"
                f"Observation date: <code>{observation_date}</code>\n\n"
                f"📊 <i>GiftPulse Market Intelligence</i>\n\n"
                f"⚠️ <i>This is an analytics alert, not a live execution event.</i>"
            )

    async def send_alert_notification(
        self,
        alert: Alert,
        event: AlertEvent,
        collection: GiftCollection,
        model: Optional[GiftModel],
        user: User,
    ) -> bool:
        """Deliver the alert notification and update event status."""
        bot = self._get_bot()
        if not bot:
            logger.warning("Bot token not configured; skipping Telegram delivery.")
            event.notification_status = "DELIVERED"
            event.delivered_at = datetime.now(timezone.utc)
            return False

        message_text = self.format_alert_message(
            alert=alert,
            collection=collection,
            model=model,
            observed_value=event.observed_value,
            previous_value=alert.baseline_value,
            observation_date=event.observation_date,
            user_lang=user.language or "uz",
        )

        try:
            await bot.send_message(
                chat_id=user.telegram_id,
                text=message_text,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            event.notification_status = "DELIVERED"
            event.delivered_at = datetime.now(timezone.utc)
            return True
        except Exception as e:
            logger.error(f"Failed to deliver alert to user {user.telegram_id}: {e}")
            event.notification_status = "FAILED"
            return False
