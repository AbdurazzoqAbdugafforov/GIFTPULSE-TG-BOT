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
