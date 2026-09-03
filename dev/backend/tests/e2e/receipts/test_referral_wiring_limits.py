from collections.abc import Callable
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from psycopg import AsyncConnection

from app.features.antifraud import service as antifraud_service
from app.features.antifraud.models import FraudDecision, FraudDecisionKind, FraudSignal
from app.features.referrals import database as referrals_db
from app.game_rules import REFERRAL_PAID_PER_MONTH, REFERRAL_SECOND_PURCHASE_MIN_DAYS
from tests.e2e.receipts.referral_wiring_data import (
    AT_THRESHOLD,
    NOW,
    REFEREE_CREATED_AT,
    REFERRER_CREATED_AT,
    receipt_payload,
    reward_ledger_rows,
)
from tests.factories import make_referral, make_store, make_user

FIRST_PURCHASE_AT = NOW - timedelta(days=REFERRAL_SECOND_PURCHASE_MIN_DAYS)


def _fake_decision(score: float, kind: FraudDecisionKind) -> FraudDecision:
    signal = FraudSignal(code="test_signal", weight=score, strong=False, detail="синтетика")
    return FraudDecision(score=score, decision=kind, signals=[signal])


async def _seed_referral_in_progress(
    conn: AsyncConnection, *, referrer_id: int, referee_id: int
) -> int:
    referral = await make_referral(
        conn,
        referrer_id,
        referee_id,
        created_at=REFEREE_CREATED_AT,
        status="first_purchase",
        first_purchase_at=FIRST_PURCHASE_AT,
    )
    return referral.id


async def test_second_purchase_hold_decision_moves_to_on_review(
    client: AsyncClient,
    conn: AsyncConnection,
    freeze_time: Callable[[datetime], None],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn, created_at=REFERRER_CREATED_AT)
    referee = await make_user(conn, created_at=REFEREE_CREATED_AT)
    store = await make_store(conn)
    referral_id = await _seed_referral_in_progress(
        conn, referrer_id=referrer.id, referee_id=referee.id
    )

    async def fake_check_referral(_: AsyncConnection, __: int) -> FraudDecision:
        return _fake_decision(0.6, "hold")

    monkeypatch.setattr(antifraud_service, "check_referral", fake_check_referral)

    response = await client.post(
        "/api/v1/receipts", json=receipt_payload(referee.id, store.id, NOW, AT_THRESHOLD)
    )

    assert response.status_code == 201
    assert response.json()["referral_status"] == "on_review"
    updated = await referrals_db.get_referral_by_id(conn, referral_id=referral_id)
    assert updated is not None
    assert updated.status == "on_review"
    assert updated.referrer_reward_points == 0


async def test_second_purchase_block_decision_blocks_referral(
    client: AsyncClient,
    conn: AsyncConnection,
    freeze_time: Callable[[datetime], None],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn, created_at=REFERRER_CREATED_AT)
    referee = await make_user(conn, created_at=REFEREE_CREATED_AT)
    store = await make_store(conn)
    referral_id = await _seed_referral_in_progress(
        conn, referrer_id=referrer.id, referee_id=referee.id
    )

    async def fake_check_referral(_: AsyncConnection, __: int) -> FraudDecision:
        return _fake_decision(0.9, "block")

    monkeypatch.setattr(antifraud_service, "check_referral", fake_check_referral)

    response = await client.post(
        "/api/v1/receipts", json=receipt_payload(referee.id, store.id, NOW, AT_THRESHOLD)
    )

    assert response.status_code == 201
    assert response.json()["referral_status"] == "blocked"
    updated = await referrals_db.get_referral_by_id(conn, referral_id=referral_id)
    assert updated is not None
    assert updated.status == "blocked"
    assert updated.referrer_reward_points == 0


async def test_sixth_paid_referral_in_month_gets_no_reward(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(
        conn, created_at=REFERRER_CREATED_AT, device_fingerprint="referrer-device"
    )
    for _ in range(REFERRAL_PAID_PER_MONTH):
        filler = await make_user(conn, created_at=REFERRER_CREATED_AT)
        await make_referral(
            conn,
            referrer.id,
            filler.id,
            created_at=REFEREE_CREATED_AT,
            status="rewarded",
            decided_at=NOW,
        )
    referee = await make_user(
        conn, created_at=REFEREE_CREATED_AT, device_fingerprint="referee-device"
    )
    store = await make_store(conn)
    referral_id = await _seed_referral_in_progress(
        conn, referrer_id=referrer.id, referee_id=referee.id
    )

    response = await client.post(
        "/api/v1/receipts", json=receipt_payload(referee.id, store.id, NOW, AT_THRESHOLD)
    )

    assert response.status_code == 201
    assert response.json()["referral_status"] == "qualified"
    updated = await referrals_db.get_referral_by_id(conn, referral_id=referral_id)
    assert updated is not None
    assert updated.status == "qualified"
    assert updated.decided_at is None
    assert updated.referrer_reward_points == 0
    assert await reward_ledger_rows(conn, user_id=referrer.id) == []


async def test_fifth_paid_referral_in_month_still_gets_rewarded(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(
        conn, created_at=REFERRER_CREATED_AT, device_fingerprint="referrer-device"
    )
    for _ in range(REFERRAL_PAID_PER_MONTH - 1):
        filler = await make_user(conn, created_at=REFERRER_CREATED_AT)
        await make_referral(
            conn,
            referrer.id,
            filler.id,
            created_at=REFEREE_CREATED_AT,
            status="rewarded",
            decided_at=NOW,
        )
    referee = await make_user(
        conn, created_at=REFEREE_CREATED_AT, device_fingerprint="referee-device"
    )
    store = await make_store(conn)
    referral_id = await _seed_referral_in_progress(
        conn, referrer_id=referrer.id, referee_id=referee.id
    )

    response = await client.post(
        "/api/v1/receipts", json=receipt_payload(referee.id, store.id, NOW, AT_THRESHOLD)
    )

    assert response.status_code == 201
    assert response.json()["referral_status"] == "rewarded"
    updated = await referrals_db.get_referral_by_id(conn, referral_id=referral_id)
    assert updated is not None
    assert updated.status == "rewarded"
    assert updated.decided_at == NOW
    assert updated.referrer_reward_points > 0
    # "rewarded" разблокирует рефереру ачивку neighbour отдельной строкой в ledger
    assert len(await reward_ledger_rows(conn, user_id=referrer.id)) == 2
