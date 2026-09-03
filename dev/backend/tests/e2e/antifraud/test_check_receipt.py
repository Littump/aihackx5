from collections.abc import Callable
from datetime import datetime, timedelta

from psycopg import AsyncConnection

from app.features.antifraud import service as antifraud_service
from tests.e2e.antifraud.data import NOW
from tests.factories import make_receipt, make_store, make_user


async def _fraud_check_count(conn: AsyncConnection, *, receipt_id: int) -> int:
    cursor = await conn.execute(
        "SELECT count(*) FROM fraud_checks WHERE subject_type = 'receipt' AND subject_id = %s",
        (receipt_id,),
    )
    row = await cursor.fetchone()
    assert row is not None
    return int(row[0])


async def test_check_receipt_happy_path_approves_and_writes_one_row(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    receipt = await make_receipt(conn, user.id, purchased_at=NOW)

    decision = await antifraud_service.check_receipt(conn, user.id, receipt)

    assert decision.decision == "approve"
    assert decision.signals == []
    assert await _fraud_check_count(conn, receipt_id=receipt.id) == 1


async def test_check_receipt_second_call_inserts_a_second_row(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    receipt = await make_receipt(conn, user.id, purchased_at=NOW)

    await antifraud_service.check_receipt(conn, user.id, receipt)
    await antifraud_service.check_receipt(conn, user.id, receipt)

    assert await _fraud_check_count(conn, receipt_id=receipt.id) == 2


async def test_check_receipt_combines_burst_and_daily_volume_into_hold(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    store = await make_store(conn)
    offsets = (50, 40, 30, 20, 10, 0)
    receipt = None
    for minutes in offsets:
        receipt = await make_receipt(
            conn, user.id, store_id=store.id, purchased_at=NOW - timedelta(minutes=minutes)
        )
    assert receipt is not None

    decision = await antifraud_service.check_receipt(conn, user.id, receipt)

    codes = {signal.code for signal in decision.signals}
    assert {"burst_same_store", "daily_volume"} <= codes
    assert decision.decision == "hold"

    cursor = await conn.execute(
        "SELECT user_id, decision FROM fraud_checks WHERE subject_type = 'receipt' "
        "AND subject_id = %s",
        (receipt.id,),
    )
    row = await cursor.fetchone()
    assert row == (user.id, "hold")
