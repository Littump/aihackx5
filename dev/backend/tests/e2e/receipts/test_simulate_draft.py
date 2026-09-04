from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal

from httpx import AsyncClient
from psycopg import AsyncConnection
from psycopg.types.json import Jsonb

from app.core.clock import week_end, week_start
from app.game_rules import (
    CATEGORIES,
    SIMULATE_DRAFT_DEFAULT_PRICE,
    SIMULATE_DRAFT_ITEMS_MAX,
    SIMULATE_DRAFT_ITEMS_MIN,
)
from tests.e2e.receipts.data import (
    SIMULATE_DRAFT_FIELDS,
    SIMULATE_DRAFT_GOAL_FIELDS,
    SIMULATE_DRAFT_ITEM_FIELDS,
)
from tests.factories import make_challenge, make_store, make_user, make_user_features

NOW = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)
DAIRY_AFFINITY = Jsonb({"dairy": {"share": 0.8, "visits": 6, "cadence_days": 4.0}})


async def test_draft_returns_editable_basket_by_contract(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    store = await make_store(conn)
    await make_user_features(conn, user.id, favourite_store_id=store.id)

    response = await client.get(f"/api/v1/users/{user.id}/receipts/simulate/draft")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == SIMULATE_DRAFT_FIELDS
    assert body["store_id"] == store.id
    assert body["store_name"] == store.name
    assert body["goal"] is None
    assert body["categories"] == list(CATEGORIES)
    assert body["default_price"] == SIMULATE_DRAFT_DEFAULT_PRICE
    assert SIMULATE_DRAFT_ITEMS_MIN <= len(body["items"]) <= SIMULATE_DRAFT_ITEMS_MAX
    for item in body["items"]:
        assert set(item.keys()) == SIMULATE_DRAFT_ITEM_FIELDS
        assert item["category"] in CATEGORIES
        assert item["price"] > 0
        assert item["matches_goal"] is False


async def test_draft_includes_goal_category_item_when_hero_is_category(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    store = await make_store(conn)
    await make_user_features(conn, user.id, favourite_store_id=store.id)
    await make_challenge(
        conn,
        user.id,
        type="category",
        category="meat_fish",
        progress=Decimal("1"),
        target=Decimal("3"),
        is_hero=True,
        period_start=week_start(),
        period_end=week_end(),
    )

    response = await client.get(f"/api/v1/users/{user.id}/receipts/simulate/draft")

    assert response.status_code == 200
    body = response.json()
    assert set(body["goal"].keys()) == SIMULATE_DRAFT_GOAL_FIELDS
    assert body["goal"]["type"] == "category"
    assert body["goal"]["category"] == "meat_fish"
    assert body["goal"]["progress"] == 1.0
    assert body["goal"]["target"] == 3.0
    matching = [item for item in body["items"] if item["matches_goal"]]
    assert matching
    assert all(item["category"] == "meat_fish" for item in matching)


async def test_draft_with_frequency_hero_marks_no_item_as_goal(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    store = await make_store(conn)
    await make_user_features(
        conn, user.id, favourite_store_id=store.id, category_affinity=DAIRY_AFFINITY
    )
    await make_challenge(
        conn,
        user.id,
        type="frequency",
        category=None,
        is_hero=True,
        period_start=week_start(),
        period_end=week_end(),
    )

    response = await client.get(f"/api/v1/users/{user.id}/receipts/simulate/draft")

    assert response.status_code == 200
    body = response.json()
    assert body["goal"]["type"] == "frequency"
    assert body["goal"]["category"] is None
    assert all(item["matches_goal"] is False for item in body["items"])


async def test_draft_explicit_store_id_overrides_favourite_store(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    favourite_store = await make_store(conn)
    requested_store = await make_store(conn)
    await make_user_features(conn, user.id, favourite_store_id=favourite_store.id)

    response = await client.get(
        f"/api/v1/users/{user.id}/receipts/simulate/draft?store_id={requested_store.id}"
    )

    assert response.status_code == 200
    assert response.json()["store_id"] == requested_store.id


async def test_draft_unknown_user_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users/999999/receipts/simulate/draft")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "user_not_found"


async def test_draft_without_any_store_returns_404(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)

    response = await client.get(f"/api/v1/users/{user.id}/receipts/simulate/draft")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "no_stores_available"


async def test_draft_items_can_be_confirmed_as_is(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    store = await make_store(conn)
    await make_user_features(conn, user.id, favourite_store_id=store.id)

    draft_body = (await client.get(f"/api/v1/users/{user.id}/receipts/simulate/draft")).json()
    items = [
        {
            "product_name": item["product_name"],
            "category": item["category"],
            "price": item["price"],
            "is_promo": item["is_promo"],
        }
        for item in draft_body["items"]
    ]
    response = await client.post(
        f"/api/v1/users/{user.id}/receipts/simulate", json={"items": items}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["counted"] is True
    assert len(body["receipt"]["items"]) == len(items)
    assert body["receipt"]["paid_total"] == round(sum(item["price"] for item in items), 2)
