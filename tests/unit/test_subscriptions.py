"""Unit and repository tests for Subscriptions and Entitlements."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from app.core.constants import DEFAULT_PLAN_LIMITS, PaymentStatus, PlanType
from app.database.models import User, SubscriptionPlan, Subscription
from app.database.repositories.subscription_repo import SubscriptionRepository
from app.database.repositories.payment_repo import PaymentRepository
from app.services.subscriptions.entitlement import EntitlementService


@pytest.mark.asyncio
async def test_free_plan_defaults_and_limits(test_db_session):
    sub_repo = SubscriptionRepository(test_db_session)
    await sub_repo.seed_default_plans()

    # Create test user
    user = User(telegram_id=12345, language="uz", timezone="Asia/Tashkent")
    test_db_session.add(user)
    await test_db_session.flush()

    ent = EntitlementService(test_db_session)
    plan_info = await ent.get_user_plan(user.id)

    # Should default to FREE
    assert plan_info.code == PlanType.FREE.value
    assert plan_info.alert_limit == 3
    assert plan_info.watchlist_limit == 5

    # Can create alert up to 3
    allowed, err = await ent.can_create_alert(user.id)
    assert allowed is True
    assert err is None


@pytest.mark.asyncio
async def test_pro_plan_activation_and_limits(test_db_session):
    sub_repo = SubscriptionRepository(test_db_session)
    await sub_repo.seed_default_plans()

    user = User(telegram_id=99999, language="en", timezone="Asia/Tashkent")
    test_db_session.add(user)
    await test_db_session.flush()

    pro_plan = await sub_repo.get_plan_by_code(PlanType.PRO.value)
    # Activate PRO subscription
    await sub_repo.activate_subscription(user.id, pro_plan.id, duration_days=30)

    ent = EntitlementService(test_db_session)
    plan_info = await ent.get_user_plan(user.id)

    assert plan_info.code == PlanType.PRO.value
    assert plan_info.alert_limit == 30
    assert plan_info.watchlist_limit == 50
    assert plan_info.expires_at is not None


@pytest.mark.asyncio
async def test_expired_subscription_falls_back_to_free(test_db_session):
    sub_repo = SubscriptionRepository(test_db_session)
    await sub_repo.seed_default_plans()

    user = User(telegram_id=55555, language="en", timezone="Asia/Tashkent")
    test_db_session.add(user)
    await test_db_session.flush()

    pro_plan = await sub_repo.get_plan_by_code(PlanType.PRO.value)
    # Create expired subscription (expired 1 day ago)
    expired_sub = Subscription(
        user_id=user.id,
        plan_id=pro_plan.id,
        status="ACTIVE",
        starts_at=datetime.now(timezone.utc) - timedelta(days=31),
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    test_db_session.add(expired_sub)
    await test_db_session.flush()

    ent = EntitlementService(test_db_session)
    plan_info = await ent.get_user_plan(user.id)

    # Should detect expiration and fall back to FREE
    assert plan_info.code == PlanType.FREE.value
    assert plan_info.alert_limit == 3


@pytest.mark.asyncio
async def test_payment_approval_and_duplicate_prevention(test_db_session):
    sub_repo = SubscriptionRepository(test_db_session)
    await sub_repo.seed_default_plans()

    user = User(telegram_id=77777, language="uz")
    test_db_session.add(user)
    await test_db_session.flush()

    pro_plan = await sub_repo.get_plan_by_code(PlanType.PRO.value)

    pay_repo = PaymentRepository(test_db_session)
    payment = await pay_repo.create_payment_request(
        user_id=user.id,
        plan_id=pro_plan.id,
        amount=Decimal("19900"),
        transaction_reference="TX_123456",
    )
    assert payment.status == PaymentStatus.PENDING.value

    # First approval succeeds
    approved = await pay_repo.approve_payment(payment.id, admin_telegram_id=111)
    assert approved is not None
    assert approved.status == PaymentStatus.APPROVED.value
    assert approved.reviewed_by == 111

    # Second approval on already approved payment must fail / return None
    duplicate = await pay_repo.approve_payment(payment.id, admin_telegram_id=111)
    assert duplicate is None
