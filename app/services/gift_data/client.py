"""HTTP client for TG Gifts Open Data datasets with conditional caching and retries."""

import asyncio
from typing import Any, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger


class TGGiftsClient:
    """Client for fetching CC BY 4.0 public datasets from tggifts.com."""

    def __init__(self, timeout_seconds: float = 20.0, max_retries: int = 3):
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self._etags: dict[str, str] = {}
        self._last_modified: dict[str, str] = {}
        self._cache: dict[str, Any] = {}

    async def _fetch_with_retry(self, url: str) -> Optional[dict[str, Any]]:
        headers = {
            "User-Agent": "GiftPulse/1.0 (Telegram Gifts Market Analytics)",
            "Accept": "application/json",
        }
        if url in self._etags:
            headers["If-None-Match"] = self._etags[url]
        if url in self._last_modified:
            headers["If-Modified-Since"] = self._last_modified[url]

        delay = 1.0
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(url, headers=headers)

                    if resp.status_code == 304:
                        logger.info(f"TG Gifts dataset 304 Not Modified for {url}")
                        return self._cache.get(url)

                    if resp.status_code == 200:
                        etag = resp.headers.get("ETag")
                        if etag:
                            self._etags[url] = etag
                        lm = resp.headers.get("Last-Modified")
                        if lm:
                            self._last_modified[url] = lm

                        data = resp.json()
                        self._cache[url] = data
                        return data

                    logger.warning(
                        f"TG Gifts fetch attempt {attempt}/{self.max_retries} for {url} returned HTTP {resp.status_code}"
                    )
            except Exception as exc:
                last_exception = exc
                logger.warning(
                    f"TG Gifts fetch attempt {attempt}/{self.max_retries} failed for {url}: {exc}"
                )

            if attempt < self.max_retries:
                await asyncio.sleep(delay)
                delay *= 2

        if last_exception:
            logger.error(f"Failed to fetch TG Gifts dataset from {url} after {self.max_retries} attempts: {last_exception}")
        return None

    async def fetch_floors_daily(self) -> Optional[dict[str, Any]]:
        return await self._fetch_with_retry(settings.TG_GIFTS_FLOORS_URL)

    async def fetch_models_daily(self) -> Optional[dict[str, Any]]:
        return await self._fetch_with_retry(settings.TG_GIFTS_MODELS_URL)

    async def fetch_index(self) -> Optional[dict[str, Any]]:
        return await self._fetch_with_retry(settings.TG_GIFTS_INDEX_URL)
