from collections.abc import Callable
from datetime import datetime, timedelta

import pytest
from psycopg import AsyncConnection

from app.core.errors import AppError
from app.features.antifraud import service as antifraud_service
from tests.e2e.antifraud.data import NOW, REFERRER_CREATED_AT
from tests.factories import make_referral, make_user


async def _fraud_check_row(conn: AsyncConnection, *, referral_id: int) -> tuple[int, str] | None:
    cursor = await conn.execute(
        "SELECT user_id, decision FROM fraud_checks WHERE subject_type = 'referral' "
        "AND subject_id = %s",
        (referral_id,),
    )
    row = await cursor.fetchone()
    return (row[0], row[1]) if row is not None else None


async def test_check_referral_happy_path_approves_and_writes_one_row(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn, created_at=REFERRER_CREATED_AT)
    referee = await make_user(conn, created_at=NOW)
    referral = await make_referral(conn, referrer.id, referee.id, created_at=NOW)

    decision = await antifraud_service.check_referral(conn, referral.id)

    assert decision.decision == "approve"
    assert decision.signals == []
    assert await _fraud_check_row(conn, referral_id=referral.id) == (referrer.id, "approve")


async def test_check_referral_unknown_id_raises_not_found(conn: AsyncConnection) -> None:
    with pytest.raises(AppError) as exc_info:
        await antifraud_service.check_referral(conn, 999999)

    assert exc_info.value.code == "referral_not_found"
    assert exc_info.value.status == 404


async def test_check_referral_combines_shared_device_and_invite_burst_into_hold(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(
        conn, device_fingerprint="device-shared", created_at=REFERRER_CREATED_AT
    )
    burst_at = REFERRER_CREATED_AT + timedelta(hours=2)
    # 5 приглашений ДО anchor (lookback-only окно), проверяемое — последним, шестым
    for i in range(5):
        invitee = await make_user(conn, device_fingerprint=f"device-{i}", created_at=burst_at)
        await make_referral(
            conn, referrer.id, invitee.id, created_at=burst_at - timedelta(minutes=5 - i)
        )
    checked_invitee = await make_user(conn, device_fingerprint="device-shared", created_at=burst_at)
    checked_referral = await make_referral(
        conn, referrer.id, checked_invitee.id, created_at=burst_at
    )

    decision = await antifraud_service.check_referral(conn, checked_referral.id)

    codes = {signal.code for signal in decision.signals}
    assert codes == {"shared_device", "invite_burst"}
    assert decision.decision == "hold"
    assert await _fraud_check_row(conn, referral_id=checked_referral.id) == (referrer.id, "hold")
