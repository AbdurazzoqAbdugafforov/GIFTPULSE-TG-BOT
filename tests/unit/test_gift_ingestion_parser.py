"""Unit tests for TG Gifts Open Data payload parsers and rarity normalizer."""

from decimal import Decimal
import pytest
from app.services.gift_data.parser import TGGiftsParser


def test_parse_floors_daily():
    payload = {
        "generated": "2026-11-01T10:00:00Z",
        "collections": {
            "durovs_cap": {
                "name": "Durov's Cap",
                "days": [
                    ["2026-10-30", "150.5", "12", "floor"],
                    ["2026-10-31", "162.0", "15", "floor"],
                    ["2026-11-01", "175.0", "8", "floor"],
                ],
            },
            "pepe_star": {
                "name": "Pepe Star",
                "days": [
                    ["2026-11-01", "45.0", None, "floor"],
                ],
            },
        },
    }

    normalized, max_date, generated_dt = TGGiftsParser.parse_floors_daily(payload)

    assert "durovs_cap" in normalized
    assert "pepe_star" in normalized
    assert max_date == "2026-11-01"
    assert generated_dt is not None

    durov = normalized["durovs_cap"]
    assert durov.name == "Durov's Cap"
    assert durov.latest_floor_gram == Decimal("175.0")
    assert durov.recent_sales == "8"
    assert len(durov.history) == 3


def test_parse_models_daily_and_rarity_permille():
    """Verify rarity permille conversion: percentage = rarity_permille / 10."""
    payload = {
        "collections": {
            "plush_pepe": {
                "models": {
                    "Golden Crown": {
                        "slug": "golden_crown",
                        "rarity_permille": 25,  # 25 permille = 2.5%
                        "days": [
                            ["2026-10-31", "800.0", 3],
                            ["2026-11-01", "850.0", 2],
                        ],
                    },
                    "Common Green": {
                        "slug": "common_green",
                        "rarity_permille": 500,  # 500 permille = 50.0%
                        "days": [
                            ["2026-11-01", "120.0", 15],
                        ],
                    },
                    "Unknown Rarity": {
                        "slug": "unknown_rarity",
                        "rarity_permille": None,
                        "days": [
                            ["2026-11-01", "50.0", None],
                        ],
                    },
                }
            }
        }
    }

    models, max_date = TGGiftsParser.parse_models_daily(payload)

    assert len(models) == 3
    assert max_date == "2026-11-01"

    golden = next(m for m in models if m.name == "Golden Crown")
    assert golden.rarity_permille == Decimal("25")
    assert golden.rarity_pct == Decimal("2.5")
    assert golden.latest_floor_gram == Decimal("850.0")
    assert golden.buy_now_listings == 2

    common = next(m for m in models if m.name == "Common Green")
    assert common.rarity_permille == Decimal("500")
    assert common.rarity_pct == Decimal("50.0")

    unknown = next(m for m in models if m.name == "Unknown Rarity")
    assert unknown.rarity_permille is None
    assert unknown.rarity_pct is None


def test_parse_index():
    payload = {
        "name": "TG Gifts Index",
        "symbol": "TGGI",
        "latest": {
            "date": "2026-11-01",
            "value": "1450.25",
            "change_1d_pct": "2.5",
            "change_7d_pct": "10.0",
            "constituents": 2,
        },
        "series": [
            {"date": "2026-10-30", "value": "1400.00"},
            {"date": "2026-10-31", "value": "1420.50"},
            {"date": "2026-11-01", "value": "1450.25"},
        ],
        "constituents": [
            {
                "slug": "durovs_cap",
                "name": "Durov's Cap",
                "floor_gram": "175.0",
                "weight_pct": "35.5",
                "recent_sales": "8",
            },
            {
                "slug": "plush_pepe",
                "name": "Plush Pepe",
                "floor_gram": "120.0",
                "weight_pct": "25.0",
                "recent_sales": "15",
            },
        ],
    }

    index_data = TGGiftsParser.parse_index(payload)

    assert index_data is not None
    assert index_data.latest_value == Decimal("1450.25")
    assert index_data.latest_date == "2026-11-01"
    assert len(index_data.series) == 3
    assert len(index_data.constituents) == 2
    assert index_data.constituents[0].slug == "durovs_cap"
    assert index_data.constituents[0].weight_pct == Decimal("35.5")
