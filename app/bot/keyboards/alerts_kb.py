"""Inline keyboards for managing and creating price alerts."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.core.constants import AlertStatus, AlertType
from app.database.models.alert import Alert
from app.localization.i18n import i18n


def get_alerts_list_keyboard(
    alerts: list[Alert],
    current_page: int,
    total_pages: int,
    lang: str = "uz",
) -> InlineKeyboardMarkup:
    """List user alerts with management actions."""
    buttons: list[list[InlineKeyboardButton]] = []

    # New Alert button on top
    buttons.append([
        InlineKeyboardButton(
            text=i18n.get("btn_new_alert", lang=lang),
            callback_data="alert:start_create",
        )
    ])

    for a in alerts:
        status_icon = "🟢" if a.status == AlertStatus.ACTIVE.value else ("🔴" if a.status == AlertStatus.TRIGGERED.value else "⏸")
        target_fmt = f"{a.target_value:,.2f}".rstrip("0").rstrip(".")
        txt = f"{status_icon} {a.symbol} ({a.alert_type.split('_')[-1]} {target_fmt})"
        buttons.append([
            InlineKeyboardButton(text=txt, callback_data=f"alert:view:{a.id}")
        ])

    # Pagination navigation
    if total_pages > 1:
        nav: list[InlineKeyboardButton] = []
        if current_page > 1:
            nav.append(
                InlineKeyboardButton(text=i18n.get("btn_prev", lang=lang), callback_data=f"alert:page:{current_page - 1}")
            )
        nav.append(
            InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="noop")
        )
        if current_page < total_pages:
            nav.append(
                InlineKeyboardButton(text=i18n.get("btn_next", lang=lang), callback_data=f"alert:page:{current_page + 1}")
            )
        buttons.append(nav)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_alert_detail_keyboard(alert: Alert, lang: str = "uz") -> InlineKeyboardMarkup:
    """Action buttons for a single alert: Pause/Resume, Delete, Back."""
    toggle_text = "⏸ Pauza" if alert.status == AlertStatus.ACTIVE.value else "▶️ Faollashtirish"
    toggle_action = f"alert:pause:{alert.id}" if alert.status == AlertStatus.ACTIVE.value else f"alert:resume:{alert.id}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=toggle_text, callback_data=toggle_action),
                InlineKeyboardButton(
                    text=i18n.get("btn_delete", lang=lang),
                    callback_data=f"alert:delete:{alert.id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=i18n.get("btn_back", lang=lang),
                    callback_data="alert:page:1",
                ),
            ],
        ]
    )


def get_alert_type_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Type selection keyboard when creating an alert."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.get("alert_type_above", lang=lang),
                    callback_data=f"alert_type:{AlertType.PRICE_ABOVE.value}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.get("alert_type_below", lang=lang),
                    callback_data=f"alert_type:{AlertType.PRICE_BELOW.value}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.get("alert_type_pct_up", lang=lang),
                    callback_data=f"alert_type:{AlertType.PERCENTAGE_INCREASE.value}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.get("alert_type_pct_down", lang=lang),
                    callback_data=f"alert_type:{AlertType.PERCENTAGE_DECREASE.value}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.get("btn_cancel", lang=lang),
                    callback_data="alert:cancel",
                )
            ],
        ]
    )


def get_alert_mode_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Mode selection keyboard (one-time vs recurring)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎯 " + i18n.get("alert_mode_once", lang=lang),
                    callback_data="alert_mode:once",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔁 " + i18n.get("alert_mode_recurring", lang=lang),
                    callback_data="alert_mode:recurring",
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.get("btn_cancel", lang=lang),
                    callback_data="alert:cancel",
                )
            ],
        ]
    )
