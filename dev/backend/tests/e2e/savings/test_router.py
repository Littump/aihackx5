from collections.abc import Callable
from datetime import UTC, datetime

from httpx import AsyncClient
from psycopg import AsyncConnection

from tests.e2e.savings.data import AC_ITEM, SAVINGS_CATEGORY_FIELDS, SAVINGS_FIELDS
from tests.factories import make_receipt, make_user

NOW = datetime(2026, 9, 15, 10, 0, tzinfo=UTC)


async def test_get_savings_happy_path_matches_ac_example(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    await make_receipt(
        conn, user.id, purchased_at=NOW, items=AC_ITEM, points_earned=10, points_spent=50
    )

    response = await client.get(f"/api/v1/users/{user.id}/savings", params={"period": "month"})

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == SAVINGS_FIELDS
    assert body["period"] == "month"
    assert body["amount"] == 210.0
    assert body["previous_amount"] == 0.0
    assert body["delta"] == 210.0
    assert body["discount_amount"] == 150.0
    assert body["points_earned"] == 10
    assert body["points_spent"] == 50
    for category in body["top_categories"]:
        assert set(category.keys()) == SAVINGS_CATEGORY_FIELDS


async def test_get_savings_default_period_is_month(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)

    response = await client.get(f"/api/v1/users/{user.id}/savings")

    assert response.status_code == 200
    assert response.json()["period"] == "month"


async def test_get_savings_unknown_user_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users/999999/savings")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "user_not_found"


async def test_get_savings_invalid_period_returns_422(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)

    response = await client.get(f"/api/v1/users/{user.id}/savings", params={"period": "year"})

    assert response.status_code == 422


async def test_get_savings_field_types_match_contract(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    await make_receipt(conn, user.id, purchased_at=NOW)

    response = await client.get(f"/api/v1/users/{user.id}/savings")

    body = response.json()
    assert isinstance(body["amount"], float)
    assert isinstance(body["previous_amount"], float)
    assert isinstance(body["delta"], float)
    assert isinstance(body["discount_amount"], float)
    assert isinstance(body["points_earned"], int)
    assert isinstance(body["points_spent"], int)
    assert isinstance(body["top_categories"], list)
