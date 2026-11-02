"""Structured logging configuration with sensitive data sanitization."""

import logging
import re
import sys
from typing import Any
from app.core.config import settings

# Sensitive patterns to redact
SENSITIVE_PATTERNS = [
    re.compile(r"bot\d+:[A-Za-z0-9_-]{35}", re.IGNORECASE),  # Telegram Bot Token
    re.compile(r"password=([^\s&;]+)", re.IGNORECASE),
    re.compile(r"://([^:]+):([^@]+)@", re.IGNORECASE),  # DB connection credentials
    re.compile(r"(api[_-]?key|secret|token|private[_-]?key)=([^\s&;]+)", re.IGNORECASE),
]


class SensitiveDataFilter(logging.Filter):
    """Filter that masks sensitive tokens, passwords, and secrets in log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self._sanitize(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self._sanitize_val(v) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self._sanitize_val(arg) for arg in record.args)
        return True

    def _sanitize_val(self, val: Any) -> Any:
        if isinstance(val, str):
            return self._sanitize(val)
        return val

    def _sanitize(self, text: str) -> str:
        for pattern in SENSITIVE_PATTERNS:
            text = pattern.sub("[REDACTED]", text)
        return text


def setup_logging(log_level: str | None = None) -> logging.Logger:
    """Initialize structured application logging with UTF-8 support on Windows."""
    # Force UTF-8 on Windows consoles to prevent charmap UnicodeEncodeError
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    level = getattr(logging, (log_level or settings.LOG_LEVEL).upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    handler.addFilter(SensitiveDataFilter())

    root_logger.addHandler(handler)

    # Silence overly verbose external loggers
    logging.getLogger("aiogram").setLevel(logging.INFO)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return logging.getLogger("giftpulse")


logger = setup_logging()
