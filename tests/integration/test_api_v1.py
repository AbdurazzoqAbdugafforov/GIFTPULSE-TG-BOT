"""Integration tests for GiftPulse Mini App REST API v1 endpoints."""

from decimal import Decimal
import json
import time
from unittest.mock import AsyncMock, patch
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.main import app
from app.core.config import settings
from app.core.security import create_access_token
import app.database.session as db_session_module
from app.database.models.base import Base
from app.database.models.collection import GiftCollection, CollectionFloorSnapshot
from app.database.models.model_item import GiftModel, ModelFloorSnapshot
from app.database.models.user import User
from app.database.repositories.subscription_repo import SubscriptionRepository
from app.database.repositories.user_repo import UserRepository
from tests.unit.test_telegram_auth import _generate_valid_init_data


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def api_client_and_user():
    """Sets up an in-memory SQLite database for FastAPI and yields an authenticated AsyncClient."""
    test_db_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(test_db_url, echo=False)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Initialize tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default subscription plans, create test user, and seed sample collection
    async with session_factory() as session:
        sub_repo = SubscriptionRepository(session)
        await sub_repo.seed_default_plans()

        user_repo = UserRepository(session)
        user, _ = await user_repo.get_or_create(
            telegram_id=777888999,
            username="giftpulse_tester",
            first_name="GiftCollector",
        )

        col = GiftCollection(
            collection_slug="durovs_cap",
            collection_name="Durov's Cap",
        )
        session.add(col)
        await session.flush()

        snap = CollectionFloorSnapshot(
            collection_id=col.id,
            observation_date="2026-11-01",
            floor_value=Decimal("150.0"),
            recent_sales="12",
        )
        session.add(snap)

        model = GiftModel(
            collection_id=col.id,
            model_name="Gold Edition",
            model_slug="gold_edition",
        )
        session.add(model)
        await session.flush()

        m_snap = ModelFloorSnapshot(
            model_id=model.id,
            observation_date="2026-11-01",
            floor_value=Decimal("450.0"),
            rarity_permille=Decimal("25"),
            buy_now_listings=3,
        )
        session.add(m_snap)
        await session.commit()

        user_id = user.id
        telegram_id = user.telegram_id
        col_id = col.id
        model_id = model.id

    token = create_access_token(user_id=user_id, telegram_id=telegram_id)

    with patch.object(db_session_module, "async_session_factory", session_factory):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            yield client, user_id, telegram_id, token, col_id, model_id, session_factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_auth_telegram_endpoint(api_client_and_user):
    """Test POST /api/v1/auth/telegram authenticating with signed initData."""
    client, user_id, telegram_id, token, col_id, model_id, session_factory = api_client_and_user

    user_data = {
        "id": 999111222,
        "first_name": "NewCollector",
        "username": "new_gift_user",
        "language_code": "uz",
    }
    init_data = _generate_valid_init_data(user_data, bot_token=settings.BOT_TOKEN)

    with patch.object(db_session_module, "async_session_factory", session_factory):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as anon_client:
            res = await anon_client.post("/api/v1/auth/telegram", json={"init_data": init_data})
            assert res.status_code == 200
            data = res.json()
            assert "token" in data
            assert data["user"]["first_name"] == "NewCollector"
            assert data["user"]["telegram_id"] == 999111222


@pytest.mark.asyncio
async def test_get_me_endpoint(api_client_and_user):
    """Test GET /api/v1/auth/me returns authenticated user and plan."""
    client, user_id, telegram_id, token, col_id, model_id, _ = api_client_and_user

    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["telegram_id"] == telegram_id
    assert data["plan"]["code"] == "FREE"


@pytest.mark.asyncio
async def test_markets_endpoints(api_client_and_user):
    """Test browsing collections and models via API v1."""
    client, user_id, telegram_id, token, col_id, model_id, _ = api_client_and_user

    # List collections
    res = await client.get("/api/v1/markets")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert any(c["slug"] == "durovs_cap" for c in data["items"])

    # Collection detail
    res_col = await client.get("/api/v1/markets/durovs_cap")
    assert res_col.status_code == 200
    col_data = res_col.json()
    assert col_data["name"] == "Durov's Cap"
    assert "GiftPulse Market Intelligence" in col_data["attribution"]

    # Models list
    res_models = await client.get("/api/v1/markets/durovs_cap/models")
    assert res_models.status_code == 200
    models_data = res_models.json()
    assert "items" in models_data
    assert len(models_data["items"]) >= 1
    assert models_data["items"][0]["name"] == "Gold Edition"
    # Rarity permille 25 -> 2.5%
    assert models_data["items"][0]["rarity_pct"] == 2.5


@pytest.mark.asyncio
async def test_alerts_crud(api_client_and_user):
    """Test full CRUD lifecycle of Gift floor alerts through API v1."""
    client, user_id, telegram_id, token, col_id, model_id, _ = api_client_and_user

    # 1. Create collection floor alert
    payload = {
        "collection_id": col_id,
        "alert_type": "COLLECTION_FLOOR_ABOVE",
        "target_value": 200.0,
        "is_recurring": False,
    }
    create_res = await client.post("/api/v1/alerts", json=payload)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["collection_id"] == col_id
    alert_id = created["id"]

    # 2. List alerts
    list_res = await client.get("/api/v1/alerts")
    assert list_res.status_code == 200
    alerts = list_res.json()
    assert any(a["id"] == alert_id for a in alerts)

    # 3. Pause alert
    pause_res = await client.put(f"/api/v1/alerts/{alert_id}/pause")
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "PAUSED"

    # 4. Resume alert
    resume_res = await client.put(f"/api/v1/alerts/{alert_id}/resume")
    assert resume_res.status_code == 200
    assert resume_res.json()["status"] == "ACTIVE"

    # 5. Delete alert
    del_res = await client.delete(f"/api/v1/alerts/{alert_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "DELETED"


@pytest.mark.asyncio
async def test_watchlist_endpoints(api_client_and_user):
    """Test Watchlist add, get, and delete endpoints."""
    client, user_id, telegram_id, token, col_id, model_id, _ = api_client_and_user

    # 1. Add collection to watchlist
    add_res = await client.post("/api/v1/watchlist", json={"collection_id": col_id})
    assert add_res.status_code == 201
    assert add_res.json()["status"] == "ADDED"

    # 2. Get watchlist
    get_res = await client.get("/api/v1/watchlist")
    assert get_res.status_code == 200
    wl_data = get_res.json()
    assert any(item["collection_id"] == col_id for item in wl_data)

    # 3. Remove collection from watchlist
    del_res = await client.delete(f"/api/v1/watchlist/{col_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "REMOVED"


@pytest.mark.asyncio
async def test_portfolio_endpoints(api_client_and_user):
    """Test Portfolio add position, get summary, and delete position."""
    client, user_id, telegram_id, token, col_id, model_id, _ = api_client_and_user

    # 1. Add position
    pos_payload = {
        "collection_id": col_id,
        "model_id": model_id,
        "quantity": 2.0,
        "purchase_price": 400.0,
    }
    add_res = await client.post("/api/v1/portfolio", json=pos_payload)
    assert add_res.status_code == 201
    pos_data = add_res.json()
    pos_id = pos_data["id"]

    # 2. Get portfolio summary
    summary_res = await client.get("/api/v1/portfolio")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["currency"] == "GRAM"
    assert summary["total_cost_basis"] == 800.0
    assert summary["total_estimated_value"] == 900.0  # 2 * 450.0
    assert summary["total_unrealized_pnl"] == 100.0
    assert any(p["id"] == pos_id for p in summary["positions"])

    # 3. Delete position
    del_res = await client.delete(f"/api/v1/portfolio/{pos_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "DELETED"


@pytest.mark.asyncio
async def test_subscription_and_payment_flow(api_client_and_user):
    """Test subscription tier listing and payment submission."""
    client, user_id, telegram_id, token, col_id, model_id, _ = api_client_and_user

    # 1. Get subscription details
    sub_res = await client.get("/api/v1/subscription")
    assert sub_res.status_code == 200
    sub_data = sub_res.json()
    assert sub_data["current_plan"]["code"] == "FREE"
    assert len(sub_data["available_plans"]) >= 3

    # 2. Submit payment receipt
    pay_res = await client.post(
        "/api/v1/subscription/payment",
        json={"plan_code": "PRO", "transaction_reference": "TX-9988771122"},
    )
    assert pay_res.status_code == 201
    pay_data = pay_res.json()
    assert pay_data["status"] == "PENDING"
    assert "id" in pay_data
