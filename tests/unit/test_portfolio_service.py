"""Unit and integration tests for GiftPulse Portfolio valuation and analytics."""

from decimal import Decimal
import pytest
from app.core.constants import DATA_ATTRIBUTION_TEXT, DATA_ATTRIBUTION_URL
from app.database.models import (
    CollectionFloorSnapshot,
    GiftCollection,
    GiftModel,
    ModelFloorSnapshot,
    Portfolio,
    PortfolioPosition,
    User,
)
from app.services.portfolio.service import PortfolioService


@pytest.mark.asyncio
async def test_portfolio_model_floor_valuation(test_db_session):
    """Test portfolio holding with model-level floor valuation."""
    user = User(telegram_id=111222, language="uz")
    test_db_session.add(user)
    await test_db_session.flush()

    col = GiftCollection(collection_slug="pepe_star", collection_name="Pepe Star")
    test_db_session.add(col)
    await test_db_session.flush()

    model = GiftModel(
        collection_id=col.id,
        model_name="Pepe Astronaut",
        model_slug="pepe_astronaut",
    )
    test_db_session.add(model)
    await test_db_session.flush()

    # Add model snapshot
    m_snap = ModelFloorSnapshot(
        model_id=model.id,
        observation_date="2026-11-01",
        floor_value=Decimal("250.0"),
        rarity_permille=Decimal("50"),
    )
    test_db_session.add(m_snap)

    # User owns 2 Pepe Astronauts bought at 200 GRAM each (cost: 400 GRAM)
    # Estimated value at 250 GRAM = 500 GRAM (+100 GRAM PnL, +25%)
    port = Portfolio(user_id=user.id, name="Test Portfolio")
    test_db_session.add(port)
    await test_db_session.flush()

    pos = PortfolioPosition(
        portfolio_id=port.id,
        collection_id=col.id,
        model_id=model.id,
        quantity=Decimal("2.0"),
        purchase_price=Decimal("200.0"),
    )
    test_db_session.add(pos)
    await test_db_session.commit()

    svc = PortfolioService(test_db_session)
    summary = await svc.calculate_summary(user.id, port.id)

    assert summary["total_cost_basis"] == 400.0
    assert summary["total_estimated_value"] == 500.0
    assert summary["total_unrealized_pnl"] == 100.0
    assert summary["total_pnl_pct"] == 25.0
    assert summary["currency"] == "GRAM"
    assert len(summary["positions"]) == 1
    assert summary["positions"][0]["valuation_source"] == "MODEL_FLOOR"
    assert summary["attribution"] == DATA_ATTRIBUTION_TEXT
    assert summary["attribution_url"] == DATA_ATTRIBUTION_URL


@pytest.mark.asyncio
async def test_portfolio_collection_floor_fallback_and_warning(test_db_session):
    """Test fallback to collection floor and warning when model snapshot is missing."""
    user = User(telegram_id=333444, language="en")
    test_db_session.add(user)
    await test_db_session.flush()

    col = GiftCollection(collection_slug="durovs_cap", collection_name="Durov's Cap")
    test_db_session.add(col)
    await test_db_session.flush()

    c_snap = CollectionFloorSnapshot(
        collection_id=col.id,
        observation_date="2026-11-01",
        floor_value=Decimal("80.0"),
    )
    test_db_session.add(c_snap)

    # Model without model floor snapshot
    model = GiftModel(
        collection_id=col.id,
        model_name="Rare Fedora",
        model_slug="rare_fedora",
    )
    test_db_session.add(model)
    await test_db_session.flush()

    port = Portfolio(user_id=user.id, name="Main")
    test_db_session.add(port)
    await test_db_session.flush()

    # User owns 1 Rare Fedora bought at 100 GRAM
    pos = PortfolioPosition(
        portfolio_id=port.id,
        collection_id=col.id,
        model_id=model.id,
        quantity=Decimal("1.0"),
        purchase_price=Decimal("100.0"),
    )
    test_db_session.add(pos)
    await test_db_session.commit()

    svc = PortfolioService(test_db_session)
    summary = await svc.calculate_summary(user.id, port.id)

    # Fallback to collection floor 80.0 -> PnL: -20.0 (-20%)
    assert summary["total_cost_basis"] == 100.0
    assert summary["total_estimated_value"] == 80.0
    assert summary["total_unrealized_pnl"] == -20.0
    assert summary["total_pnl_pct"] == -20.0
    assert summary["positions"][0]["valuation_source"] == "COLLECTION_FLOOR_FALLBACK"
    assert len(summary["warnings"]) >= 1
    assert "Rare Fedora" in summary["warnings"][0]
