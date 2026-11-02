"""Security, validation, and authorization tests."""

import pytest
from unittest.mock import MagicMock
from app.bot.filters.admin import IsAdmin
from app.core.config import settings
from app.core.security import sanitize_telegram_html, validate_positive_number, validate_symbol


@pytest.mark.asyncio
async def test_admin_filter_authorization():
    # Configure test admin ID
    settings.ADMIN_IDS = [123456789]
    admin_filter = IsAdmin()

    # Admin user
    admin_msg = MagicMock()
    admin_msg.from_user.id = 123456789
    assert await admin_filter(admin_msg) is True

    # Non-admin user
    regular_msg = MagicMock()
    regular_msg.from_user.id = 987654321
    assert await admin_filter(regular_msg) is False

    # Event without user
    empty_msg = MagicMock()
    empty_msg.from_user = None
    assert await admin_filter(empty_msg) is False


def test_symbol_validation():
    # Valid symbols
    assert validate_symbol("btc") == "BTC"
    assert validate_symbol("btcusdt") == "BTCUSDT"
    assert validate_symbol("TON") == "TON"

    # Malicious or invalid symbols
    with pytest.raises(ValueError):
        validate_symbol("BTC; DROP TABLE users;--")

    with pytest.raises(ValueError):
        validate_symbol("<script>alert(1)</script>")

    with pytest.raises(ValueError):
        validate_symbol("A")  # Too short

    with pytest.raises(ValueError):
        validate_symbol("VERYLONGSYMBOLNAMEEXCEEDING")


def test_positive_number_validation():
    # Valid numbers
    assert validate_positive_number("68000") == 68000.0
    assert validate_positive_number(0.0001) == 0.0001

    # Zero or negative numbers
    with pytest.raises(ValueError):
        validate_positive_number("0")

    with pytest.raises(ValueError):
        validate_positive_number("-15")

    # Non-numeric input
    with pytest.raises(ValueError):
        validate_positive_number("abc")

    # Exorbitant numbers
    with pytest.raises(ValueError):
        validate_positive_number("1e15")


def test_telegram_html_sanitizer():
    raw = "<b>Hello</b> & <script>alert('xss')</script>"
    sanitized = sanitize_telegram_html(raw)
    assert "&lt;b&gt;" in sanitized
    assert "&amp;" in sanitized
    assert "&lt;script&gt;" in sanitized
    assert "<script>" not in sanitized
