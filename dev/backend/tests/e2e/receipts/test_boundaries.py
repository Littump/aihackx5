from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from httpx import AsyncClient
from psycopg import AsyncConnection

from tests.e2e.receipts.data import ONE_ITEM_PAYLOAD
from tests.factories import make_receipt, make_store, make_user

BASE_TIME = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)
MSK = ZoneInfo("Europe/Moscow")


def _payload(
    user_id: int, store_id: int, purchased_at: datetime, items: list[dict[str, object]]
) -> dict[str, object]:
    return {
        "user_id": user_id,
        "store_id": store_id,
        "purchased_at": purchased_at.isoformat(),
        "items": items,
    }


async def test_second_receipt_exactly_at_dedup_window_boundary_is_counted(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)
    store = await make_store(conn)
    await client.post(
        "/api/v1/receipts", json=_payload(user.id, store.id, BASE_TIME, ONE_ITEM_PAYLOAD)
    )

    exactly_on_boundary = BASE_TIME + timedelta(minutes=30)
    response = await client.post(
        "/api/v1/receipts",
        json=_payload(user.id, store.id, exactly_on_boundary, ONE_ITEM_PAYLOAD),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["counted"] is True
    assert body["counted_reason"] is None


async def test_daily_limit_resets_after_moscow_midnight(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)
    store = await make_store(conn)
    late_evening = datetime(2026, 9, 2, 20, 0, tzinfo=MSK)
    for hour_offset in (0, 1, 2):
        moment = late_evening + timedelta(hours=hour_offset)
        response = await client.post(
            "/api/v1/receipts", json=_payload(user.id, store.id, moment, ONE_ITEM_PAYLOAD)
        )
        assert response.json()["counted"] is True

    just_after_midnight = late_evening + timedelta(hours=4, minutes=5)
    response = await client.post(
        "/api/v1/receipts",
        json=_payload(user.id, store.id, just_after_midnight, ONE_ITEM_PAYLOAD),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["counted"] is True
    assert body["counted_reason"] is None


async def test_list_receipts_returns_empty_items_when_no_receipts(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)

    response = await client.get(f"/api/v1/users/{user.id}/receipts")

    assert response.status_code == 200
    assert response.json() == {"items": []}


async def test_list_receipts_limit_truncates_to_most_recent(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)
    receipts = [
        await make_receipt(conn, user.id, purchased_at=BASE_TIME + timedelta(hours=i))
        for i in range(5)
    ]

    response = await client.get(f"/api/v1/users/{user.id}/receipts", params={"limit": 2})

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["id"] for item in items] == [receipts[4].id, receipts[3].id]


async def test_process_receipt_numeric_field_types_match_contract(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)
    store = await make_store(conn)

    response = await client.post(
        "/api/v1/receipts", json=_payload(user.id, store.id, BASE_TIME, ONE_ITEM_PAYLOAD)
    )

    body = response.json()
    receipt = body["receipt"]
    assert isinstance(receipt["id"], int)
    assert isinstance(receipt["store_id"], int)
    assert isinstance(receipt["regular_total"], float)
    assert isinstance(receipt["paid_total"], float)
    assert isinstance(receipt["discount_total"], float)
    assert isinstance(receipt["points_earned"], int)
    assert isinstance(receipt["points_spent"], int)
    assert isinstance(receipt["counted"], bool)
    assert isinstance(receipt["is_returned"], bool)
    item = receipt["items"][0]
    assert isinstance(item["qty"], float)
    assert isinstance(item["regular_price"], float)
    assert isinstance(item["paid_price"], float)
    assert isinstance(item["is_promo"], bool)
    assert isinstance(body["xp_delta"], int)
    assert isinstance(body["savings_delta"], float)
    assert isinstance(body["fraud"]["score"], float)
    assert body["domovoy"]["items"] == []
    assert body["fraud"]["signals"] == []
    assert body["challenges"] == []
    assert body["achievements_unlocked"] == []
    assert isinstance(body["league_rank_before"], int)
    assert isinstance(body["league_rank_after"], int)
    assert body["referral_status"] is None
