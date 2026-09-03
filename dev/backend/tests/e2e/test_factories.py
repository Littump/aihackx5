from datetime import UTC, datetime
from decimal import Decimal

import pytest
from psycopg import AsyncConnection
from psycopg.types.json import Jsonb

from app.features.challenges.models import ChallengeEconomics, ChallengeRow
from app.features.domovoy.models import DomovoyStateRow
from app.features.receipts.models import ReceiptRow
from app.features.user_features.models import UserFeaturesRow
from app.features.users.models import StoreRow, UserRow
from app.game_rules import FEATURES_WINDOW_WEEKS

from .. import factories
from . import factories_data as data


async def test_make_store_returns_store_row(conn: AsyncConnection) -> None:
    store = await factories.make_store(conn)
    assert isinstance(store, StoreRow)
    assert store.chain == "pyaterochka"
    assert store.id > 0


async def test_make_user_returns_user_row(conn: AsyncConnection) -> None:
    store = await factories.make_store(conn)
    user = await factories.make_user(conn, favourite_store_id=store.id)
    assert isinstance(user, UserRow)
    assert user.favourite_store_id == store.id
    assert user.segment == "regular_mid"
    assert user.social_propensity == Decimal("0")


async def test_make_receipt_without_args_has_three_items_two_categories(
    conn: AsyncConnection,
) -> None:
    user = await factories.make_user(conn)
    receipt = await factories.make_receipt(conn, user.id)
    assert isinstance(receipt, ReceiptRow)
    cur = await conn.execute(
        "SELECT category FROM receipt_items WHERE receipt_id = %(id)s", {"id": receipt.id}
    )
    categories = [row[0] for row in await cur.fetchall()]
    assert len(categories) == 3
    assert len(set(categories)) == 2
    assert receipt.regular_total == data.DEFAULT_RECEIPT_REGULAR_TOTAL
    assert receipt.paid_total == data.DEFAULT_RECEIPT_PAID_TOTAL
    assert receipt.discount_total == data.DEFAULT_RECEIPT_DISCOUNT_TOTAL


@pytest.mark.parametrize(
    ("items", "regular_total", "paid_total", "discount_total"), data.RECEIPT_ITEM_CASES
)
async def test_make_receipt_computes_totals_from_items(
    conn: AsyncConnection,
    items: list[dict[str, object]],
    regular_total: Decimal,
    paid_total: Decimal,
    discount_total: Decimal,
) -> None:
    user = await factories.make_user(conn)
    receipt = await factories.make_receipt(conn, user.id, items=items)
    assert receipt.regular_total == regular_total
    assert receipt.paid_total == paid_total
    assert receipt.discount_total == discount_total


async def test_make_receipt_reuses_given_store(conn: AsyncConnection) -> None:
    store = await factories.make_store(conn)
    user = await factories.make_user(conn)
    receipt = await factories.make_receipt(conn, user.id, store_id=store.id)
    assert receipt.store_id == store.id


async def test_make_challenge_returns_challenge_row(conn: AsyncConnection) -> None:
    user = await factories.make_user(conn)
    challenge = await factories.make_challenge(conn, user.id, is_hero=False)
    assert isinstance(challenge, ChallengeRow)
    assert challenge.user_id == user.id
    assert challenge.is_hero is False
    assert challenge.status == "active"
    assert challenge.baseline == Decimal("2")


async def test_make_domovoy_state_returns_domovoy_state_row(conn: AsyncConnection) -> None:
    user = await factories.make_user(conn)
    state = await factories.make_domovoy_state(conn, user.id, mood="cheerful")
    assert isinstance(state, DomovoyStateRow)
    assert state.user_id == user.id
    assert state.mood == "cheerful"
    assert state.xp == 0


async def test_make_user_features_returns_user_features_row(conn: AsyncConnection) -> None:
    user = await factories.make_user(conn)
    features = await factories.make_user_features(conn, user.id)
    assert isinstance(features, UserFeaturesRow)
    assert features.user_id == user.id
    assert features.window_weeks == FEATURES_WINDOW_WEEKS
    assert features.category_affinity == {}
    assert features.weekday_pattern == []


async def test_make_store_overrides_all_fields(conn: AsyncConnection) -> None:
    store = await factories.make_store(
        conn,
        name="Перекрёсток, Тверская 1",
        chain="perekrestok",
        district="Тверской",
        city="Санкт-Петербург",
    )
    assert store.name == "Перекрёсток, Тверская 1"
    assert store.chain == "perekrestok"
    assert store.district == "Тверской"
    assert store.city == "Санкт-Петербург"


async def test_make_user_overrides_all_fields(conn: AsyncConnection) -> None:
    referrer = await factories.make_user(conn)
    user = await factories.make_user(
        conn,
        segment="heavy",
        device_fingerprint="fp-123",
        referred_by_user_id=referrer.id,
        social_propensity=Decimal("0.456"),
    )
    assert user.segment == "heavy"
    assert user.device_fingerprint == "fp-123"
    assert user.referred_by_user_id == referrer.id
    assert user.social_propensity == Decimal("0.456")


async def test_make_receipt_empty_items_is_zero_total_boundary(conn: AsyncConnection) -> None:
    user = await factories.make_user(conn)
    receipt = await factories.make_receipt(conn, user.id, items=[])
    assert receipt.regular_total == Decimal("0.00")
    assert receipt.paid_total == Decimal("0.00")
    assert receipt.discount_total == Decimal("0.00")
    cur = await conn.execute(
        "SELECT count(*) FROM receipt_items WHERE receipt_id = %(id)s", {"id": receipt.id}
    )
    row = await cur.fetchone()
    assert row is not None
    assert row[0] == 0


async def test_make_receipt_return_boundary_overrides(conn: AsyncConnection) -> None:
    user = await factories.make_user(conn)
    returned_at = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
    receipt = await factories.make_receipt(conn, user.id, is_returned=True, returned_at=returned_at)
    assert receipt.is_returned is True
    assert receipt.returned_at == returned_at


async def test_make_receipt_counted_false_override(conn: AsyncConnection) -> None:
    user = await factories.make_user(conn)
    receipt = await factories.make_receipt(conn, user.id, counted=False)
    assert receipt.counted is False


async def test_make_receipt_creates_own_store_per_call_by_default(
    conn: AsyncConnection,
) -> None:
    user = await factories.make_user(conn)
    first = await factories.make_receipt(conn, user.id)
    second = await factories.make_receipt(conn, user.id)
    assert first.store_id != second.store_id


async def test_make_challenge_overrides_zero_baseline_and_jsonb(conn: AsyncConnection) -> None:
    user = await factories.make_user(conn)
    economics = {
        "avg_basket": 600.0,
        "expected_incremental_purchases": 1.0,
        "expected_incremental_margin": 90.0,
        "max_reward_rub": 36.0,
        "contribution_margin": 0.15,
        "reward_share_max": 0.4,
    }
    challenge = await factories.make_challenge(
        conn,
        user.id,
        status="completed",
        baseline=Decimal("0"),
        target=Decimal("1"),
        economics=Jsonb(economics),
        rationale_features=Jsonb({"frequency_per_week": 2.3}),
    )
    assert challenge.status == "completed"
    assert challenge.baseline == Decimal("0")
    assert challenge.economics == ChallengeEconomics(**economics)
    assert challenge.rationale_features == {"frequency_per_week": 2.3}


async def test_make_domovoy_state_overrides_fields(conn: AsyncConnection) -> None:
    user = await factories.make_user(conn)
    state = await factories.make_domovoy_state(
        conn,
        user.id,
        xp=320,
        level=4,
        streak_weeks=3,
        streak_freeze_available=False,
        items=Jsonb(["hat", "scarf"]),
    )
    assert state.xp == 320
    assert state.level == 4
    assert state.streak_weeks == 3
    assert state.streak_freeze_available is False
    assert state.items == ["hat", "scarf"]


async def test_make_user_features_overrides_fields(conn: AsyncConnection) -> None:
    user = await factories.make_user(conn)
    features = await factories.make_user_features(
        conn,
        user.id,
        frequency_per_week=Decimal("2.500"),
        recency_days=3,
        cadence_days=Decimal("3.50"),
        category_affinity=Jsonb({"dairy": {"share": 0.21, "visits": 6, "cadence_days": 5.8}}),
        weekday_pattern=Jsonb([0.1, 0.2, 0.7]),
        realized_savings_30d=Decimal("450.00"),
    )
    assert features.frequency_per_week == Decimal("2.500")
    assert features.recency_days == 3
    assert features.cadence_days == Decimal("3.50")
    assert features.category_affinity["dairy"].share == 0.21
    assert features.weekday_pattern == [0.1, 0.2, 0.7]
    assert features.realized_savings_30d == Decimal("450.00")
