from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from httpx import AsyncClient
from psycopg import AsyncConnection

from app.features.user_features import database as user_features_db
from app.features.user_features import service as user_features_service
from app.game_rules import FEATURES_WINDOW_WEEKS, USER_FEATURES_RECENCY_NO_HISTORY_DAYS
from tests.factories import make_receipt, make_store, make_user

PURCHASED_AT = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)
ITEMS_PAYLOAD = [
    {
        "product_name": "Молоко",
        "category": "dairy",
        "qty": 1,
        "regular_price": 100.0,
        "paid_price": 80.0,
        "is_promo": True,
    }
]


def _payload(user_id: int, store_id: int, purchased_at: datetime) -> dict[str, object]:
    return {
        "user_id": user_id,
        "store_id": store_id,
        "purchased_at": purchased_at.isoformat(),
        "items": ITEMS_PAYLOAD,
    }


async def test_post_receipt_creates_user_features_row(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(PURCHASED_AT)
    user = await make_user(conn)
    store = await make_store(conn, chain="pyaterochka")

    response = await client.post("/api/v1/receipts", json=_payload(user.id, store.id, PURCHASED_AT))

    assert response.status_code == 201
    features = await user_features_db.get_user_features_by_user_id(conn, user_id=user.id)
    assert features is not None
    assert features.window_weeks == FEATURES_WINDOW_WEEKS
    assert features.frequency_per_week == Decimal("0.100")
    assert features.recency_days == 0
    assert features.avg_basket == Decimal("80.00")
    assert features.promo_sensitivity == Decimal("1.000")
    assert features.favourite_store_id == store.id
    assert features.cross_chain_share == Decimal("0")
    assert features.category_affinity["dairy"].visits == 1


async def test_second_receipt_updates_existing_user_features_row(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(PURCHASED_AT)
    user = await make_user(conn)
    store = await make_store(conn, chain="pyaterochka")
    await client.post("/api/v1/receipts", json=_payload(user.id, store.id, PURCHASED_AT))

    later = PURCHASED_AT + timedelta(days=3)
    freeze_time(later)
    await client.post("/api/v1/receipts", json=_payload(user.id, store.id, later))

    features = await user_features_db.get_user_features_by_user_id(conn, user_id=user.id)
    assert features is not None
    assert features.frequency_per_week == Decimal("0.200")
    assert features.recency_days == 0
    assert features.avg_basket == Decimal("80.00")


async def test_no_history_persists_recency_sentinel_not_null(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(PURCHASED_AT)
    user = await make_user(conn)

    computed = await user_features_service.recompute(conn, user.id)

    assert computed.recency_days == USER_FEATURES_RECENCY_NO_HISTORY_DAYS
    stored = await user_features_db.get_user_features_by_user_id(conn, user_id=user.id)
    assert stored is not None
    assert stored.recency_days == USER_FEATURES_RECENCY_NO_HISTORY_DAYS
    assert stored.favourite_store_id is None
    assert stored.cadence_days is None


async def test_favourite_store_tie_goes_to_last_store_via_http(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(PURCHASED_AT)
    user = await make_user(conn)
    store_a = await make_store(conn, chain="pyaterochka")
    store_b = await make_store(conn, chain="perekrestok")
    await client.post("/api/v1/receipts", json=_payload(user.id, store_a.id, PURCHASED_AT))

    later = PURCHASED_AT + timedelta(days=1)
    freeze_time(later)
    await client.post("/api/v1/receipts", json=_payload(user.id, store_b.id, later))

    features = await user_features_db.get_user_features_by_user_id(conn, user_id=user.id)
    assert features is not None
    assert features.favourite_store_id == store_b.id


async def test_dedup_receipt_recomputes_without_inflating_frequency(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(PURCHASED_AT)
    user = await make_user(conn)
    store = await make_store(conn, chain="pyaterochka")
    await client.post("/api/v1/receipts", json=_payload(user.id, store.id, PURCHASED_AT))

    dedup_time = PURCHASED_AT + timedelta(minutes=10)
    freeze_time(dedup_time)
    response = await client.post("/api/v1/receipts", json=_payload(user.id, store.id, dedup_time))

    assert response.json()["counted"] is False
    features = await user_features_db.get_user_features_by_user_id(conn, user_id=user.id)
    assert features is not None
    assert features.frequency_per_week == Decimal("0.100")


async def test_returned_receipt_excluded_from_features(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(PURCHASED_AT)
    user = await make_user(conn)
    await make_receipt(conn, user.id, purchased_at=PURCHASED_AT, is_returned=True)
    await make_receipt(conn, user.id, purchased_at=PURCHASED_AT)

    features = await user_features_service.recompute(conn, user.id)

    assert features.frequency_per_week == Decimal("0.100")
