"""Application configuration management using Pydantic Settings."""

import os
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Bot configuration
    BOT_TOKEN: str = Field(default="", description="Telegram Bot API Token")
    ADMIN_IDS: List[int] = Field(default_factory=list, description="Telegram User IDs for Admins")

    # Database & Cache
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://giftpulse:giftpulse_password@localhost:5432/giftpulse",
        description="Async PostgreSQL connection string",
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # TG Gifts Open Data Feeds
    TG_GIFTS_BASE_URL: str = Field(
        default="https://tggifts.com",
        description="Base URL for TG Gifts",
    )
    TG_GIFTS_FLOORS_URL: str = Field(
        default="https://tggifts.com/data/floors-daily.json",
        description="URL for TG Gifts collection floors daily snapshot",
    )
    TG_GIFTS_MODELS_URL: str = Field(
        default="https://tggifts.com/data/models-daily.json",
        description="URL for TG Gifts models daily snapshot",
    )
    TG_GIFTS_INDEX_URL: str = Field(
        default="https://tggifts.com/data/index.json",
        description="URL for TG Gifts market index snapshot",
    )

    # Localization & Defaults
    DEFAULT_TIMEZONE: str = Field(
        default="Asia/Tashkent",
        description="Default timezone for users",
    )
    DEFAULT_LANGUAGE: str = Field(
        default="uz",
        description="Default interface language (uz, en, ru)",
    )

    # Pricing (in UZS for 30 days)
    PRO_PLAN_PRICE: int = Field(default=19900, description="PRO plan price in UZS")
    ELITE_PLAN_PRICE: int = Field(default=49900, description="ELITE plan price in UZS")

    # Payment details for manual verification
    PAYMENT_CARD_NUMBER: str = Field(
        default="8600 0000 0000 0000",
        description="Bank card number for manual transfers",
    )
    PAYMENT_CARD_HOLDER: str = Field(
        default="GiftPulse LLC",
        description="Card holder name",
    )

    # Operational Parameters
    RATE_LIMIT_CALLS_PER_MINUTE: int = Field(default=60, description="Max calls per minute")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    PORT: int = Field(default=8000, description="FastAPI server port")
    MINI_APP_URL: str = Field(default="http://localhost:8000", description="Public URL for Telegram Mini App")
    JWT_SECRET: str = Field(default="giftpulse-super-secret-key-change-in-production", description="Secret key for JWT")
    JWT_ALGORITHM: str = Field(default="HS256", description="Algorithm for JWT")
    SESSION_EXPIRE_HOURS: int = Field(default=72, description="Session expiration in hours")

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: Union[str, int, List[Union[str, int]]]) -> List[int]:
        if isinstance(v, list):
            return [int(x) for x in v if str(x).strip()]
        if isinstance(v, int):
            return [v]
        if isinstance(v, str):
            ids = []
            for item in v.split(","):
                cleaned = item.strip()
                if cleaned and cleaned.isdigit():
                    ids.append(int(cleaned))
            return ids
        return []

    @property
    def is_admin(self) -> callable:
        """Helper lambda/method to check admin status."""
        return lambda tid: tid in self.ADMIN_IDS


settings = Settings()
