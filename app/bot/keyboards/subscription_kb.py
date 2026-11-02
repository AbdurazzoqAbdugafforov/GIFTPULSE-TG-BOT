"""Inline keyboards for subscriptions and payment flows."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.core.constants import PlanType
from app.localization.i18n import i18n


def get_subscription_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Keyboard displaying available upgrade options."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get("btn_upgrade_pro", lang=lang),
                    callback_data=f"sub:choose:{PlanType.PRO.value}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.get("btn_upgrade_elite", lang=lang),
                    callback_data=f"sub:choose:{PlanType.ELITE.value}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.get("btn_refresh", lang=lang),
                    callback_data="sub:refresh",
                )
            ],
        ]
    )


def get_payment_submit_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Action buttons on payment instructions screen."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get("btn_cancel", lang=lang),
                    callback_data="sub:cancel_payment",
                )
            ]
        ]
    )
