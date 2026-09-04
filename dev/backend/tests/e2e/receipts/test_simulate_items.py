from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal

from httpx import AsyncClient
from psycopg import AsyncConnection

from app.core.clock import week_end, week_start
from app.features.receipts import catalog
from tests.e2e.receipts.data import RECEIPT_PROCESSING_RESULT_FIELDS
from tests.factories import make_challenge, make_store, make_user, make_user_features

NOW = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)
DAIRY_ITEM = {"category": "dairy", "price": 120.0}
BAKERY_ITEM = {"category": "bakery", "price": 80.0}


async def _user_with_dairy_goal(conn: AsyncConnection) -> tuple[int, int]:
    user = await make_user(conn)
    store = await make_store(conn)
    await make_user_features(conn, user.id, favourite_store_id=store.id)
    challenge = await make_challenge(
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
    return user.id, challenge.id


async def test_confirmed_items_become_the_receipt(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    store = await make_store(conn)
    await make_user_features(conn, user.id, favourite_store_id=store.id)

    response = await client.post(
        f"/api/v1/users/{user.id}/receipts/simulate",
        json={"items": [DAIRY_ITEM, BAKERY_ITEM]},
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body.keys()) == RECEIPT_PROCESSING_RESULT_FIELDS
    assert body["counted"] is True
    items = body["receipt"]["items"]
    assert [item["category"] for item in items] == ["dairy", "bakery"]
    assert [item["paid_price"] for item in items] == [120.0, 80.0]
    assert body["receipt"]["paid_total"] == 200.0
    assert body["receipt"]["discount_total"] == 0.0


async def test_item_of_goal_category_moves_hero_progress(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user_id, challenge_id = await _user_with_dairy_goal(conn)

    response = await client.post(
        f"/api/v1/users/{user_id}/receipts/simulate", json={"items": [DAIRY_ITEM]}
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body["challenges"]) == 1
    assert body["challenges"][0]["challenge_id"] == challenge_id
    assert body["challenges"][0]["progress_after"] == 1.0


async def test_receipt_without_goal_category_leaves_hero_progress_untouched(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user_id, _ = await _user_with_dairy_goal(conn)

    response = await client.post(
        f"/api/v1/users/{user_id}/receipts/simulate", json={"items": [BAKERY_ITEM]}
    )

    assert response.status_code == 201
    assert response.json()["challenges"] == []


async def test_promo_item_creates_discount_and_savings(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    store = await make_store(conn)
    await make_user_features(conn, user.id, favourite_store_id=store.id)

    response = await client.post(
        f"/api/v1/users/{user.id}/receipts/simulate",
        json={"items": [{"category": "dairy", "price": 80.0, "is_promo": True}]},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["receipt"]["paid_total"] == 80.0
    assert body["receipt"]["regular_total"] == 100.0
    assert body["receipt"]["discount_total"] == 20.0
    assert body["savings_delta"] == 20.0


async def test_item_without_product_name_gets_generated_name(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    store = await make_store(conn)
    await make_user_features(conn, user.id, favourite_store_id=store.id)

    response = await client.post(
        f"/api/v1/users/{user.id}/receipts/simulate", json={"items": [DAIRY_ITEM]}
    )

    assert response.status_code == 201
    assert (
        response.json()["receipt"]["items"][0]["product_name"] == catalog.products_for("dairy")[0]
    )


async def test_items_override_fraud_burst_scenario(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    store = await make_store(conn)
    await make_user_features(conn, user.id, favourite_store_id=store.id)

    response = await client.post(
        f"/api/v1/users/{user.id}/receipts/simulate",
        json={"scenario": "fraud_burst", "items": [DAIRY_ITEM]},
    )

    assert response.status_code == 201
    assert response.json()["counted"] is True
    cursor = await conn.execute("SELECT count(*) FROM receipts WHERE user_id = %s", (user.id,))
    row = await cursor.fetchone()
    assert row is not None
    assert row[0] == 1


async def test_unknown_category_returns_422(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    await make_store(conn)

    response = await client.post(
        f"/api/v1/users/{user.id}/receipts/simulate",
        json={"items": [{"category": "crypto", "price": 10.0}]},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unknown_category"


async def test_empty_items_list_returns_422(client: AsyncClient, conn: AsyncConnection) -> None:
    user = await make_user(conn)

    response = await client.post(f"/api/v1/users/{user.id}/receipts/simulate", json={"items": []})

    assert response.status_code == 422


async def test_too_many_items_returns_422(client: AsyncClient, conn: AsyncConnection) -> None:
    user = await make_user(conn)

    response = await client.post(
        f"/api/v1/users/{user.id}/receipts/simulate", json={"items": [DAIRY_ITEM] * 21}
    )

    assert response.status_code == 422


async def test_negative_price_returns_422(client: AsyncClient, conn: AsyncConnection) -> None:
    user = await make_user(conn)

    response = await client.post(
        f"/api/v1/users/{user.id}/receipts/simulate",
        json={"items": [{"category": "dairy", "price": -1}]},
    )

    assert response.status_code == 422
