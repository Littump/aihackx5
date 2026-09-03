from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Literal

import pytest
from httpx import AsyncClient
from psycopg import AsyncConnection

from app.game_rules import REFERRAL_REWARDS, REFERRAL_SECOND_PURCHASE_MIN_DAYS
from tests.e2e.receipts.referral_wiring_data import (
    AT_THRESHOLD,
    NOW,
    REFEREE_CREATED_AT,
    REFERRER_CREATED_AT,
    receipt_payload,
    reward_ledger_rows,
)
from tests.factories import make_referral, make_store, make_user

RefereeKind = Literal["new", "dormant", "active"]
NON_NEW_KINDS: tuple[RefereeKind, ...] = ("dormant", "active")
FIRST_PURCHASE_KIND_CASES: list[tuple[RefereeKind, int]] = [
    (kind, REFERRAL_REWARDS[kind]["referee_first_purchase_points"]) for kind in NON_NEW_KINDS
]


@pytest.mark.parametrize("referee_kind, expected_points", FIRST_PURCHASE_KIND_CASES)
async def test_first_purchase_reward_matches_referee_kind_table(
    client: AsyncClient,
    conn: AsyncConnection,
    freeze_time: Callable[[datetime], None],
    referee_kind: RefereeKind,
    expected_points: int,
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn, created_at=REFERRER_CREATED_AT)
    referee = await make_user(conn, created_at=REFEREE_CREATED_AT)
    store = await make_store(conn)
    await make_referral(
        conn,
        referrer.id,
        referee.id,
        created_at=REFEREE_CREATED_AT,
        referee_kind=referee_kind,
    )

    response = await client.post(
        "/api/v1/receipts", json=receipt_payload(referee.id, store.id, NOW, AT_THRESHOLD)
    )

    assert response.status_code == 201
    assert response.json()["referral_status"] == "first_purchase"
    ledger = await reward_ledger_rows(conn, user_id=referee.id)
    assert ("referral", 0, expected_points) in ledger


SECOND_PURCHASE_KIND_CASES: list[tuple[RefereeKind, int, int]] = [
    (
        kind,
        REFERRAL_REWARDS[kind]["referrer_reward_points"],
        REFERRAL_REWARDS[kind]["referrer_reward_xp"],
    )
    for kind in NON_NEW_KINDS
]


@pytest.mark.parametrize("referee_kind, expected_points, expected_xp", SECOND_PURCHASE_KIND_CASES)
async def test_second_purchase_reward_matches_referee_kind_table(
    client: AsyncClient,
    conn: AsyncConnection,
    freeze_time: Callable[[datetime], None],
    referee_kind: RefereeKind,
    expected_points: int,
    expected_xp: int,
) -> None:
    freeze_time(NOW)
    referrer = await make_user(
        conn, created_at=REFERRER_CREATED_AT, device_fingerprint=f"referrer-{referee_kind}"
    )
    referee = await make_user(
        conn, created_at=REFEREE_CREATED_AT, device_fingerprint=f"referee-{referee_kind}"
    )
    store = await make_store(conn)
    first_purchase_at = NOW - timedelta(days=REFERRAL_SECOND_PURCHASE_MIN_DAYS)
    await make_referral(
        conn,
        referrer.id,
        referee.id,
        created_at=REFEREE_CREATED_AT,
        referee_kind=referee_kind,
        status="first_purchase",
        first_purchase_at=first_purchase_at,
    )

    response = await client.post(
        "/api/v1/receipts", json=receipt_payload(referee.id, store.id, NOW, AT_THRESHOLD)
    )

    assert response.status_code == 201
    assert response.json()["referral_status"] == "rewarded"
    ledger = await reward_ledger_rows(conn, user_id=referrer.id)
    assert ("referral", expected_xp, expected_points) in ledger
