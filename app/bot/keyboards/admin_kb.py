"""Inline keyboards for administrator dashboard and actions."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_admin_dashboard_keyboard() -> InlineKeyboardMarkup:
    """Administrator dashboard navigation keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Statistika", callback_data="admin:stats"),
                InlineKeyboardButton(text="💳 Kutilayotgan To'lovlar", callback_data="admin:pending"),
            ],
            [
                InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin:users"),
                InlineKeyboardButton(text="💎 Tarif Rejalari", callback_data="admin:plans"),
            ],
            [
                InlineKeyboardButton(text="📢 E'lon Yuborish", callback_data="admin:broadcast"),
                InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin:refresh"),
            ],
        ]
    )


def get_payment_action_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    """Admin buttons to approve or reject a specific payment."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data=f"admin:pay:approve:{payment_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Rad etish",
                    callback_data=f"admin:pay:reject:{payment_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Kutilayotganlar ro'yxatiga",
                    callback_data="admin:pending",
                )
            ],
        ]
    )


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Confirmation before sending broadcast."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 Yuborish", callback_data="admin:broadcast_confirm"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin:broadcast_cancel"),
            ]
        ]
    )
