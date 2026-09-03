from collections.abc import Callable
from datetime import datetime, timedelta

import pytest
from psycopg import AsyncConnection

from app.features.achievements import database as achievements_db
from app.features.achievements import service as achievements_service
from app.game_rules import ACHIEVEMENT_EXPLORER_WINDOW_DAYS
from tests.e2e.achievements.data import (
    AT_SAVER_THRESHOLD_ITEM,
    BELOW_SAVER_THRESHOLD_ITEM,
    NOW,
    SAVER_ITEM,
    not_counted_receipt,
)
from tests.factories import make_receipt, make_store, make_user


async def _achievement_count(conn: AsyncConnection, *, user_id: int, code: str) -> int:
    cursor = await conn.execute(
        "SELECT count(*) FROM achievements WHERE user_id = %s AND code = %s", (user_id, code)
    )
    row = await cursor.fetchone()
    assert row is not None
    return int(row[0])


async def test_saver_1000_does_not_unlock_when_qualifying_receipt_is_returned(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    await make_receipt(conn, user.id, purchased_at=NOW, items=SAVER_ITEM, is_returned=True)

    unlocked = await achievements_service.on_receipt(
        conn,
        user.id,
        receipt=not_counted_receipt(),
        challenge_deltas=[],
        referral_status=None,
    )

    assert unlocked == []


@pytest.mark.parametrize(
    ("case_id", "items", "expected"),
    [
        ("below_threshold", BELOW_SAVER_THRESHOLD_ITEM, []),
        ("at_threshold", AT_SAVER_THRESHOLD_ITEM, ["saver_1000"]),
    ],
    ids=["below_threshold", "at_threshold"],
)
async def test_saver_1000_boundary_via_real_savings_calculation(
    conn: AsyncConnection,
    freeze_time: Callable[[datetime], None],
    case_id: str,
    items: list[dict[str, object]],
    expected: list[str],
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    await make_receipt(conn, user.id, purchased_at=NOW, items=items)

    unlocked = await achievements_service.on_receipt(
        conn,
        user.id,
        receipt=not_counted_receipt(),
        challenge_deltas=[],
        referral_status=None,
    )

    assert unlocked == expected


async def test_explorer_does_not_unlock_when_second_chain_receipt_is_outside_window(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    pyaterochka = await make_store(conn, chain="pyaterochka")
    perekrestok = await make_store(conn, chain="perekrestok")
    outside_window = NOW - timedelta(days=ACHIEVEMENT_EXPLORER_WINDOW_DAYS + 1)
    await make_receipt(conn, user.id, store_id=pyaterochka.id, purchased_at=outside_window)
    await make_receipt(conn, user.id, store_id=perekrestok.id, purchased_at=NOW)

    unlocked = await achievements_service.on_receipt(
        conn,
        user.id,
        receipt=not_counted_receipt(),
        challenge_deltas=[],
        referral_status=None,
    )

    assert "explorer" not in unlocked


async def test_insert_achievement_is_idempotent_under_conflicting_inserts(
    conn: AsyncConnection,
) -> None:
    user = await make_user(conn)

    first = await achievements_db.insert_achievement(conn, user_id=user.id, code="explorer")
    second = await achievements_db.insert_achievement(conn, user_id=user.id, code="explorer")

    assert first is not None
    assert second is None
    assert await _achievement_count(conn, user_id=user.id, code="explorer") == 1
