from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from psycopg import AsyncConnection

from tests.e2e.savings.data import AC_ITEM, FOUR_CATEGORY_ITEMS
from tests.factories import make_receipt, make_user

NOW = datetime(2026, 9, 15, 10, 0, tzinfo=UTC)


async def test_returned_receipt_excluded_from_savings(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    await make_receipt(
        conn,
        user.id,
        purchased_at=NOW,
        items=AC_ITEM,
        points_earned=10,
        points_spent=50,
        is_returned=True,
    )
    await make_receipt(conn, user.id, purchased_at=NOW, items=AC_ITEM)

    response = await client.get(f"/api/v1/users/{user.id}/savings", params={"period": "month"})

    assert response.json()["amount"] == 150.0


async def test_previous_month_receipt_counted_in_previous_amount(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    last_month = datetime(2026, 8, 20, 10, 0, tzinfo=UTC)
    await make_receipt(
        conn, user.id, purchased_at=last_month, items=AC_ITEM, points_earned=10, points_spent=50
    )

    response = await client.get(f"/api/v1/users/{user.id}/savings", params={"period": "month"})

    body = response.json()
    assert body["amount"] == 0.0
    assert body["previous_amount"] == 210.0
    assert body["delta"] == -210.0


async def test_week_period_uses_last_seven_days_sliding_window(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    within_window = NOW - timedelta(days=6)
    before_window = NOW - timedelta(days=8)
    await make_receipt(
        conn, user.id, purchased_at=within_window, items=AC_ITEM, points_earned=10, points_spent=50
    )
    await make_receipt(
        conn, user.id, purchased_at=before_window, items=AC_ITEM, points_earned=10, points_spent=50
    )

    response = await client.get(f"/api/v1/users/{user.id}/savings", params={"period": "week"})

    body = response.json()
    assert body["period"] == "week"
    assert body["amount"] == 210.0


async def test_top_categories_sorted_by_contribution_and_capped_at_three(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    await make_receipt(conn, user.id, purchased_at=NOW, items=FOUR_CATEGORY_ITEMS)

    response = await client.get(f"/api/v1/users/{user.id}/savings", params={"period": "month"})

    categories = response.json()["top_categories"]
    assert [c["category"] for c in categories] == ["dairy", "bakery", "drinks"]
    assert len(categories) == 3


async def test_receipt_exactly_seven_days_ago_falls_into_previous_week(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    six_days_ago = NOW - timedelta(days=6)
    seven_days_ago = NOW - timedelta(days=7)
    await make_receipt(conn, user.id, purchased_at=six_days_ago, items=AC_ITEM)
    await make_receipt(
        conn, user.id, purchased_at=seven_days_ago, items=AC_ITEM, points_earned=10, points_spent=50
    )

    response = await client.get(f"/api/v1/users/{user.id}/savings", params={"period": "week"})

    body = response.json()
    assert body["amount"] == 150.0
    assert body["previous_amount"] == 210.0


async def test_year_boundary_receipt_counted_in_previous_month(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(datetime(2026, 1, 10, 10, 0, tzinfo=UTC))
    user = await make_user(conn)
    last_december = datetime(2025, 12, 20, 10, 0, tzinfo=UTC)
    await make_receipt(
        conn, user.id, purchased_at=last_december, items=AC_ITEM, points_earned=10, points_spent=50
    )

    response = await client.get(f"/api/v1/users/{user.id}/savings", params={"period": "month"})

    body = response.json()
    assert body["amount"] == 0.0
    assert body["previous_amount"] == 210.0


async def test_empty_history_returns_zero_summary(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)

    response = await client.get(f"/api/v1/users/{user.id}/savings", params={"period": "month"})

    body = response.json()
    assert body["amount"] == 0.0
    assert body["previous_amount"] == 0.0
    assert body["delta"] == 0.0
    assert body["discount_amount"] == 0.0
    assert body["points_earned"] == 0
    assert body["points_spent"] == 0
    assert body["top_categories"] == []
