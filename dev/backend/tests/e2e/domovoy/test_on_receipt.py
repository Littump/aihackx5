from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from psycopg import AsyncConnection

from app.features.domovoy import database as domovoy_db
from app.features.domovoy import service as domovoy_service
from app.game_rules import MOOD_SLEEPY_INACTIVITY_DAYS, XP_RECEIPT
from tests.factories import make_domovoy_state, make_receipt, make_user

PURCHASED_AT = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)
NOW = datetime(2026, 9, 2, 18, 0, tzinfo=UTC)
MILK_ITEM: list[dict[str, object]] = [
    {
        "product_name": "Молоко",
        "category": "dairy",
        "qty": Decimal("1"),
        "regular_price": Decimal("100.00"),
        "paid_price": Decimal("90.00"),
    }
]
GROCERY_ITEM: list[dict[str, object]] = [
    {
        "product_name": "Соль",
        "category": "grocery",
        "qty": Decimal("1"),
        "regular_price": Decimal("50.00"),
        "paid_price": Decimal("50.00"),
    }
]


async def test_on_receipt_counted_adds_xp_and_feeds_domovoy(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    receipt = await make_receipt(conn, user.id, items=MILK_ITEM, purchased_at=PURCHASED_AT)

    delta = await domovoy_service.on_receipt(conn, user.id, receipt)

    assert delta.xp_delta == XP_RECEIPT
    assert delta.xp == XP_RECEIPT
    assert delta.mood == "healthy"
    assert delta.last_fed_at == PURCHASED_AT

    state = await domovoy_db.get_domovoy_state(conn, user_id=user.id)
    assert state is not None
    assert state.xp == XP_RECEIPT
    assert state.level == 1
    assert state.last_fed_at == PURCHASED_AT

    ledger_cursor = await conn.execute(
        "SELECT kind, xp_delta, points_delta, ref_type, ref_id "
        "FROM reward_ledger WHERE user_id = %s",
        (user.id,),
    )
    ledger_row = await ledger_cursor.fetchone()
    assert ledger_row == ("receipt_xp", XP_RECEIPT, 0, "receipt", receipt.id)


async def test_on_receipt_not_counted_keeps_xp_unchanged(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    receipt = await make_receipt(
        conn, user.id, items=MILK_ITEM, purchased_at=PURCHASED_AT, counted=False
    )

    delta = await domovoy_service.on_receipt(conn, user.id, receipt)

    assert delta.xp_delta == 0
    assert delta.xp == 0
    assert delta.mood == "sleepy"
    assert delta.last_fed_at is None

    state = await domovoy_db.get_domovoy_state(conn, user_id=user.id)
    assert state is not None
    assert state.xp == 0
    assert state.last_fed_at is None

    ledger_cursor = await conn.execute(
        "SELECT count(*) FROM reward_ledger WHERE user_id = %s", (user.id,)
    )
    ledger_row = await ledger_cursor.fetchone()
    assert ledger_row is not None
    assert ledger_row[0] == 0


async def test_on_receipt_upgrades_level_at_the_100_xp_boundary(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    await make_domovoy_state(conn, user.id, xp=90, level=1)
    receipt = await make_receipt(conn, user.id, items=MILK_ITEM, purchased_at=PURCHASED_AT)

    delta = await domovoy_service.on_receipt(conn, user.id, receipt)

    assert delta.xp == 100
    assert delta.level == 2

    state = await domovoy_db.get_domovoy_state(conn, user_id=user.id)
    assert state is not None
    assert state.xp == 100
    assert state.level == 2


async def test_mood_window_includes_a_receipt_exactly_seven_days_old(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    boundary = NOW - timedelta(days=MOOD_SLEEPY_INACTIVITY_DAYS)
    await make_receipt(conn, user.id, items=GROCERY_ITEM, purchased_at=boundary)
    trigger = await make_receipt(conn, user.id, items=GROCERY_ITEM, counted=False)

    delta = await domovoy_service.on_receipt(conn, user.id, trigger)

    assert delta.mood == "bored"


async def test_mood_window_excludes_a_receipt_older_than_seven_days(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    just_outside = NOW - timedelta(days=MOOD_SLEEPY_INACTIVITY_DAYS) - timedelta(seconds=1)
    await make_receipt(conn, user.id, items=GROCERY_ITEM, purchased_at=just_outside)
    trigger = await make_receipt(conn, user.id, items=GROCERY_ITEM, counted=False)

    delta = await domovoy_service.on_receipt(conn, user.id, trigger)

    assert delta.mood == "sleepy"


async def test_get_state_creates_row_once_and_is_idempotent(conn: AsyncConnection) -> None:
    user = await make_user(conn)

    first = await domovoy_service.get_state(conn, user.id)
    second = await domovoy_service.get_state(conn, user.id)

    assert first == second
    assert first.xp == 0
    assert first.mood == "bored"

    count_cursor = await conn.execute(
        "SELECT count(*) FROM domovoy_states WHERE user_id = %s", (user.id,)
    )
    row = await count_cursor.fetchone()
    assert row is not None
    assert row[0] == 1
