from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from psycopg import AsyncConnection

from app.game_rules import XP_ACHIEVEMENT, XP_RECEIPT
from tests.e2e.receipts.data import (
    DOMOVOY_STATE_FIELDS,
    FRAUD_DECISION_FIELDS,
    LIMIT_CASES,
    ONE_ITEM_PAYLOAD,
    RECEIPT_FIELDS,
    RECEIPT_PROCESSING_RESULT_FIELDS,
    TWO_ITEM_DISCOUNT_TOTAL,
    TWO_ITEM_PAID_TOTAL,
    TWO_ITEM_PAYLOAD,
    TWO_ITEM_REGULAR_TOTAL,
)
from tests.factories import make_receipt, make_store, make_user

BASE_TIME = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)


def _payload(
    user_id: int, store_id: int, purchased_at: datetime, items: list[dict[str, object]]
) -> dict[str, object]:
    return {
        "user_id": user_id,
        "store_id": store_id,
        "purchased_at": purchased_at.isoformat(),
        "items": items,
    }


async def test_process_receipt_computes_totals_and_matches_contract(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)
    store = await make_store(conn)

    response = await client.post(
        "/api/v1/receipts", json=_payload(user.id, store.id, BASE_TIME, TWO_ITEM_PAYLOAD)
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body.keys()) == RECEIPT_PROCESSING_RESULT_FIELDS
    assert set(body["receipt"].keys()) == RECEIPT_FIELDS
    assert set(body["domovoy"].keys()) == DOMOVOY_STATE_FIELDS
    assert set(body["fraud"].keys()) == FRAUD_DECISION_FIELDS
    assert body["receipt"]["regular_total"] == TWO_ITEM_REGULAR_TOTAL
    assert body["receipt"]["paid_total"] == TWO_ITEM_PAID_TOTAL
    assert body["receipt"]["discount_total"] == TWO_ITEM_DISCOUNT_TOTAL
    assert body["counted"] is True
    assert body["counted_reason"] is None
    # первый счётный чек пользователя разблокирует first_receipt
    expected_xp = XP_RECEIPT + XP_ACHIEVEMENT
    assert body["xp_delta"] == expected_xp
    assert body["domovoy"]["xp"] == expected_xp
    assert body["domovoy"]["level"] == 1
    assert body["domovoy"]["xp_to_next_level"] == 100 - expected_xp
    assert body["fraud"]["decision"] == "approve"
    assert body["achievements_unlocked"] == ["first_receipt"]


async def test_second_receipt_same_store_within_dedup_window_is_not_counted(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)
    store = await make_store(conn)
    await client.post(
        "/api/v1/receipts", json=_payload(user.id, store.id, BASE_TIME, ONE_ITEM_PAYLOAD)
    )

    later = BASE_TIME + timedelta(minutes=10)
    response = await client.post(
        "/api/v1/receipts", json=_payload(user.id, store.id, later, ONE_ITEM_PAYLOAD)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["counted"] is False
    assert body["counted_reason"] == "dedup_window"
    assert body["receipt"]["counted"] is False


async def test_second_receipt_same_store_after_dedup_window_is_counted(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)
    store = await make_store(conn)
    await client.post(
        "/api/v1/receipts", json=_payload(user.id, store.id, BASE_TIME, ONE_ITEM_PAYLOAD)
    )

    later = BASE_TIME + timedelta(minutes=31)
    response = await client.post(
        "/api/v1/receipts", json=_payload(user.id, store.id, later, ONE_ITEM_PAYLOAD)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["counted"] is True
    assert body["counted_reason"] is None


async def test_second_receipt_different_store_within_window_is_counted(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)
    first_store = await make_store(conn)
    second_store = await make_store(conn)
    await client.post(
        "/api/v1/receipts", json=_payload(user.id, first_store.id, BASE_TIME, ONE_ITEM_PAYLOAD)
    )

    later = BASE_TIME + timedelta(minutes=10)
    response = await client.post(
        "/api/v1/receipts", json=_payload(user.id, second_store.id, later, ONE_ITEM_PAYLOAD)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["counted"] is True
    assert body["counted_reason"] is None


async def test_fourth_receipt_same_day_hits_daily_limit(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)
    store = await make_store(conn)
    for hour_offset in (0, 2, 4):
        moment = BASE_TIME + timedelta(hours=hour_offset)
        await client.post(
            "/api/v1/receipts", json=_payload(user.id, store.id, moment, ONE_ITEM_PAYLOAD)
        )

    fourth = BASE_TIME + timedelta(hours=6)
    response = await client.post(
        "/api/v1/receipts", json=_payload(user.id, store.id, fourth, ONE_ITEM_PAYLOAD)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["counted"] is False
    assert body["counted_reason"] == "daily_limit"


async def test_process_receipt_empty_items_returns_422(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)
    store = await make_store(conn)

    response = await client.post(
        "/api/v1/receipts", json=_payload(user.id, store.id, BASE_TIME, [])
    )

    assert response.status_code == 422
    assert set(response.json()["error"].keys()) == {"code", "message"}


async def test_process_receipt_unknown_user_returns_404(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    store = await make_store(conn)

    response = await client.post(
        "/api/v1/receipts", json=_payload(999999, store.id, BASE_TIME, ONE_ITEM_PAYLOAD)
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "user_not_found"


async def test_process_receipt_unknown_store_returns_404(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)

    response = await client.post(
        "/api/v1/receipts", json=_payload(user.id, 999999, BASE_TIME, ONE_ITEM_PAYLOAD)
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "store_not_found"


async def test_list_receipts_sorted_by_purchased_at_desc(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)
    earlier = await make_receipt(conn, user.id, purchased_at=BASE_TIME)
    later = await make_receipt(conn, user.id, purchased_at=BASE_TIME + timedelta(hours=1))

    response = await client.get(f"/api/v1/users/{user.id}/receipts")

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["id"] for item in items] == [later.id, earlier.id]
    assert len(items[0]["items"]) == 3


@pytest.mark.parametrize(("limit", "expected_status"), LIMIT_CASES)
async def test_list_receipts_limit_boundaries(
    client: AsyncClient, conn: AsyncConnection, limit: int, expected_status: int
) -> None:
    user = await make_user(conn)
    await make_receipt(conn, user.id)

    response = await client.get(f"/api/v1/users/{user.id}/receipts", params={"limit": limit})

    assert response.status_code == expected_status


async def test_list_receipts_unknown_user_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users/999999/receipts")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "user_not_found"
