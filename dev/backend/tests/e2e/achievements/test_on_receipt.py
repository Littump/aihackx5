from collections.abc import Callable
from datetime import datetime
from decimal import Decimal

from psycopg import AsyncConnection

from app.features.achievements import database as achievements_db
from app.features.achievements import service as achievements_service
from app.features.challenges.models import ChallengeProgressDelta
from app.features.domovoy import database as domovoy_db
from app.game_rules import ACHIEVEMENT_STREAK_WEEKS, XP_ACHIEVEMENT
from tests.e2e.achievements.data import NOW, SAVER_ITEM, not_counted_receipt, receipt_detail
from tests.factories import (
    make_domovoy_state,
    make_receipt,
    make_referral,
    make_store,
    make_user,
)


def _completed_challenge_delta() -> ChallengeProgressDelta:
    return ChallengeProgressDelta(
        challenge_id=1,
        progress_before=Decimal("1"),
        progress_after=Decimal("2"),
        target=Decimal("2"),
        completed=True,
        reward_points=0,
        reward_xp=0,
    )


async def _achievement_count(conn: AsyncConnection, *, user_id: int, code: str) -> int:
    cursor = await conn.execute(
        "SELECT count(*) FROM achievements WHERE user_id = %s AND code = %s", (user_id, code)
    )
    row = await cursor.fetchone()
    assert row is not None
    return int(row[0])


async def test_first_receipt_unlocks_on_first_counted_receipt(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    row = await make_receipt(conn, user.id, purchased_at=NOW)

    unlocked = await achievements_service.on_receipt(
        conn,
        user.id,
        receipt=receipt_detail(row, counted=True),
        challenge_deltas=[],
        referral_status=None,
    )

    assert unlocked == ["first_receipt"]
    assert await _achievement_count(conn, user_id=user.id, code="first_receipt") == 1
    state = await domovoy_db.get_domovoy_state(conn, user_id=user.id)
    assert state is not None
    assert state.xp == XP_ACHIEVEMENT


async def test_first_challenge_unlocks_when_a_challenge_completes(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)

    unlocked = await achievements_service.on_receipt(
        conn,
        user.id,
        receipt=not_counted_receipt(),
        challenge_deltas=[_completed_challenge_delta()],
        referral_status=None,
    )

    assert unlocked == ["first_challenge"]


async def test_streak_4_unlocks_at_the_threshold(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    await make_domovoy_state(conn, user.id, streak_weeks=ACHIEVEMENT_STREAK_WEEKS)

    unlocked = await achievements_service.on_receipt(
        conn,
        user.id,
        receipt=not_counted_receipt(),
        challenge_deltas=[],
        referral_status=None,
    )

    assert unlocked == ["streak_4"]


async def test_saver_1000_unlocks_when_month_savings_reach_threshold(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    await make_receipt(conn, user.id, purchased_at=NOW, items=SAVER_ITEM)

    unlocked = await achievements_service.on_receipt(
        conn,
        user.id,
        receipt=not_counted_receipt(),
        challenge_deltas=[],
        referral_status=None,
    )

    assert unlocked == ["saver_1000"]


async def test_explorer_unlocks_with_receipts_in_both_chains(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    pyaterochka = await make_store(conn, chain="pyaterochka")
    perekrestok = await make_store(conn, chain="perekrestok")
    await make_receipt(conn, user.id, store_id=pyaterochka.id, purchased_at=NOW)
    await make_receipt(conn, user.id, store_id=perekrestok.id, purchased_at=NOW)

    unlocked = await achievements_service.on_receipt(
        conn,
        user.id,
        receipt=not_counted_receipt(),
        challenge_deltas=[],
        referral_status=None,
    )

    assert unlocked == ["explorer"]


async def test_neighbour_unlocks_for_the_referrer_but_is_not_in_the_events_unlocked_list(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn)
    referee = await make_user(conn)
    await make_referral(conn, referrer.id, referee.id, status="rewarded")

    unlocked = await achievements_service.on_receipt(
        conn,
        referee.id,
        receipt=not_counted_receipt(),
        challenge_deltas=[],
        referral_status="rewarded",
    )

    # neighbour достаётся рефереру, а не пользователю этого события
    assert unlocked == []
    assert await _achievement_count(conn, user_id=referrer.id, code="neighbour") == 1
    assert await _achievement_count(conn, user_id=referee.id, code="neighbour") == 0


async def test_repeated_trigger_does_not_duplicate_the_same_achievement(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    row = await make_receipt(conn, user.id, purchased_at=NOW)
    detail = receipt_detail(row, counted=True)

    first = await achievements_service.on_receipt(
        conn,
        user.id,
        receipt=detail,
        challenge_deltas=[],
        referral_status=None,
    )
    second = await achievements_service.on_receipt(
        conn,
        user.id,
        receipt=detail,
        challenge_deltas=[],
        referral_status=None,
    )

    assert first == ["first_receipt"]
    assert second == []
    assert await _achievement_count(conn, user_id=user.id, code="first_receipt") == 1
    rows = await achievements_db.list_achievements_for_user(conn, user_id=user.id)
    assert len(rows) == 1
