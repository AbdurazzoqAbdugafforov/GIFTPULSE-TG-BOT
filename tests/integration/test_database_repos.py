"""Integration tests for GiftPulse database models and repositories."""

from decimal import Decimal
import pytest
from app.core.constants import AlertStatus, AlertType
from app.database.models import GiftCollection, GiftModel, User
from app.database.repositories.alert_repo import AlertRepository
from app.database.repositories.portfolio_repo import PortfolioRepository
from app.database.repositories.user_repo import UserRepository
from app.database.repositories.watchlist_repo import WatchlistRepository


@pytest.mark.asyncio
async def test_user_repository_crud(test_db_session):
    repo = UserRepository(test_db_session)
    user, is_new = await repo.get_or_create(telegram_id=1001, username="gift_collector", first_name="Ali")
    assert is_new is True
    assert user.telegram_id == 1001
    assert user.language == "uz"

    # Second call fetches existing user
    user2, is_new2 = await repo.get_or_create(telegram_id=1001)
    assert is_new2 is False
    assert user2.id == user.id

    # Update language
    await repo.update_language(user.id, "en")
    updated = await repo.get_by_telegram_id(1001)
    assert updated.language == "en"


@pytest.mark.asyncio
async def test_watchlist_repository(test_db_session):
    user_repo = UserRepository(test_db_session)
    user, _ = await user_repo.get_or_create(telegram_id=2002)

    col = GiftCollection(collection_slug="pepe_star", collection_name="Pepe Star")
    test_db_session.add(col)
    await test_db_session.flush()

    wl_repo = WatchlistRepository(test_db_session)
    # Add collection to watchlist
    added = await wl_repo.add_collection(user.id, col.id)
    assert added is True

    # Duplicate add returns False
    duplicate = await wl_repo.add_collection(user.id, col.id)
    assert duplicate is False

    # Check entries count and check
    count = await wl_repo.count_user_entries(user.id)
    assert count == 1
    assert await wl_repo.is_in_watchlist(user.id, col.id) is True

    # Remove collection
    deleted = await wl_repo.remove_collection(user.id, col.id)
    assert deleted is True
    assert await wl_repo.count_user_entries(user.id) == 0


@pytest.mark.asyncio
async def test_alert_lifecycle_and_pause_resume(test_db_session):
    user_repo = UserRepository(test_db_session)
    user, _ = await user_repo.get_or_create(telegram_id=3003)

    col = GiftCollection(collection_slug="durovs_cap", collection_name="Durov's Cap")
    test_db_session.add(col)
    await test_db_session.flush()

    alert_repo = AlertRepository(test_db_session)
    alert = await alert_repo.create_alert(
        user_id=user.id,
        collection_id=col.id,
        alert_type=AlertType.COLLECTION_FLOOR_ABOVE.value,
        target_value=Decimal("180.0"),
        baseline_value=Decimal("150.0"),
        is_recurring=False,
    )
    assert alert.status == AlertStatus.ACTIVE.value
    assert alert.collection_id == col.id

    # Pause alert
    paused = await alert_repo.pause_alert(alert.id, user.id)
    assert paused is True
    fetched = await alert_repo.get_by_id(alert.id, user.id)
    assert fetched.status == AlertStatus.PAUSED.value

    # Resume alert
    resumed = await alert_repo.resume_alert(alert.id, user.id)
    assert resumed is True
    fetched = await alert_repo.get_by_id(alert.id, user.id)
    assert fetched.status == AlertStatus.ACTIVE.value

    # Delete alert
    deleted = await alert_repo.delete_alert(alert.id, user.id)
    assert deleted is True
    assert len(await alert_repo.get_user_alerts(user.id, status=AlertStatus.ACTIVE.value)) == 0


@pytest.mark.asyncio
async def test_portfolio_positions_repository(test_db_session):
    user_repo = UserRepository(test_db_session)
    user, _ = await user_repo.get_or_create(telegram_id=4004)

    col = GiftCollection(collection_slug="plush_pepe", collection_name="Plush Pepe")
    test_db_session.add(col)
    await test_db_session.flush()

    port_repo = PortfolioRepository(test_db_session)
    port = await port_repo.get_or_create_portfolio(user.id)
    assert port.user_id == user.id

    # Add position
    pos = await port_repo.add_position(
        user_id=user.id,
        collection_id=col.id,
        quantity=Decimal("3.0"),
        purchase_price=Decimal("85.0"),
        notes="Purchased on launch",
    )
    assert pos.id is not None
    assert pos.quantity == Decimal("3.0")

    positions = await port_repo.get_positions(user.id)
    assert len(positions) == 1
    assert positions[0].collection_id == col.id

    # Delete position
    deleted = await port_repo.delete_position(pos.id, user.id)
    assert deleted is True
    assert len(await port_repo.get_positions(user.id)) == 0
