"""Parser and normalizer for TG Gifts Open Data JSON payloads."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional
from app.core.logging import logger
from app.services.gift_data.schemas import (
    CollectionDayObservation,
    IndexConstituent,
    IndexSeriesPoint,
    ModelDayObservation,
    NormalizedCollection,
    NormalizedIndex,
    NormalizedModel,
)


class TGGiftsParser:
    """Robust parser for TG Gifts daily public datasets."""

    @staticmethod
    def parse_floors_daily(
        payload: dict[str, Any]
    ) -> tuple[dict[str, NormalizedCollection], Optional[str], Optional[datetime]]:
        """Parse floors-daily.json into normalized collection structures.
        Returns (collections_dict, latest_observation_date, source_generated_at).
        """
        if not isinstance(payload, dict):
            logger.error("Invalid floors-daily payload: expected dict")
            return {}, None, None

        generated_raw = payload.get("generated")
        generated_dt = None
        if generated_raw:
            try:
                generated_dt = datetime.fromisoformat(generated_raw.replace("Z", "+00:00"))
            except Exception:
                pass

        raw_collections = payload.get("collections", {})
        if not isinstance(raw_collections, dict):
            logger.error("Invalid collections field in floors payload")
            return {}, None, generated_dt

        normalized: dict[str, NormalizedCollection] = {}
        max_date: Optional[str] = None

        for slug, col_info in raw_collections.items():
            if not isinstance(col_info, dict):
                continue

            name = col_info.get("name") or slug.replace("_", " ").title()
            raw_days = col_info.get("days", [])
            if not isinstance(raw_days, list) or not raw_days:
                continue

            history: list[CollectionDayObservation] = []
            for day_row in raw_days:
                if not isinstance(day_row, list) or len(day_row) < 2:
                    continue
                d_str = str(day_row[0])
                try:
                    f_val = Decimal(str(day_row[1]))
                except Exception:
                    continue

                sales_val = None
                if len(day_row) > 2 and day_row[2] is not None:
                    sales_val = str(day_row[2])

                kind_val = None
                if len(day_row) > 3 and day_row[3] is not None:
                    kind_val = str(day_row[3])

                obs = CollectionDayObservation(
                    date=d_str,
                    floor_gram=f_val,
                    recent_sales=sales_val,
                    price_kind=kind_val,
                )
                history.append(obs)
                if max_date is None or d_str > max_date:
                    max_date = d_str

            if not history:
                continue

            # Sort by date ascending
            history.sort(key=lambda x: x.date)
            latest_obs = history[-1]

            norm_col = NormalizedCollection(
                slug=slug,
                name=name,
                latest_date=latest_obs.date,
                latest_floor_gram=latest_obs.floor_gram,
                recent_sales=latest_obs.recent_sales,
                history=history,
            )
            normalized[slug] = norm_col

        return normalized, max_date, generated_dt

    @staticmethod
    def parse_models_daily(payload: dict[str, Any]) -> tuple[list[NormalizedModel], Optional[str]]:
        """Parse models-daily.json into normalized model structures.
        Converts rarity_permille to percentage (percentage = rarity_permille / 10).
        """
        if not isinstance(payload, dict):
            logger.error("Invalid models-daily payload: expected dict")
            return [], None

        raw_collections = payload.get("collections", {})
        if not isinstance(raw_collections, dict):
            return [], None

        models_list: list[NormalizedModel] = []
        max_date: Optional[str] = None

        for cslug, cdata in raw_collections.items():
            if not isinstance(cdata, dict):
                continue
            models_dict = cdata.get("models", {})
            if not isinstance(models_dict, dict):
                continue

            for mname, mdata in models_dict.items():
                if not isinstance(mdata, dict):
                    continue

                mslug = mdata.get("slug")
                raw_permille = mdata.get("rarity_permille")
                rarity_permille = None
                rarity_pct = None
                if raw_permille is not None:
                    try:
                        rarity_permille = Decimal(str(raw_permille))
                        rarity_pct = rarity_permille / Decimal("10")
                    except Exception:
                        pass

                raw_days = mdata.get("days", [])
                if not isinstance(raw_days, list) or not raw_days:
                    continue

                history: list[ModelDayObservation] = []
                for day_row in raw_days:
                    if not isinstance(day_row, list) or len(day_row) < 2:
                        continue
                    d_str = str(day_row[0])
                    try:
                        f_val = Decimal(str(day_row[1]))
                    except Exception:
                        continue

                    listings_val = None
                    if len(day_row) > 2 and day_row[2] is not None:
                        try:
                            listings_val = int(day_row[2])
                        except Exception:
                            pass

                    obs = ModelDayObservation(
                        date=d_str,
                        floor_gram=f_val,
                        buy_now_listings=listings_val,
                    )
                    history.append(obs)
                    if max_date is None or d_str > max_date:
                        max_date = d_str

                if not history:
                    continue

                history.sort(key=lambda x: x.date)
                latest_obs = history[-1]

                norm_model = NormalizedModel(
                    collection_slug=cslug,
                    name=mname,
                    slug=mslug,
                    rarity_permille=rarity_permille,
                    rarity_pct=rarity_pct,
                    latest_date=latest_obs.date,
                    latest_floor_gram=latest_obs.floor_gram,
                    buy_now_listings=latest_obs.buy_now_listings,
                    history=history,
                )
                models_list.append(norm_model)

        return models_list, max_date

    @staticmethod
    def parse_index(payload: dict[str, Any]) -> Optional[NormalizedIndex]:
        """Parse index.json into normalized index structure."""
        if not isinstance(payload, dict):
            logger.error("Invalid index payload: expected dict")
            return None

        latest_info = payload.get("latest", {})
        if not isinstance(latest_info, dict) or "value" not in latest_info:
            return None

        try:
            latest_val = Decimal(str(latest_info.get("value")))
            latest_date = str(latest_info.get("date"))
        except Exception as e:
            logger.error(f"Error parsing index latest value: {e}")
            return None

        c1d = Decimal(str(latest_info["change_1d_pct"])) if latest_info.get("change_1d_pct") is not None else None
        c7d = Decimal(str(latest_info["change_7d_pct"])) if latest_info.get("change_7d_pct") is not None else None
        constituents_count = latest_info.get("constituents")

        # Parse historical series
        series_points: list[IndexSeriesPoint] = []
        for s in payload.get("series", []):
            if isinstance(s, dict) and "date" in s and "value" in s:
                try:
                    s_pt = IndexSeriesPoint(
                        date=str(s["date"]),
                        value=Decimal(str(s["value"])),
                        change_pct=Decimal(str(s["change_pct"])) if s.get("change_pct") is not None else None,
                        constituents=s.get("constituents"),
                    )
                    series_points.append(s_pt)
                except Exception:
                    continue

        series_points.sort(key=lambda x: x.date)

        # Parse constituents
        constituents_list: list[IndexConstituent] = []
        for c in payload.get("constituents", []):
            if isinstance(c, dict) and "slug" in c and "name" in c:
                try:
                    c_obj = IndexConstituent(
                        slug=str(c["slug"]),
                        name=str(c["name"]),
                        floor_prev_gram=Decimal(str(c["floor_prev_gram"])) if c.get("floor_prev_gram") is not None else None,
                        floor_gram=Decimal(str(c["floor_gram"])) if c.get("floor_gram") is not None else None,
                        change_pct=Decimal(str(c["change_pct"])) if c.get("change_pct") is not None else None,
                        recent_sales=str(c["recent_sales"]) if c.get("recent_sales") is not None else None,
                        weight_pct=Decimal(str(c["weight_pct"])) if c.get("weight_pct") is not None else None,
                    )
                    constituents_list.append(c_obj)
                except Exception:
                    continue

        return NormalizedIndex(
            name=payload.get("name", "GiftPulse Index"),
            symbol=payload.get("symbol", "GPI"),
            method_version=payload.get("method_version", "1.0"),
            unit=payload.get("unit", "index points (GRAM)"),
            source="GiftPulse Market Intelligence",
            license="GiftPulse Analytics Engine",
            latest_date=latest_date,
            latest_value=latest_val,
            change_1d_pct=c1d,
            change_7d_pct=c7d,
            constituents_count=constituents_count,
            series=series_points,
            constituents=constituents_list,
        )
