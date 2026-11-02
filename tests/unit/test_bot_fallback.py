"""Unit tests for fallback router and concurrency handling."""

from unittest.mock import AsyncMock, MagicMock
import pytest
from aiogram.types import Message, CallbackQuery, User as TgUser
from app.bot.handlers.fallback import handle_fallback_message, handle_fallback_callback
from app.database.models.user import User


@pytest.mark.asyncio
async def test_fallback_message_handler():
    mock_msg = MagicMock(spec=Message)
    mock_msg.answer = AsyncMock()
    mock_msg.from_user = TgUser(id=999, is_bot=False, first_name="Ali")

    db_user = User(id=1, telegram_id=999, language="uz")

    await handle_fallback_message(mock_msg, db_user)

    mock_msg.answer.assert_called_once()
    args, kwargs = mock_msg.answer.call_args
    assert "Assalomu alaykum" in kwargs["text"] or "GiftPulse" in kwargs["text"]
    assert kwargs["reply_markup"] is not None


@pytest.mark.asyncio
async def test_fallback_callback_handler():
    mock_cb = MagicMock(spec=CallbackQuery)
    mock_cb.answer = AsyncMock()

    await handle_fallback_callback(mock_cb)

    mock_cb.answer.assert_called_once()


def test_main_menu_keyboard_https_safety(monkeypatch):
    from app.bot.keyboards.main_menu import get_main_menu_keyboard
    from app.core.config import settings

    # Case 1: HTTP URL should NOT use WebAppInfo (safe from Telegram 400 error)
    monkeypatch.setattr(settings, "MINI_APP_URL", "http://localhost:8000")
    assert not settings.is_miniapp_https
    kb = get_main_menu_keyboard("uz")
    first_btn = kb.keyboard[0][0]
    assert first_btn.web_app is None

    # Case 2: HTTPS URL correctly attaches WebAppInfo
    monkeypatch.setattr(settings, "MINI_APP_URL", "https://giftpulse.app")
    assert settings.is_miniapp_https
    kb_https = get_main_menu_keyboard("uz")
    first_btn_https = kb_https.keyboard[0][0]
    assert first_btn_https.web_app is not None
    assert first_btn_https.web_app.url == "https://giftpulse.app"

