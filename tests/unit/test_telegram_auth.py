"""Unit tests for Telegram WebApp HMAC-SHA256 authentication and JWT session tokens."""

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode
import pytest

from app.core.security import (
    validate_telegram_init_data,
    create_access_token,
    decode_access_token,
)


def _generate_valid_init_data(
    user_dict: dict,
    bot_token: str = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
    auth_date: int = None,
    query_id: str = "AAG123",
) -> str:
    """Helper to generate officially signed Telegram Mini App initData string."""
    if auth_date is None:
        auth_date = int(time.time())

    params = {
        "auth_date": str(auth_date),
        "query_id": query_id,
        "user": json.dumps(user_dict, separators=(",", ":")),
    }

    # Sort key-value pairs alphabetically
    data_check_string = "\n".join(f"{k}={params[k]}" for k in sorted(params.keys()))

    # Compute secret key and HMAC-SHA256
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    hash_sig = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    params["hash"] = hash_sig
    return urlencode(params)


def test_valid_init_data():
    """Verify that correctly signed Telegram initData passes validation and parses user."""
    bot_token = "123456:TEST_TOKEN_FOR_INITDATA"
    user_data = {
        "id": 987654321,
        "first_name": "Aziz",
        "username": "aziz_crypto",
        "language_code": "uz",
    }
    raw_init_data = _generate_valid_init_data(user_data, bot_token=bot_token)

    result = validate_telegram_init_data(raw_init_data, bot_token=bot_token)
    assert result["user"]["id"] == 987654321
    assert result["user"]["first_name"] == "Aziz"
    assert result["user"]["username"] == "aziz_crypto"
    assert result["query_id"] == "AAG123"


def test_tampered_init_data_fails():
    """Verify that tampering with any field invalidates the HMAC signature."""
    bot_token = "123456:TEST_TOKEN_FOR_INITDATA"
    user_data = {"id": 111, "first_name": "Alice"}
    raw_init_data = _generate_valid_init_data(user_data, bot_token=bot_token)

    # Tamper with the user parameter
    tampered = raw_init_data.replace("Alice", "Mallory")

    with pytest.raises(ValueError, match="Invalid Telegram HMAC signature"):
        validate_telegram_init_data(tampered, bot_token=bot_token)


def test_wrong_bot_token_fails():
    """Verify that validation fails if signed with a different bot token."""
    user_data = {"id": 111, "first_name": "Alice"}
    raw_init_data = _generate_valid_init_data(user_data, bot_token="TOKEN_A")

    with pytest.raises(ValueError, match="Invalid Telegram HMAC signature"):
        validate_telegram_init_data(raw_init_data, bot_token="TOKEN_B")


def test_expired_auth_date_fails():
    """Verify that outdated initData is rejected to prevent replay attacks."""
    bot_token = "123456:TEST_TOKEN_FOR_INITDATA"
    user_data = {"id": 222, "first_name": "Bob"}
    # auth_date from 2 days ago (> 86400s)
    old_time = int(time.time()) - 172800
    raw_init_data = _generate_valid_init_data(user_data, bot_token=bot_token, auth_date=old_time)

    with pytest.raises(ValueError, match="Telegram initData has expired"):
        validate_telegram_init_data(raw_init_data, bot_token=bot_token, max_age_seconds=86400)


def test_missing_hash_fails():
    """Verify that initData missing a hash parameter is rejected."""
    raw_data = "auth_date=123456789&user=%7B%22id%22%3A1%7D"
    with pytest.raises(ValueError, match="hash parameter missing"):
        validate_telegram_init_data(raw_data, bot_token="TOKEN")


def test_empty_init_data_fails():
    """Verify that empty string raises ValueError."""
    with pytest.raises(ValueError, match="initData is empty"):
        validate_telegram_init_data("", bot_token="TOKEN")


def test_jwt_create_and_decode():
    """Verify JWT token encoding and decoding."""
    token = create_access_token(user_id=42, telegram_id=987654)
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["tg_id"] == 987654


def test_invalid_jwt_token_fails():
    """Verify decoding a corrupted token raises ValueError."""
    with pytest.raises(ValueError, match="Invalid or expired session token"):
        decode_access_token("not.a.valid.jwt.token")
