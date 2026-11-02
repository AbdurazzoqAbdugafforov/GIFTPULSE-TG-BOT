"""Centralized Ingestion Worker process for GiftPulse."""

import asyncio
from app.core.logging import logger
from app.database.session import get_db_session
from app.services.gift_data.ingestion import IngestionService


class IngestionWorker:
    def __init__(self, interval_seconds: int = 3600):
        self.interval = interval_seconds
        self._running = False

    async def start(self) -> None:
        self._running = True
        logger.info(f"GiftPulse IngestionWorker started (interval: {self.interval}s).")

        # Initial ingestion immediately on start
        await self.run_once()

        while self._running:
            try:
                await asyncio.sleep(self.interval)
                if self._running:
                    await self.run_once()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in IngestionWorker loop: {e}")
                await asyncio.sleep(60)

    async def run_once(self) -> dict:
        logger.info("Executing periodic TG Gifts ingestion...")
        async with get_db_session() as session:
            svc = IngestionService(session)
            result = await svc.ingest_all(trigger_alerts=True)
            logger.info(f"Ingestion run complete. Result: {result.get('observation_date')}, Alerts: {result.get('alerts_triggered')}")
            return result

    def stop(self) -> None:
        self._running = False
        logger.info("GiftPulse IngestionWorker stopped.")


if __name__ == "__main__":
    worker = IngestionWorker()
    asyncio.run(worker.start())
