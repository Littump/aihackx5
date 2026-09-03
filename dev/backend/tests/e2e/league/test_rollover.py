from collections.abc import Callable
from datetime import date, datetime, timedelta

from psycopg import AsyncConnection

from app.core.clock import week_start
from app.features.league import database as league_db
from app.features.league import service as league_service
from app.features.league.models import RolloverSummary
from app.game_rules import XP_ACHIEVEMENT, XP_LEAGUE_PROMOTION, XP_LEAGUE_TOP3, level_for_xp
from tests.e2e.league.data import NOW
from tests.factories import make_league, make_league_member, make_store, make_user

PREVIOUS_WEEK = week_start(NOW - timedelta(weeks=1)).date()
CURRENT_WEEK = week_start(NOW).date()
DIVISION_MIDDLE = 3


async def _seed_scored_league(
    conn: AsyncConnection, *, store_id: int, division: int, count: int, week: date
) -> tuple[int, list[int]]:
    league = await make_league(conn, store_id=store_id, division=division, week_start=week)
    user_ids: list[int] = []
    for index in range(count):
        member = await make_user(conn)
        await make_league_member(conn, league.id, member.id, score=count - index)
        user_ids.append(member.id)
    return league.id, user_ids


async def _ledger_xp_deltas(conn: AsyncConnection, user_id: int) -> list[int]:
    cursor = await conn.execute(
        "SELECT xp_delta FROM reward_ledger WHERE user_id = %s ORDER BY id", (user_id,)
    )
    return [row[0] for row in await cursor.fetchall()]


async def _division_for_current_week(conn: AsyncConnection, user_id: int) -> int | None:
    membership = await league_db.get_membership_for_week(
        conn, user_id=user_id, week_start=CURRENT_WEEK
    )
    return membership.division if membership is not None else None


async def _achievement_count(conn: AsyncConnection, user_id: int, code: str) -> int:
    cursor = await conn.execute(
        "SELECT count(*) FROM achievements WHERE user_id = %s AND code = %s", (user_id, code)
    )
    row = await cursor.fetchone()
    assert row is not None
    return int(row[0])


async def test_rollover_promotes_top7_demotes_bottom5_and_grants_top3_xp(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    store = await make_store(conn)
    league_id, user_ids = await _seed_scored_league(
        conn, store_id=store.id, division=DIVISION_MIDDLE, count=30, week=PREVIOUS_WEEK
    )

    summary = await league_service.rollover_week(conn)

    assert summary == RolloverSummary(
        leagues_closed=1, users_promoted=7, users_demoted=5, week_start=CURRENT_WEEK
    )
    old_league = await league_db.get_league_by_id(conn, league_id=league_id)
    assert old_league is not None
    assert old_league.status == "closed"

    for user_id in user_ids[:3]:
        assert sorted(await _ledger_xp_deltas(conn, user_id)) == sorted(
            [XP_LEAGUE_PROMOTION, XP_LEAGUE_TOP3, XP_ACHIEVEMENT]
        )
        assert await _division_for_current_week(conn, user_id) == DIVISION_MIDDLE + 1
    for user_id in user_ids[3:7]:
        assert await _ledger_xp_deltas(conn, user_id) == [XP_LEAGUE_PROMOTION]
        assert await _division_for_current_week(conn, user_id) == DIVISION_MIDDLE + 1
    for user_id in user_ids[7:25]:
        assert await _ledger_xp_deltas(conn, user_id) == []
        assert await _division_for_current_week(conn, user_id) == DIVISION_MIDDLE
    for user_id in user_ids[25:]:
        assert await _ledger_xp_deltas(conn, user_id) == []
        assert await _division_for_current_week(conn, user_id) == DIVISION_MIDDLE - 1


async def test_rollover_division_1_never_demotes(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    store = await make_store(conn)
    _, user_ids = await _seed_scored_league(
        conn, store_id=store.id, division=1, count=30, week=PREVIOUS_WEEK
    )

    summary = await league_service.rollover_week(conn)

    assert summary.users_demoted == 0
    for user_id in user_ids[:3]:
        assert sorted(await _ledger_xp_deltas(conn, user_id)) == sorted(
            [XP_LEAGUE_PROMOTION, XP_LEAGUE_TOP3, XP_ACHIEVEMENT]
        )
        assert await _division_for_current_week(conn, user_id) == 2
    for user_id in user_ids[25:]:
        assert await _ledger_xp_deltas(conn, user_id) == []
        assert await _division_for_current_week(conn, user_id) == 1


async def test_rollover_division_5_never_promotes_but_still_grants_top3_xp(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    store = await make_store(conn)
    _, user_ids = await _seed_scored_league(
        conn, store_id=store.id, division=5, count=30, week=PREVIOUS_WEEK
    )

    summary = await league_service.rollover_week(conn)

    assert summary.users_promoted == 0
    for user_id in user_ids[:3]:
        assert await _ledger_xp_deltas(conn, user_id) == [XP_LEAGUE_TOP3, XP_ACHIEVEMENT]
        assert await _division_for_current_week(conn, user_id) == 5
    for user_id in user_ids[3:7]:
        assert await _ledger_xp_deltas(conn, user_id) == []
        assert await _division_for_current_week(conn, user_id) == 5


async def test_rollover_is_idempotent_for_the_same_week(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    store = await make_store(conn)
    _, user_ids = await _seed_scored_league(
        conn, store_id=store.id, division=DIVISION_MIDDLE, count=30, week=PREVIOUS_WEEK
    )

    first = await league_service.rollover_week(conn)
    second = await league_service.rollover_week(conn)
    third = await league_service.rollover_week(conn)

    empty = RolloverSummary(
        leagues_closed=0, users_promoted=0, users_demoted=0, week_start=CURRENT_WEEK
    )
    assert first.leagues_closed == 1
    assert second == empty
    assert third == empty
    for user_id in user_ids[:3]:
        assert sorted(await _ledger_xp_deltas(conn, user_id)) == sorted(
            [XP_LEAGUE_PROMOTION, XP_LEAGUE_TOP3, XP_ACHIEVEMENT]
        )
    for user_id in user_ids[3:7]:
        assert await _ledger_xp_deltas(conn, user_id) == [XP_LEAGUE_PROMOTION]
    for user_id in user_ids[25:]:
        assert await _ledger_xp_deltas(conn, user_id) == []


async def test_rollover_ignores_open_league_of_current_week(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    store = await make_store(conn)
    league_id, user_ids = await _seed_scored_league(
        conn, store_id=store.id, division=DIVISION_MIDDLE, count=5, week=CURRENT_WEEK
    )

    summary = await league_service.rollover_week(conn)

    assert summary == RolloverSummary(
        leagues_closed=0, users_promoted=0, users_demoted=0, week_start=CURRENT_WEEK
    )
    current_league = await league_db.get_league_by_id(conn, league_id=league_id)
    assert current_league is not None
    assert current_league.status == "open"
    for user_id in user_ids:
        assert await _ledger_xp_deltas(conn, user_id) == []


async def test_rollover_accumulates_top3_and_promotion_xp_on_domovoy_state(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    store = await make_store(conn)
    _, user_ids = await _seed_scored_league(
        conn, store_id=store.id, division=DIVISION_MIDDLE, count=30, week=PREVIOUS_WEEK
    )
    top_user_id = user_ids[0]

    await league_service.rollover_week(conn)

    cursor = await conn.execute(
        "SELECT xp, level FROM domovoy_states WHERE user_id = %s", (top_user_id,)
    )
    row = await cursor.fetchone()
    assert row is not None
    expected_xp = XP_LEAGUE_PROMOTION + XP_LEAGUE_TOP3 + XP_ACHIEVEMENT
    assert row[0] == expected_xp
    assert row[1] == level_for_xp(expected_xp)


async def test_rollover_defect_conflicts_when_user_already_member_of_target_league(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW - timedelta(weeks=1))
    store = await make_store(conn)
    _, user_ids = await _seed_scored_league(
        conn, store_id=store.id, division=DIVISION_MIDDLE, count=30, week=PREVIOUS_WEEK
    )
    safe_user_id = user_ids[10]

    freeze_time(NOW)
    stale_membership = await league_service.ensure_member(conn, safe_user_id)

    await league_service.rollover_week(conn)

    cursor = await conn.execute(
        "SELECT l.id, l.division FROM league_members lm "
        "JOIN leagues l ON l.id = lm.league_id "
        "WHERE lm.user_id = %s AND l.week_start = %s",
        (safe_user_id, CURRENT_WEEK),
    )
    rows = await cursor.fetchall()
    assert len(rows) == 1
    assert rows[0][0] == stale_membership.league_id
    assert rows[0][1] == DIVISION_MIDDLE


async def test_rollover_preserves_score_when_transferring_pre_rollover_membership(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW - timedelta(weeks=1))
    store = await make_store(conn)
    _, user_ids = await _seed_scored_league(
        conn, store_id=store.id, division=DIVISION_MIDDLE, count=30, week=PREVIOUS_WEEK
    )
    demoted_user_id = user_ids[29]

    freeze_time(NOW)
    stale_membership = await league_service.ensure_member(conn, demoted_user_id)
    await league_db.update_member_score(
        conn, league_id=stale_membership.league_id, user_id=demoted_user_id, score=42
    )

    await league_service.rollover_week(conn)

    membership = await league_db.get_membership_for_week(
        conn, user_id=demoted_user_id, week_start=CURRENT_WEEK
    )
    assert membership is not None
    assert membership.division == DIVISION_MIDDLE - 1
    assert membership.league_id != stale_membership.league_id
    assert membership.score == 42


async def test_rollover_replaces_stale_pre_rollover_membership_with_promoted_division(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW - timedelta(weeks=1))
    store = await make_store(conn)
    _, user_ids = await _seed_scored_league(
        conn, store_id=store.id, division=DIVISION_MIDDLE, count=30, week=PREVIOUS_WEEK
    )
    promoted_user_id = user_ids[0]

    freeze_time(NOW)
    stale_membership = await league_service.ensure_member(conn, promoted_user_id)
    assert stale_membership.division == DIVISION_MIDDLE

    await league_service.rollover_week(conn)

    cursor = await conn.execute(
        "SELECT l.id, l.division FROM league_members lm "
        "JOIN leagues l ON l.id = lm.league_id "
        "WHERE lm.user_id = %s AND l.week_start = %s",
        (promoted_user_id, CURRENT_WEEK),
    )
    rows = await cursor.fetchall()
    assert len(rows) == 1
    assert rows[0][1] == DIVISION_MIDDLE + 1
    assert rows[0][0] != stale_membership.league_id


async def test_rollover_unlocks_league_top3_achievement_for_top3_only(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    store = await make_store(conn)
    _, user_ids = await _seed_scored_league(
        conn, store_id=store.id, division=DIVISION_MIDDLE, count=30, week=PREVIOUS_WEEK
    )

    await league_service.rollover_week(conn)

    for user_id in user_ids[:3]:
        assert await _achievement_count(conn, user_id, "league_top3") == 1
    for user_id in user_ids[3:7]:
        assert await _achievement_count(conn, user_id, "league_top3") == 0
