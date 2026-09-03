from collections.abc import Callable
from datetime import datetime, timedelta
from decimal import Decimal

from httpx import AsyncClient
from psycopg import AsyncConnection

from app.core.clock import week_end, week_start
from app.game_rules import XP_ACHIEVEMENT, XP_RECEIPT
from tests.e2e.receipts.antifraud_wiring_data import (
    BURST_HISTORY_OFFSETS_MIN,
    DAILY_LIMIT_HOUR_OFFSETS,
    FINAL_ITEM_PAYLOAD,
    HISTORY_ITEM,
    NOW,
)
from tests.factories import make_challenge, make_receipt, make_store, make_user


def _payload(
    user_id: int, store_id: int, purchased_at: datetime, pos_id: str | None
) -> dict[str, object]:
    return {
        "user_id": user_id,
        "store_id": store_id,
        "purchased_at": purchased_at.isoformat(),
        "pos_id": pos_id,
        "items": FINAL_ITEM_PAYLOAD,
    }


async def _make_burst_history(
    conn: AsyncConnection, user_id: int, store_id: int, *, pos_id: str | None
) -> None:
    for minutes in BURST_HISTORY_OFFSETS_MIN:
        await make_receipt(
            conn,
            user_id,
            store_id=store_id,
            purchased_at=NOW - timedelta(minutes=minutes),
            counted=False,
            pos_id=pos_id,
            items=[HISTORY_ITEM],
        )


async def test_burst_and_same_pos_signals_block_receipt_and_persist_reason(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    store = await make_store(conn)
    await _make_burst_history(conn, user.id, store.id, pos_id="POS1")

    response = await client.post("/api/v1/receipts", json=_payload(user.id, store.id, NOW, "POS1"))

    assert response.status_code == 201
    body = response.json()
    assert body["fraud"]["decision"] == "block"
    assert body["fraud"]["score"] >= 0.8
    strong_signals = [s for s in body["fraud"]["signals"] if s["strong"]]
    assert len(strong_signals) >= 2
    assert body["counted"] is False
    assert body["counted_reason"] == "fraud_block"
    assert body["xp_delta"] == 0

    cursor = await conn.execute(
        "SELECT counted FROM receipts WHERE id = %s", (body["receipt"]["id"],)
    )
    row = await cursor.fetchone()
    assert row is not None
    assert row[0] is False


async def test_burst_and_daily_volume_hold_keeps_counted_and_awards_rewards(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    store = await make_store(conn)
    await make_challenge(
        conn,
        user.id,
        type="frequency",
        category=None,
        baseline=Decimal("2"),
        target=Decimal("5"),
        progress=Decimal("0"),
        is_hero=True,
        period_start=week_start(),
        period_end=week_end(),
    )
    await _make_burst_history(conn, user.id, store.id, pos_id=None)

    response = await client.post("/api/v1/receipts", json=_payload(user.id, store.id, NOW, None))

    assert response.status_code == 201
    body = response.json()
    assert body["fraud"]["decision"] == "hold"
    assert 0.5 <= body["fraud"]["score"] < 0.8
    assert body["counted"] is True
    assert body["counted_reason"] is None
    # первый счётный чек пользователя разблокирует first_receipt
    assert body["xp_delta"] == XP_RECEIPT + XP_ACHIEVEMENT
    assert body["achievements_unlocked"] == ["first_receipt"]
    assert body["challenges"][0]["progress_after"] == 1.0

    cursor = await conn.execute(
        "SELECT count(*) FROM fraud_checks WHERE subject_type = 'receipt' AND subject_id = %s",
        (body["receipt"]["id"],),
    )
    row = await cursor.fetchone()
    assert row is not None
    assert row[0] == 1


async def test_block_leaves_hero_challenge_and_league_rank_untouched(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    store = await make_store(conn)
    hero = await make_challenge(
        conn,
        user.id,
        type="frequency",
        category=None,
        baseline=Decimal("2"),
        target=Decimal("5"),
        progress=Decimal("0"),
        is_hero=True,
        period_start=week_start(),
        period_end=week_end(),
    )
    await _make_burst_history(conn, user.id, store.id, pos_id="POS1")

    response = await client.post("/api/v1/receipts", json=_payload(user.id, store.id, NOW, "POS1"))

    assert response.status_code == 201
    body = response.json()
    assert body["fraud"]["decision"] == "block"
    assert body["counted"] is False
    assert body["challenges"] == []
    assert body["league_rank_before"] == body["league_rank_after"]

    cursor = await conn.execute("SELECT progress, status FROM challenges WHERE id = %s", (hero.id,))
    row = await cursor.fetchone()
    assert row is not None
    assert row[0] == Decimal("0")
    assert row[1] == "active"


async def test_block_keeps_daily_limit_reason_when_already_uncounted(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    other_store = await make_store(conn)
    burst_store = await make_store(conn)
    for hour_offset in DAILY_LIMIT_HOUR_OFFSETS:
        await make_receipt(
            conn,
            user.id,
            store_id=other_store.id,
            purchased_at=NOW - timedelta(hours=6) + timedelta(hours=hour_offset),
            counted=True,
        )
    await _make_burst_history(conn, user.id, burst_store.id, pos_id="POS1")

    response = await client.post(
        "/api/v1/receipts", json=_payload(user.id, burst_store.id, NOW, "POS1")
    )

    assert response.status_code == 201
    body = response.json()
    assert body["fraud"]["decision"] == "block"
    assert body["counted"] is False
    assert body["counted_reason"] == "daily_limit"
