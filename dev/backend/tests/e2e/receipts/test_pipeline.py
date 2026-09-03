from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient
from psycopg import AsyncConnection

from app.core.clock import week_end, week_start
from app.features.challenges import database as challenges_db
from app.features.challenges import service as challenges_service
from app.features.domovoy import database as domovoy_db
from app.features.domovoy import service as domovoy_service
from app.features.user_features import database as user_features_db
from app.game_rules import XP_ACHIEVEMENT, XP_CHALLENGE, XP_RECEIPT
from tests.e2e.receipts.data import RECEIPT_FIELDS, RECEIPT_PROCESSING_RESULT_FIELDS
from tests.factories import make_challenge, make_store, make_user

PURCHASED_AT = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)
ITEMS_PAYLOAD = [
    {
        "product_name": "Молоко",
        "category": "dairy",
        "qty": 1,
        "regular_price": 100.0,
        "paid_price": 80.0,
    }
]
EXPECTED_SAVINGS_DELTA = 45.0


def _payload(user_id: int, store_id: int) -> dict[str, object]:
    return {
        "user_id": user_id,
        "store_id": store_id,
        "purchased_at": PURCHASED_AT.isoformat(),
        "points_earned": 20,
        "points_spent": 5,
        "items": ITEMS_PAYLOAD,
    }


async def test_process_receipt_happy_path_moves_hero_challenge_and_domovoy(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(PURCHASED_AT)
    user = await make_user(conn)
    store = await make_store(conn)
    hero = await make_challenge(
        conn,
        user.id,
        type="frequency",
        baseline=Decimal("1"),
        target=Decimal("2"),
        progress=Decimal("0"),
        is_hero=True,
        reward_xp=50,
        reward_points=30,
        period_start=week_start(),
        period_end=week_end(),
    )

    response = await client.post("/api/v1/receipts", json=_payload(user.id, store.id))

    assert response.status_code == 201
    body = response.json()
    assert set(body.keys()) == RECEIPT_PROCESSING_RESULT_FIELDS
    assert set(body["receipt"].keys()) == RECEIPT_FIELDS
    assert body["counted"] is True
    # первый счётный чек пользователя разблокирует first_receipt
    expected_xp = XP_RECEIPT + XP_ACHIEVEMENT
    assert body["xp_delta"] == expected_xp
    assert body["domovoy"]["xp"] == expected_xp
    assert body["achievements_unlocked"] == ["first_receipt"]
    assert body["savings_delta"] == EXPECTED_SAVINGS_DELTA
    assert len(body["challenges"]) == 1
    challenge_delta = body["challenges"][0]
    assert challenge_delta["challenge_id"] == hero.id
    assert challenge_delta["progress_before"] == 0.0
    assert challenge_delta["progress_after"] == 1.0
    assert challenge_delta["completed"] is False

    receipts_count = await conn.execute(
        "SELECT count(*) FROM receipts WHERE user_id = %s", (user.id,)
    )
    row = await receipts_count.fetchone()
    assert row is not None
    assert row[0] == 1

    features = await user_features_db.get_user_features_by_user_id(conn, user_id=user.id)
    assert features is not None
    assert features.frequency_per_week != Decimal("0")

    state = await domovoy_db.get_domovoy_state(conn, user_id=user.id)
    assert state is not None
    assert state.xp == expected_xp

    challenge = await challenges_db.get_challenge_by_id(conn, challenge_id=hero.id)
    assert challenge is not None
    assert challenge.progress == Decimal("1")


async def test_process_receipt_completing_hero_challenge_combines_xp_and_streak(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(PURCHASED_AT)
    user = await make_user(conn)
    store = await make_store(conn)
    hero = await make_challenge(
        conn,
        user.id,
        type="frequency",
        baseline=Decimal("1"),
        target=Decimal("2"),
        progress=Decimal("1"),
        is_hero=True,
        reward_xp=XP_CHALLENGE,
        reward_points=30,
        period_start=week_start(),
        period_end=week_end(),
    )

    response = await client.post("/api/v1/receipts", json=_payload(user.id, store.id))

    assert response.status_code == 201
    body = response.json()
    # чек первый и завершает челлендж: first_challenge + first_receipt
    expected_achievements_xp = 2 * XP_ACHIEVEMENT
    expected_xp = XP_RECEIPT + XP_CHALLENGE + expected_achievements_xp
    assert body["xp_delta"] == expected_xp
    assert body["domovoy"]["xp"] == expected_xp
    assert body["domovoy"]["streak_weeks"] == 1
    assert body["achievements_unlocked"] == ["first_challenge", "first_receipt"]
    assert len(body["challenges"]) == 1
    challenge_delta = body["challenges"][0]
    assert challenge_delta["challenge_id"] == hero.id
    assert challenge_delta["completed"] is True
    assert challenge_delta["reward_xp"] == XP_CHALLENGE
    assert challenge_delta["reward_points"] == 30

    challenge = await challenges_db.get_challenge_by_id(conn, challenge_id=hero.id)
    assert challenge is not None
    assert challenge.status == "completed"
    assert challenge.progress == Decimal("2")

    state = await domovoy_db.get_domovoy_state(conn, user_id=user.id)
    assert state is not None
    assert state.xp == expected_xp
    assert state.streak_weeks == 1

    ledger_cursor = await conn.execute(
        "SELECT kind, xp_delta, points_delta FROM reward_ledger "
        "WHERE user_id = %s ORDER BY created_at ASC, id ASC",
        (user.id,),
    )
    ledger_rows = await ledger_cursor.fetchall()
    assert ledger_rows == [
        ("receipt_xp", XP_RECEIPT, 0),
        ("challenge", XP_CHALLENGE, 30),
        ("achievement", XP_ACHIEVEMENT, 0),
        ("achievement", XP_ACHIEVEMENT, 0),
    ]


async def test_failure_in_domovoy_step_leaves_nothing_written(
    client: AsyncClient,
    conn: AsyncConnection,
    freeze_time: Callable[[datetime], None],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    freeze_time(PURCHASED_AT)
    user = await make_user(conn)
    store = await make_store(conn)
    hero = await make_challenge(
        conn,
        user.id,
        type="frequency",
        baseline=Decimal("1"),
        target=Decimal("2"),
        progress=Decimal("0"),
        is_hero=True,
        period_start=week_start(),
        period_end=week_end(),
    )

    async def _fail_on_receipt(*args: object, **kwargs: object) -> None:
        raise RuntimeError("boom in domovoy step")

    monkeypatch.setattr(domovoy_service, "on_receipt", _fail_on_receipt)

    with pytest.raises(RuntimeError, match="boom in domovoy step"):
        await client.post("/api/v1/receipts", json=_payload(user.id, store.id))

    receipts_count = await conn.execute(
        "SELECT count(*) FROM receipts WHERE user_id = %s", (user.id,)
    )
    row = await receipts_count.fetchone()
    assert row is not None
    assert row[0] == 0

    items_count = await conn.execute("SELECT count(*) FROM receipt_items")
    items_row = await items_count.fetchone()
    assert items_row is not None
    assert items_row[0] == 0

    features = await user_features_db.get_user_features_by_user_id(conn, user_id=user.id)
    assert features is None

    state = await domovoy_db.get_domovoy_state(conn, user_id=user.id)
    assert state is None

    challenge = await challenges_db.get_challenge_by_id(conn, challenge_id=hero.id)
    assert challenge is not None
    assert challenge.progress == Decimal("0")


async def test_failure_in_challenges_step_leaves_nothing_written(
    client: AsyncClient,
    conn: AsyncConnection,
    freeze_time: Callable[[datetime], None],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    freeze_time(PURCHASED_AT)
    user = await make_user(conn)
    store = await make_store(conn)

    async def _fail_on_receipt(*args: object, **kwargs: object) -> None:
        raise RuntimeError("boom in challenges step")

    monkeypatch.setattr(challenges_service, "on_receipt", _fail_on_receipt)

    with pytest.raises(RuntimeError, match="boom in challenges step"):
        await client.post("/api/v1/receipts", json=_payload(user.id, store.id))

    receipts_count = await conn.execute(
        "SELECT count(*) FROM receipts WHERE user_id = %s", (user.id,)
    )
    row = await receipts_count.fetchone()
    assert row is not None
    assert row[0] == 0

    features = await user_features_db.get_user_features_by_user_id(conn, user_id=user.id)
    assert features is None

    state = await domovoy_db.get_domovoy_state(conn, user_id=user.id)
    assert state is None


async def test_process_receipt_fills_league_rank_before_and_after(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(PURCHASED_AT)
    user = await make_user(conn)
    store = await make_store(conn)

    response = await client.post("/api/v1/receipts", json=_payload(user.id, store.id))

    assert response.status_code == 201
    body = response.json()
    assert body["league_rank_before"] == 1
    assert body["league_rank_after"] == 1
