from collections.abc import Callable
from datetime import datetime
from decimal import Decimal

from psycopg import AsyncConnection

from app.core.clock import week_end, week_start
from app.features.challenges import database as challenges_db
from app.features.challenges import service as challenges_service
from app.features.domovoy import database as domovoy_db
from app.features.receipts import database as receipts_db
from app.features.receipts.models import ReceiptDetail, ReceiptRow
from tests.e2e.challenges.data import DAIRY_ITEM, NOW
from tests.factories import make_challenge, make_receipt, make_user


async def _receipt_detail(conn: AsyncConnection, receipt: ReceiptRow) -> ReceiptDetail:
    items = await receipts_db.list_receipt_items_for_receipts(conn, receipt_ids=[receipt.id])
    return ReceiptDetail(
        id=receipt.id,
        store_id=receipt.store_id,
        store_name="Тестовый магазин",
        purchased_at=receipt.purchased_at,
        regular_total=receipt.regular_total,
        paid_total=receipt.paid_total,
        discount_total=receipt.discount_total,
        points_earned=receipt.points_earned,
        points_spent=receipt.points_spent,
        counted=receipt.counted,
        is_returned=receipt.is_returned,
        items=items,
    )


async def test_returning_the_closing_receipt_reopens_the_challenge(
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
        await challenges_service.on_receipt(conn, user.id, await _receipt_detail(conn, receipt))
    closing_receipt = await make_receipt(conn, user.id, items=DAIRY_ITEM, purchased_at=NOW)
    closing_detail = await _receipt_detail(conn, closing_receipt)
    completion = await challenges_service.on_receipt(conn, user.id, closing_detail)
    assert completion[0].completed is True

    deltas = await challenges_service.on_receipt_returned(conn, user.id, closing_detail)

    assert deltas[0].progress_after == Decimal("2")
    assert deltas[0].completed is False
    assert deltas[0].reward_points == -30

    reopened = await challenges_db.get_challenge_by_id(conn, challenge_id=challenge.id)
    assert reopened is not None
    assert reopened.status == "active"
    assert reopened.progress == Decimal("2")
    assert reopened.completed_at is None

    ledger_cursor = await conn.execute(
        "SELECT xp_delta, points_delta FROM reward_ledger "
        "WHERE user_id = %s ORDER BY created_at ASC",
        (user.id,),
    )
    ledger_rows = await ledger_cursor.fetchall()
    assert ledger_rows == [(50, 30), (0, -30)]

    state = await domovoy_db.get_domovoy_state(conn, user_id=user.id)
    assert state is not None
    assert state.xp == 50
    assert state.streak_weeks == 1


async def test_returning_a_not_counted_receipt_is_a_noop(
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
        progress=Decimal("1"),
        is_hero=True,
        period_start=week_start(),
        period_end=week_end(),
    )
    receipt = await make_receipt(conn, user.id, items=DAIRY_ITEM, purchased_at=NOW, counted=False)
    receipt_detail = await _receipt_detail(conn, receipt)

    deltas = await challenges_service.on_receipt_returned(conn, user.id, receipt_detail)

    assert deltas == []
    unchanged = await challenges_db.get_challenge_by_id(conn, challenge_id=challenge.id)
    assert unchanged is not None
    assert unchanged.progress == Decimal("1")

    ledger_cursor = await conn.execute(
        "SELECT count(*) FROM reward_ledger WHERE user_id = %s", (user.id,)
    )
    ledger_row = await ledger_cursor.fetchone()
    assert ledger_row is not None
    assert ledger_row[0] == 0
