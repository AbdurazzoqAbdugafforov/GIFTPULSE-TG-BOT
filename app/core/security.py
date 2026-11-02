"""Security utilities, validation, and rate limiting."""

import hashlib
import hmac
import html
import json
import re
import time
from urllib.parse import parse_qsl, unquote
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.constants import REDIS_THROTTLE_KEY_PREFIX

# Strict alphanumeric regex for crypto symbols (e.g. BTC, ETH, SOL, BTCUSDT)
SYMBOL_REGEX = re.compile(r"^[A-Z0-9]{2,12}$")


def sanitize_telegram_html(text: str) -> str:
    """Escape user input for safe rendering in HTML format in Telegram messages."""
    if not text:
        return ""
    return html.escape(str(text))


def validate_symbol(symbol: str) -> str:
    """Validate and normalize cryptocurrency symbol.
    Raises ValueError if symbol format is invalid.
    """
    cleaned = symbol.strip().upper()
    if not SYMBOL_REGEX.match(cleaned):
        raise ValueError(f"Invalid symbol format: {symbol}")
    return cleaned


def validate_positive_number(val: float | int | str, param_name: str = "Value") -> float:
    """Validate positive float values for prices, quantities, and targets."""
    try:
        num = float(val)
    except (ValueError, TypeError):
        raise ValueError(f"{param_name} must be a valid number.")

    if num <= 0:
        raise ValueError(f"{param_name} must be strictly greater than 0.")
    if num > 1e12:
        raise ValueError(f"{param_name} exceeds maximum permitted value.")
    return num


async def check_rate_limit(
    redis_client: Optional[aioredis.Redis],
    user_id: int,
    max_calls: int = 30,
    window_seconds: int = 60,
) -> bool:
    """Check if a user is within the rate limit.
    Returns True if permitted, False if rate limited.
    """
    if redis_client is None:
        return True  # Fallback if redis is temporarily unavailable

    key = f"{REDIS_THROTTLE_KEY_PREFIX}{user_id}"
    try:
        current = await redis_client.incr(key)
        if current == 1:
            await redis_client.expire(key, window_seconds)
        return current <= max_calls
    except Exception:
        # Fail open rather than blocking all users if cache has transient error
        return True


def validate_telegram_init_data(
    init_data_raw: str,
    bot_token: str = settings.BOT_TOKEN,
    max_age_seconds: int = 86400,
) -> Dict[str, Any]:
    """Validate Telegram WebApp initData HMAC-SHA256 signature and freshness.

    Follows the official Telegram Mini App algorithm:
    1. Parse query string into key-value pairs.
    2. Extract 'hash' parameter.
    3. Sort remaining key-value pairs alphabetically.
    4. Construct data_check_string with '\\n' separator.
    5. Compute secret_key = HMAC_SHA256(key="WebAppData", msg=bot_token).
    6. Compute signature = HMAC_SHA256(key=secret_key, msg=data_check_string).
    7. Compare signature with received hash using constant-time comparison.
    8. Verify auth_date freshness.
    9. Returns parsed dict with authenticated user info.
    """
    if not init_data_raw:
        raise ValueError("initData is empty")

    parsed_params = dict(parse_qsl(init_data_raw, keep_blank_values=True))
    received_hash = parsed_params.pop("hash", None)
    if not received_hash:
        raise ValueError("hash parameter missing from initData")

    # Construct data_check_string
    sorted_items = sorted(parsed_params.items())
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted_items)

    # Compute secret key and hash
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("Invalid Telegram HMAC signature")

    # Validate auth_date freshness
    auth_date = int(parsed_params.get("auth_date", 0))
    if auth_date <= 0:
        raise ValueError("Missing or invalid auth_date in initData")

    current_ts = int(time.time())
    if current_ts - auth_date > max_age_seconds:
        raise ValueError("Telegram initData has expired")

    # Parse user payload
    user_raw = parsed_params.get("user")
    user_data = json.loads(user_raw) if user_raw else {}

    return {
        "user": user_data,
        "auth_date": auth_date,
        "query_id": parsed_params.get("query_id"),
        "start_param": parsed_params.get("start_param"),
    }


def create_access_token(
    user_id: int,
    telegram_id: int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate JWT session token for authenticated Telegram Mini App user."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=settings.SESSION_EXPIRE_HOURS)
    )
    payload = {
        "sub": str(user_id),
        "tg_id": telegram_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT session token."""
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.PyJWTError as e:
        raise ValueError(f"Invalid or expired session token: {e}")

