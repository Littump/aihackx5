from collections.abc import Callable
from datetime import datetime
from decimal import Decimal

from psycopg import AsyncConnection

from app.core.clock import week_end, week_start
from app.features.challenges import database as challenges_db
from app.features.challenges import service as challenges_service
from app.features.domovoy import database as domovoy_db
from app.features.receipts import database as receipts_db
from app.features.receipts.models import ReceiptRow, ReceiptWithItems
from tests.e2e.challenges.data import BAKERY_ITEM, DAIRY_ITEM, NOW
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


async def test_two_receipts_leave_frequency_challenge_active_third_completes(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    challenge = await make_challenge(
        conn,
        user.id,
        type="frequency",
        baseline=Decimal("2"),
        target=Decimal("3"),
        progress=Decimal("0"),
        is_hero=True,
        reward_xp=50,
        reward_points=30,
        period_start=week_start(),
        period_end=week_end(),
    )

    for _ in range(2):
        receipt = await make_receipt(conn, user.id, items=DAIRY_ITEM, purchased_at=NOW)
        deltas = await challenges_service.on_receipt(
            conn, user.id, await _with_items(conn, receipt), counted=True
        )
        assert deltas[0].completed is False

    after_two = await challenges_db.get_challenge_by_id(conn, challenge_id=challenge.id)
    assert after_two is not None
    assert after_two.progress == Decimal("2")
    assert after_two.status == "active"

    closing_receipt = await make_receipt(conn, user.id, items=DAIRY_ITEM, purchased_at=NOW)
    deltas = await challenges_service.on_receipt(
        conn, user.id, await _with_items(conn, closing_receipt), counted=True
    )
    assert deltas[0].completed is True
    assert deltas[0].reward_xp == 50
    assert deltas[0].reward_points == 30

    completed = await challenges_db.get_challenge_by_id(conn, challenge_id=challenge.id)
    assert completed is not None
    assert completed.status == "completed"
    assert completed.progress == Decimal("3")
    assert completed.completed_at is not None

    ledger_cursor = await conn.execute(
        "SELECT kind, xp_delta, points_delta, ref_type, ref_id "
        "FROM reward_ledger WHERE user_id = %s",
        (user.id,),
    )
    ledger_row = await ledger_cursor.fetchone()
    assert ledger_row == ("challenge", 50, 30, "challenge", challenge.id)

    state = await domovoy_db.get_domovoy_state(conn, user_id=user.id)
    assert state is not None
    assert state.xp == 50
    assert state.streak_weeks == 1


async def test_not_counted_receipt_does_not_move_progress(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    challenge = await make_challenge(
        conn,
        user.id,
        type="frequency",
        target=Decimal("3"),
        progress=Decimal("0"),
        period_start=week_start(),
        period_end=week_end(),
    )
    receipt = await make_receipt(conn, user.id, items=DAIRY_ITEM, purchased_at=NOW, counted=False)

    deltas = await challenges_service.on_receipt(
        conn, user.id, await _with_items(conn, receipt), counted=False
    )

    assert deltas == []
    unchanged = await challenges_db.get_challenge_by_id(conn, challenge_id=challenge.id)
    assert unchanged is not None
    assert unchanged.progress == Decimal("0")


async def test_category_challenge_moves_only_with_the_matching_category(
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

    bakery_receipt = await make_receipt(conn, user.id, items=BAKERY_ITEM, purchased_at=NOW)
    deltas = await challenges_service.on_receipt(
        conn, user.id, await _with_items(conn, bakery_receipt), counted=True
    )
    assert deltas == []
    still_zero = await challenges_db.get_challenge_by_id(conn, challenge_id=challenge.id)
    assert still_zero is not None
    assert still_zero.progress == Decimal("0")

    dairy_receipt = await make_receipt(conn, user.id, items=DAIRY_ITEM, purchased_at=NOW)
    deltas = await challenges_service.on_receipt(
        conn, user.id, await _with_items(conn, dairy_receipt), counted=True
    )
    assert len(deltas) == 1
    moved = await challenges_db.get_challenge_by_id(conn, challenge_id=challenge.id)
    assert moved is not None
    assert moved.progress == Decimal("1")
