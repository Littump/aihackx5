from collections.abc import Callable
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from psycopg import AsyncConnection

from app.core.clock import week_end, week_start
from app.features.challenges import database as challenges_db
from app.features.challenges import service as challenges_service
from app.features.domovoy import database as domovoy_db
from app.features.receipts import database as receipts_db
from app.features.receipts.models import ReceiptRow, ReceiptWithItems
from tests.e2e.challenges.data import DAIRY_ITEM, MULTI_CATEGORY_NO_DAIRY_ITEMS, NOW
from tests.factories import make_challenge, make_receipt, make_user


async def _with_items(conn: AsyncConnection, receipt: ReceiptRow) -> ReceiptWithItems:
    items = await receipts_db.list_receipt_items_for_receipts(conn, receipt_ids=[receipt.id])
    return ReceiptWithItems(
        id=receipt.id,
        store_id=receipt.store_id,
        purchased_at=receipt.purchased_at,
        regular_total=receipt.regular_total,
        paid_total=receipt.paid_total,
        points_earned=receipt.points_earned,
        points_spent=receipt.points_spent,
        items=items,
    )


OUT_OF_PERIOD_CASES = ["before_period_start", "at_period_end"]


@pytest.mark.parametrize("case", OUT_OF_PERIOD_CASES)
async def test_receipt_outside_the_challenge_period_does_not_move_progress(
    case: str, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    period_start, period_end = week_start(), week_end()
    challenge = await make_challenge(
        conn,
        user.id,
        type="frequency",
        target=Decimal("3"),
        progress=Decimal("0"),
        period_start=period_start,
        period_end=period_end,
    )
    purchased_at = (
        period_start - timedelta(microseconds=1) if case == "before_period_start" else period_end
    )
    receipt = await make_receipt(conn, user.id, items=DAIRY_ITEM, purchased_at=purchased_at)

    deltas = await challenges_service.on_receipt(
        conn, user.id, await _with_items(conn, receipt), counted=True
    )

    assert deltas == []
    unchanged = await challenges_db.get_challenge_by_id(conn, challenge_id=challenge.id)
    assert unchanged is not None
    assert unchanged.progress == Decimal("0")


async def test_category_challenge_ignores_multi_category_receipt_without_dairy(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    challenge = await make_challenge(
        conn,
        user.id,
        type="category",
        category="dairy",
        target=Decimal("2"),
        progress=Decimal("0"),
        period_start=week_start(),
        period_end=week_end(),
    )
    receipt = await make_receipt(
        conn, user.id, items=MULTI_CATEGORY_NO_DAIRY_ITEMS, purchased_at=NOW
    )

    deltas = await challenges_service.on_receipt(
        conn, user.id, await _with_items(conn, receipt), counted=True
    )

    assert deltas == []
    unchanged = await challenges_db.get_challenge_by_id(conn, challenge_id=challenge.id)
    assert unchanged is not None
    assert unchanged.progress == Decimal("0")


async def test_completion_with_zero_reward_points_still_grants_xp(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    await make_challenge(
        conn,
        user.id,
        type="frequency",
        target=Decimal("1"),
        progress=Decimal("0"),
        is_hero=True,
        reward_xp=50,
        reward_points=0,
        period_start=week_start(),
        period_end=week_end(),
    )
    receipt = await make_receipt(conn, user.id, items=DAIRY_ITEM, purchased_at=NOW)

    deltas = await challenges_service.on_receipt(
        conn, user.id, await _with_items(conn, receipt), counted=True
    )

    assert deltas[0].completed is True
    assert deltas[0].reward_xp == 50
    assert deltas[0].reward_points == 0

    ledger_cursor = await conn.execute(
        "SELECT kind, xp_delta, points_delta FROM reward_ledger WHERE user_id = %s",
        (user.id,),
    )
    ledger_row = await ledger_cursor.fetchone()
    assert ledger_row == ("challenge", 50, 0)

    state = await domovoy_db.get_domovoy_state(conn, user_id=user.id)
    assert state is not None
    assert state.xp == 50


async def test_side_challenge_completion_does_not_advance_streak(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    await make_challenge(
        conn,
        user.id,
        type="frequency",
        target=Decimal("1"),
        progress=Decimal("0"),
        is_hero=False,
        reward_xp=50,
        reward_points=30,
        period_start=week_start(),
        period_end=week_end(),
    )
    receipt = await make_receipt(conn, user.id, items=DAIRY_ITEM, purchased_at=NOW)

    deltas = await challenges_service.on_receipt(
        conn, user.id, await _with_items(conn, receipt), counted=True
    )

    assert deltas[0].completed is True
    state = await domovoy_db.get_domovoy_state(conn, user_id=user.id)
    assert state is not None
    assert state.xp == 50
    assert state.streak_weeks == 0
