"""Centralized Ingestion Worker for TG Gifts Open Data."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.database.models.collection import GiftCollection, CollectionFloorSnapshot
from app.database.models.model_item import GiftModel, ModelFloorSnapshot
from app.database.models.market_index import MarketIndexSnapshot
from app.database.models.ingestion import IngestionRun
from app.services.gift_data.cache import cache_manager
from app.services.gift_data.client import TGGiftsClient
from app.services.gift_data.parser import TGGiftsParser


class IngestionService:
    """Service responsible for reliable dataset ingestion, normalization, and persistence."""

    def __init__(self, session: AsyncSession, client: Optional[TGGiftsClient] = None):
        self.session = session
        self.client = client or TGGiftsClient()
        self.parser = TGGiftsParser()

    async def ingest_all(self, trigger_alerts: bool = True) -> dict[str, Any]:
        """Fetch, parse, and save all 3 public datasets: floors, models, and index."""
        logger.info("Starting TG Gifts full ingestion cycle...")
        floors_res = await self.ingest_floors()
        models_res = await self.ingest_models()
        index_res = await self.ingest_index()

        # Update cache summary
        is_success = floors_res["status"] == "SUCCESS"
        obs_date = floors_res.get("observation_date") or index_res.get("observation_date")
        
        status_payload = {
            "last_ingestion_at": datetime.now(timezone.utc).isoformat(),
            "latest_observation_date": obs_date,
            "floors_status": floors_res["status"],
            "models_status": models_res["status"],
            "index_status": index_res["status"],
            "data_freshness": "DAILY_CURRENT" if is_success else "STALE",
            "provider": "GiftPulse Intelligence",
            "license": "GiftPulse Analytics Engine",
        }
        await cache_manager.set_json("giftpulse:ingestion:status", status_payload, ttl=86400)

        # Centrally trigger alert evaluation only if new snapshots were inserted
        alerts_triggered_count = 0
        if trigger_alerts and (floors_res.get("new_snapshots", 0) > 0 or models_res.get("new_snapshots", 0) > 0):
            try:
                from app.services.alerts.engine import AlertEngine
                alert_engine = AlertEngine(self.session)
                alerts_triggered_count = await alert_engine.evaluate_centralized_snapshots(
                    observation_date=obs_date
                )
                logger.info(f"Centralized alert evaluation completed: {alerts_triggered_count} alerts triggered.")
            except Exception as e:
                logger.error(f"Error during post-ingestion alert evaluation: {e}")

        return {
            "floors": floors_res,
            "models": models_res,
            "index": index_res,
            "observation_date": obs_date,
            "alerts_triggered": alerts_triggered_count,
        }

    async def ingest_floors(self) -> dict[str, Any]:
        """Fetch, normalize and persist floors-daily.json."""
        raw_payload = await self.client.fetch_floors_daily()
        if not raw_payload:
            run = IngestionRun(
                provider="TG_GIFTS",
                dataset_name="floors-daily",
                status="FAILED",
                error_message="HTTP request failed or provider unavailable",
            )
            self.session.add(run)
            await self.session.commit()
            return {"status": "FAILED", "records_received": 0, "new_snapshots": 0}

        collections_dict, obs_date, generated_dt = self.parser.parse_floors_daily(raw_payload)
        records_received = len(collections_dict)
        new_snapshots_count = 0

        try:
            # 1. Fetch all existing collections to minimize queries
            stmt = select(GiftCollection)
            res = await self.session.execute(stmt)
            existing_map: dict[str, GiftCollection] = {c.collection_slug: c for c in res.scalars().all()}

            # 2. Upsert collections
            for slug, norm_col in collections_dict.items():
                col_obj = existing_map.get(slug)
                if not col_obj:
                    col_obj = GiftCollection(
                        collection_slug=slug,
                        collection_name=norm_col.name,
                        is_active=True,
                    )
                    self.session.add(col_obj)
                    await self.session.flush()
                    existing_map[slug] = col_obj
                else:
                    if col_obj.collection_name != norm_col.name:
                        col_obj.collection_name = norm_col.name

                # 3. Check existing snapshots for this collection to prevent duplicate insertion
                snap_stmt = select(CollectionFloorSnapshot.observation_date).where(
                    CollectionFloorSnapshot.collection_id == col_obj.id
                )
                snap_res = await self.session.execute(snap_stmt)
                existing_dates = set(snap_res.scalars().all())

                # Insert only new daily observations
                for obs in norm_col.history:
                    if obs.date not in existing_dates:
                        snapshot = CollectionFloorSnapshot(
                            collection_id=col_obj.id,
                            observation_date=obs.date,
                            floor_value=obs.floor_gram,
                            recent_sales=obs.recent_sales,
                            source="GiftPulse Market Intelligence",
                            source_generated_at=generated_dt,
                            data_confidence="CONFIRMED",
                        )
                        self.session.add(snapshot)
                        existing_dates.add(obs.date)
                        new_snapshots_count += 1

            run = IngestionRun(
                provider="TG_GIFTS",
                dataset_name="floors-daily",
                status="SUCCESS",
                observation_date=obs_date,
                records_received=records_received,
                records_inserted=new_snapshots_count,
            )
            self.session.add(run)
            await self.session.commit()

            # Cache the latest collection list for fast API responses
            await cache_manager.set_json(
                "giftpulse:collections:latest_summary",
                {
                    "observation_date": obs_date,
                    "count": records_received,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                ttl=3600,
            )

            return {
                "status": "SUCCESS",
                "observation_date": obs_date,
                "records_received": records_received,
                "new_snapshots": new_snapshots_count,
            }
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error persisting floors-daily: {e}")
            run = IngestionRun(
                provider="TG_GIFTS",
                dataset_name="floors-daily",
                status="FAILED",
                observation_date=obs_date,
                records_received=records_received,
                records_inserted=0,
                error_message=str(e),
            )
            self.session.add(run)
            await self.session.commit()
            return {"status": "FAILED", "error": str(e), "new_snapshots": 0}

    async def ingest_models(self) -> dict[str, Any]:
        """Fetch, normalize and persist models-daily.json."""
        raw_payload = await self.client.fetch_models_daily()
        if not raw_payload:
            run = IngestionRun(
                provider="TG_GIFTS",
                dataset_name="models-daily",
                status="FAILED",
                error_message="HTTP request failed or provider unavailable",
            )
            self.session.add(run)
            await self.session.commit()
            return {"status": "FAILED", "records_received": 0, "new_snapshots": 0}

        models_list, obs_date = self.parser.parse_models_daily(raw_payload)
        records_received = len(models_list)
        new_snapshots_count = 0

        try:
            # Pre-load collections to map slug to ID
            c_stmt = select(GiftCollection)
            c_res = await self.session.execute(c_stmt)
            col_map = {c.collection_slug: c.id for c in c_res.scalars().all()}

            # Pre-load existing models: (collection_id, model_name) -> GiftModel
            m_stmt = select(GiftModel)
            m_res = await self.session.execute(m_stmt)
            existing_models = {(m.collection_id, m.model_name): m for m in m_res.scalars().all()}

            for norm_m in models_list:
                col_id = col_map.get(norm_m.collection_slug)
                if not col_id:
                    continue  # Collection must exist

                model_key = (col_id, norm_m.name)
                m_obj = existing_models.get(model_key)
                if not m_obj:
                    m_obj = GiftModel(
                        collection_id=col_id,
                        model_name=norm_m.name,
                        model_slug=norm_m.slug,
                    )
                    self.session.add(m_obj)
                    await self.session.flush()
                    existing_models[model_key] = m_obj

                # Pre-fetch existing snapshot dates for this model
                snap_stmt = select(ModelFloorSnapshot.observation_date).where(
                    ModelFloorSnapshot.model_id == m_obj.id
                )
                snap_res = await self.session.execute(snap_stmt)
                existing_dates = set(snap_res.scalars().all())

                for obs in norm_m.history:
                    if obs.date not in existing_dates:
                        m_snapshot = ModelFloorSnapshot(
                            model_id=m_obj.id,
                            observation_date=obs.date,
                            floor_value=obs.floor_gram,
                            rarity_permille=norm_m.rarity_permille,
                            buy_now_listings=obs.buy_now_listings,
                        )
                        self.session.add(m_snapshot)
                        existing_dates.add(obs.date)
                        new_snapshots_count += 1

            run = IngestionRun(
                provider="TG_GIFTS",
                dataset_name="models-daily",
                status="SUCCESS",
                observation_date=obs_date,
                records_received=records_received,
                records_inserted=new_snapshots_count,
            )
            self.session.add(run)
            await self.session.commit()

            return {
                "status": "SUCCESS",
                "observation_date": obs_date,
                "records_received": records_received,
                "new_snapshots": new_snapshots_count,
            }
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error persisting models-daily: {e}")
            run = IngestionRun(
                provider="TG_GIFTS",
                dataset_name="models-daily",
                status="FAILED",
                observation_date=obs_date,
                records_received=records_received,
                records_inserted=0,
                error_message=str(e),
            )
            self.session.add(run)
            await self.session.commit()
            return {"status": "FAILED", "error": str(e), "new_snapshots": 0}

    async def ingest_index(self) -> dict[str, Any]:
        """Fetch, normalize and persist index.json."""
        raw_payload = await self.client.fetch_index()
        if not raw_payload:
            run = IngestionRun(
                provider="TG_GIFTS",
                dataset_name="index",
                status="FAILED",
                error_message="HTTP request failed or provider unavailable",
            )
            self.session.add(run)
            await self.session.commit()
            return {"status": "FAILED", "records_received": 0, "new_snapshots": 0}

        norm_index = self.parser.parse_index(raw_payload)
        if not norm_index:
            return {"status": "FAILED", "error": "Failed to parse index JSON"}

        new_snapshots_count = 0
        try:
            existing_series_dates_stmt = select(MarketIndexSnapshot.observation_date)
            ex_series_res = await self.session.execute(existing_series_dates_stmt)
            all_known_dates = set(ex_series_res.scalars().all())

            constituents_json = [c.model_dump(mode="json") for c in norm_index.constituents]

            if norm_index.latest_date not in all_known_dates:
                idx_snap = MarketIndexSnapshot(
                    observation_date=norm_index.latest_date,
                    index_value=norm_index.latest_value,
                    change_pct=norm_index.change_1d_pct,
                    constituents=norm_index.constituents_count,
                    constituents_data=constituents_json,
                    source=norm_index.source,
                )
                self.session.add(idx_snap)
                all_known_dates.add(norm_index.latest_date)
                new_snapshots_count = 1
            else:
                stmt = select(MarketIndexSnapshot).where(
                    MarketIndexSnapshot.observation_date == norm_index.latest_date
                )
                res = await self.session.execute(stmt)
                existing = res.scalar_one_or_none()
                if existing and not existing.constituents_data and constituents_json:
                    existing.constituents_data = constituents_json

            for pt in norm_index.series:
                if pt.date not in all_known_dates:
                    series_snap = MarketIndexSnapshot(
                        observation_date=pt.date,
                        index_value=pt.value,
                        change_pct=pt.change_pct,
                        constituents=pt.constituents,
                        source=norm_index.source,
                    )
                    self.session.add(series_snap)
                    all_known_dates.add(pt.date)
                    new_snapshots_count += 1

            run = IngestionRun(
                provider="TG_GIFTS",
                dataset_name="index",
                status="SUCCESS",
                observation_date=norm_index.latest_date,
                records_received=len(norm_index.series) + 1,
                records_inserted=new_snapshots_count,
            )
            self.session.add(run)
            await self.session.commit()

            # Cache the index payload for fast rendering
            cache_payload = norm_index.model_dump(mode="json")
            await cache_manager.set_json("giftpulse:index:latest", cache_payload, ttl=3600)

            return {
                "status": "SUCCESS",
                "observation_date": norm_index.latest_date,
                "latest_value": float(norm_index.latest_value),
                "new_snapshots": new_snapshots_count,
            }
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error persisting index: {e}")
            run = IngestionRun(
                provider="TG_GIFTS",
                dataset_name="index",
                status="FAILED",
                observation_date=norm_index.latest_date,
                records_received=1,
                records_inserted=0,
                error_message=str(e),
            )
            self.session.add(run)
            await self.session.commit()
            return {"status": "FAILED", "error": str(e), "new_snapshots": 0}
