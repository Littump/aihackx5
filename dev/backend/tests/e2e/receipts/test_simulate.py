from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from psycopg import AsyncConnection
from psycopg.types.json import Jsonb

from app.core.clock import week_end, week_start
from app.game_rules import (
    SIMULATE_BASKET_VARIATION_MAX,
    SIMULATE_BASKET_VARIATION_MIN,
    SIMULATE_DEFAULT_AVG_BASKET,
    SIMULATE_FRAUD_BURST_INTERVAL_MIN,
)
from tests.e2e.receipts.data import RECEIPT_FIELDS, RECEIPT_PROCESSING_RESULT_FIELDS
from tests.factories import make_challenge, make_store, make_user, make_user_features

NOW = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)
DAIRY_AFFINITY = Jsonb({"dairy": {"share": 0.8, "visits": 6, "cadence_days": 4.0}})
NO_BODY_VARIANTS: list[dict[str, object] | None] = [None, {}, {"scenario": "typical"}]


async def test_simulate_typical_returns_counted_receipt_with_sum_in_range(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    store = await make_store(conn)
    await make_user_features(conn, user.id, avg_basket=Decimal("600"))

    response = await client.post(
        f"/api/v1/users/{user.id}/receipts/simulate", json={"store_id": store.id}
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body.keys()) == RECEIPT_PROCESSING_RESULT_FIELDS
    assert set(body["receipt"].keys()) == RECEIPT_FIELDS
    assert body["counted"] is True
    assert body["receipt"]["store_id"] == store.id
    lower = 600 * SIMULATE_BASKET_VARIATION_MIN
    upper = 600 * SIMULATE_BASKET_VARIATION_MAX
    assert lower <= body["receipt"]["regular_total"] <= upper
    assert 3 <= len(body["receipt"]["items"]) <= 6


@pytest.mark.parametrize("payload", NO_BODY_VARIANTS)
async def test_simulate_request_body_is_fully_optional(
    client: AsyncClient,
    conn: AsyncConnection,
    freeze_time: Callable[[datetime], None],
    payload: dict[str, object] | None,
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    store = await make_store(conn)
    await make_user_features(conn, user.id, favourite_store_id=store.id)

    url = f"/api/v1/users/{user.id}/receipts/simulate"
    response = await client.post(url) if payload is None else await client.post(url, json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["counted"] is True
    assert body["receipt"]["store_id"] == store.id


async def test_simulate_invalid_scenario_returns_422(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)

    response = await client.post(
        f"/api/v1/users/{user.id}/receipts/simulate", json={"scenario": "unknown"}
    )

    assert response.status_code == 422
    assert set(response.json()["error"].keys()) == {"code", "message"}


async def test_simulate_explicit_store_id_overrides_favourite_store(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    favourite_store = await make_store(conn)
    requested_store = await make_store(conn)
    await make_user_features(conn, user.id, favourite_store_id=favourite_store.id)

    response = await client.post(
        f"/api/v1/users/{user.id}/receipts/simulate", json={"store_id": requested_store.id}
    )

    assert response.status_code == 201
    assert response.json()["receipt"]["store_id"] == requested_store.id


async def test_simulate_unknown_store_id_returns_404_not_500(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)

    response = await client.post(
        f"/api/v1/users/{user.id}/receipts/simulate", json={"store_id": 999999}
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "store_not_found"


async def test_simulate_without_store_or_favourite_falls_back_to_default_store(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    store = await make_store(conn)

    response = await client.post(f"/api/v1/users/{user.id}/receipts/simulate", json={})

    assert response.status_code == 201
    assert response.json()["receipt"]["store_id"] == store.id


async def test_simulate_new_user_without_history_uses_default_avg_basket_range(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    await make_store(conn)

    response = await client.post(f"/api/v1/users/{user.id}/receipts/simulate")

    assert response.status_code == 201
    total = response.json()["receipt"]["regular_total"]
    lower = SIMULATE_DEFAULT_AVG_BASKET * SIMULATE_BASKET_VARIATION_MIN
    upper = SIMULATE_DEFAULT_AVG_BASKET * SIMULATE_BASKET_VARIATION_MAX
    assert lower <= total <= upper


async def test_simulate_no_stores_available_returns_no_stores_available_error(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)

    response = await client.post(f"/api/v1/users/{user.id}/receipts/simulate")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "no_stores_available"


async def test_simulate_category_boost_moves_category_hero_progress(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    store = await make_store(conn)
    await make_user_features(
        conn, user.id, favourite_store_id=store.id, category_affinity=DAIRY_AFFINITY
    )
    hero = await make_challenge(
        conn,
        user.id,
        type="category",
        category="dairy",
        baseline=Decimal("2"),
        target=Decimal("3"),
        progress=Decimal("0"),
        is_hero=True,
        period_start=week_start(),
        period_end=week_end(),
    )

    response = await client.post(
        f"/api/v1/users/{user.id}/receipts/simulate", json={"scenario": "category_boost"}
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body["challenges"]) == 1
    assert body["challenges"][0]["challenge_id"] == hero.id
    assert body["challenges"][0]["progress_after"] == 1.0
    categories = {item["category"] for item in body["receipt"]["items"]}
    assert "dairy" in categories


async def test_simulate_category_boost_without_category_hero_behaves_like_typical(
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
        baseline=Decimal("1"),
        target=Decimal("2"),
        progress=Decimal("0"),
        is_hero=True,
        period_start=week_start(),
        period_end=week_end(),
    )

    response = await client.post(
        f"/api/v1/users/{user.id}/receipts/simulate",
        json={"scenario": "category_boost", "store_id": store.id},
    )

    assert response.status_code == 201
    assert response.json()["counted"] is True


async def test_simulate_category_boost_without_any_active_challenges_behaves_like_typical(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    store = await make_store(conn)
    await make_user_features(conn, user.id, favourite_store_id=store.id)

    response = await client.post(
        f"/api/v1/users/{user.id}/receipts/simulate", json={"scenario": "category_boost"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["counted"] is True
    assert body["challenges"] == []


async def test_simulate_fraud_burst_creates_four_receipts_with_at_most_one_counted(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    store = await make_store(conn)
    await make_user_features(conn, user.id, favourite_store_id=store.id)

    response = await client.post(
        f"/api/v1/users/{user.id}/receipts/simulate", json={"scenario": "fraud_burst"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["counted"] is False
    assert body["counted_reason"] == "dedup_window"
    assert body["receipt"]["purchased_at"] == NOW.isoformat().replace("+00:00", "Z")

    total_cursor = await conn.execute(
        "SELECT count(*) FROM receipts WHERE user_id = %s", (user.id,)
    )
    total_row = await total_cursor.fetchone()
    assert total_row is not None
    assert total_row[0] == 4

    counted_cursor = await conn.execute(
        "SELECT count(*) FROM receipts WHERE user_id = %s AND counted = true", (user.id,)
    )
    counted_row = await counted_cursor.fetchone()
    assert counted_row is not None
    assert counted_row[0] <= 1

    times_cursor = await conn.execute(
        "SELECT purchased_at FROM receipts WHERE user_id = %s ORDER BY purchased_at", (user.id,)
    )
    times = [row[0] for row in await times_cursor.fetchall()]
    assert times[-1] == NOW
    interval = timedelta(minutes=SIMULATE_FRAUD_BURST_INTERVAL_MIN)
    assert [times[i + 1] - times[i] for i in range(3)] == [interval, interval, interval]


async def test_simulate_unknown_user_returns_404(client: AsyncClient) -> None:
    response = await client.post("/api/v1/users/999999/receipts/simulate")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "user_not_found"
