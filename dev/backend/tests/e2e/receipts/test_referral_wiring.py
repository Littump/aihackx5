from collections.abc import Callable
from datetime import datetime, timedelta

from httpx import AsyncClient
from psycopg import AsyncConnection

from app.features.referrals import database as referrals_db
from app.game_rules import REFERRAL_SECOND_PURCHASE_MIN_DAYS
from tests.e2e.receipts.referral_wiring_data import (
    AT_THRESHOLD,
    BELOW_THRESHOLD,
    NEW_REWARD,
    NOW,
    REFEREE_CREATED_AT,
    REFERRER_CREATED_AT,
    receipt_payload,
    reward_ledger_rows,
)
from tests.factories import make_referral, make_store, make_user


async def test_first_purchase_below_threshold_is_not_qualifying(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn, created_at=REFERRER_CREATED_AT)
    referee = await make_user(conn, created_at=REFEREE_CREATED_AT)
    store = await make_store(conn)
    referral = await make_referral(conn, referrer.id, referee.id, created_at=REFEREE_CREATED_AT)

    response = await client.post(
        "/api/v1/receipts", json=receipt_payload(referee.id, store.id, NOW, BELOW_THRESHOLD)
    )

    assert response.status_code == 201
    assert response.json()["referral_status"] is None
    updated = await referrals_db.get_referral_by_id(conn, referral_id=referral.id)
    assert updated is not None
    assert updated.status == "pending"
    assert updated.first_purchase_at is None


async def test_first_purchase_at_threshold_rewards_referee(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn, created_at=REFERRER_CREATED_AT)
    referee = await make_user(conn, created_at=REFEREE_CREATED_AT)
    store = await make_store(conn)
    referral = await make_referral(conn, referrer.id, referee.id, created_at=REFEREE_CREATED_AT)

    response = await client.post(
        "/api/v1/receipts", json=receipt_payload(referee.id, store.id, NOW, AT_THRESHOLD)
    )

    assert response.status_code == 201
    assert response.json()["referral_status"] == "first_purchase"
    updated = await referrals_db.get_referral_by_id(conn, referral_id=referral.id)
    assert updated is not None
    assert updated.status == "first_purchase"
    assert updated.first_purchase_at == NOW
    ledger = await reward_ledger_rows(conn, user_id=referee.id)
    assert ("referral", 0, NEW_REWARD["referee_first_purchase_points"]) in ledger


async def test_second_purchase_before_min_days_is_not_qualifying(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn, created_at=REFERRER_CREATED_AT)
    referee = await make_user(conn, created_at=REFEREE_CREATED_AT)
    store = await make_store(conn)
    first_purchase_at = NOW - timedelta(days=5)
    referral = await make_referral(
        conn,
        referrer.id,
        referee.id,
        created_at=REFEREE_CREATED_AT,
        status="first_purchase",
        first_purchase_at=first_purchase_at,
    )

    response = await client.post(
        "/api/v1/receipts", json=receipt_payload(referee.id, store.id, NOW, AT_THRESHOLD)
    )

    assert response.status_code == 201
    assert response.json()["referral_status"] is None
    updated = await referrals_db.get_referral_by_id(conn, referral_id=referral.id)
    assert updated is not None
    assert updated.status == "first_purchase"
    assert updated.second_purchase_at is None


async def test_second_purchase_at_min_days_qualifies_and_rewards_referrer(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(
        conn, created_at=REFERRER_CREATED_AT, device_fingerprint="referrer-device"
    )
    referee = await make_user(
        conn, created_at=REFEREE_CREATED_AT, device_fingerprint="referee-device"
    )
    store = await make_store(conn)
    first_purchase_at = NOW - timedelta(days=REFERRAL_SECOND_PURCHASE_MIN_DAYS)
    referral = await make_referral(
        conn,
        referrer.id,
        referee.id,
        created_at=REFEREE_CREATED_AT,
        status="first_purchase",
        first_purchase_at=first_purchase_at,
    )

    response = await client.post(
        "/api/v1/receipts", json=receipt_payload(referee.id, store.id, NOW, AT_THRESHOLD)
    )

    assert response.status_code == 201
    assert response.json()["referral_status"] == "rewarded"
    updated = await referrals_db.get_referral_by_id(conn, referral_id=referral.id)
    assert updated is not None
    assert updated.status == "rewarded"
    assert updated.second_purchase_at == NOW
    assert updated.decided_at == NOW
    assert updated.referrer_reward_points == NEW_REWARD["referrer_reward_points"]
    assert await reward_ledger_rows(conn, user_id=referrer.id) == [
        ("referral", NEW_REWARD["referrer_reward_xp"], NEW_REWARD["referrer_reward_points"])
    ]
