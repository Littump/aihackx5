from collections.abc import Callable
from datetime import datetime, timedelta

import pytest
from psycopg import AsyncConnection

from app.core.clock import week_start
from app.core.errors import AppError
from app.features.league import database as league_db
from app.features.league import service as league_service
from app.game_rules import LEAGUE_SIZE
from tests.e2e.league.data import NOW
from tests.factories import make_league, make_store, make_user, make_user_features

PREVIOUS_WEEK = week_start(NOW - timedelta(weeks=1)).date()


async def test_ensure_member_defaults_newcomer_to_division_1(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    await make_store(conn)
    user = await make_user(conn)

    membership = await league_service.ensure_member(conn, user.id)

    assert membership.division == 1
    league = await league_db.get_league_by_id(conn, league_id=membership.league_id)
    assert league is not None
    assert league.week_start == week_start(NOW).date()


async def test_ensure_member_is_idempotent_within_same_week(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    await make_store(conn)
    user = await make_user(conn)

    first = await league_service.ensure_member(conn, user.id)
    second = await league_service.ensure_member(conn, user.id)

    assert first == second
    count = await league_db.count_members(conn, league_id=first.league_id)
    assert count == 1


async def test_ensure_member_inherits_division_from_previous_week(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    store = await make_store(conn)
    old_league = await make_league(conn, store_id=store.id, division=3, week_start=PREVIOUS_WEEK)
    user = await make_user(conn)
    await league_db.insert_member(conn, league_id=old_league.id, user_id=user.id)

    freeze_time(NOW)
    membership = await league_service.ensure_member(conn, user.id)

    assert membership.division == 3


async def test_31st_member_creates_new_league_for_same_store(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    store = await make_store(conn)
    league = await make_league(conn, store_id=store.id, division=1)
    for _ in range(LEAGUE_SIZE):
        member = await make_user(conn)
        await league_db.insert_member(conn, league_id=league.id, user_id=member.id)

    newcomer = await make_user(conn)
    membership = await league_service.ensure_member(conn, newcomer.id)

    assert membership.store_id == store.id
    assert membership.league_id != league.id
    old_league = await league_db.get_league_by_id(conn, league_id=league.id)
    assert old_league is not None
    assert old_league.status == "closed"
    new_league = await league_db.get_league_by_id(conn, league_id=membership.league_id)
    assert new_league is not None
    assert new_league.status == "open"


async def test_ensure_member_unknown_user_raises_not_found(conn: AsyncConnection) -> None:
    with pytest.raises(AppError) as excinfo:
        await league_service.ensure_member(conn, 999999)
    assert excinfo.value.code == "user_not_found"


async def test_ensure_member_falls_back_to_default_store_without_purchase_history(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    default_store = await make_store(conn)
    await make_store(conn)
    user = await make_user(conn)

    membership = await league_service.ensure_member(conn, user.id)

    assert membership.store_id == default_store.id


async def test_ensure_member_uses_live_user_features_store_over_stale_users_column(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    stale_store = await make_store(conn)
    live_store = await make_store(conn)
    user = await make_user(conn, favourite_store_id=stale_store.id)
    await make_user_features(conn, user.id, favourite_store_id=live_store.id)

    membership = await league_service.ensure_member(conn, user.id)

    assert membership.store_id == live_store.id
