from datetime import date

import pytest
from psycopg import AsyncConnection
from psycopg.errors import CheckViolation, UniqueViolation

WEEK_START = date(2026, 8, 31)


async def _make_store(conn: AsyncConnection) -> int:
    cur = await conn.execute(
        "INSERT INTO stores (name, chain, district, city) "
        "VALUES ('Пятёрочка, Ленина 12', 'pyaterochka', 'Центр', 'Москва') RETURNING id"
    )
    row = await cur.fetchone()
    assert row is not None
    return int(row[0])


async def _make_league(conn: AsyncConnection, store_id: int, **overrides: object) -> int:
    params: dict[str, object] = {
        "store_id": store_id,
        "division": 1,
        "week_start": WEEK_START,
        "status": "open",
    }
    params.update(overrides)
    cur = await conn.execute(
        "INSERT INTO leagues (store_id, division, week_start, status) "
        "VALUES (%(store_id)s, %(division)s, %(week_start)s, %(status)s) RETURNING id",
        params,
    )
    row = await cur.fetchone()
    assert row is not None
    return int(row[0])


@pytest.mark.parametrize("division", [1, 5])
async def test_leagues_division_check_accepts_boundaries(
    conn: AsyncConnection, division: int
) -> None:
    store_id = await _make_store(conn)
    assert await _make_league(conn, store_id, division=division) > 0


@pytest.mark.parametrize("division", [0, 6])
async def test_leagues_division_check_rejects_out_of_range(
    conn: AsyncConnection, division: int
) -> None:
    store_id = await _make_store(conn)
    with pytest.raises(CheckViolation):
        await _make_league(conn, store_id, division=division)


async def test_leagues_unique_blocks_two_simultaneously_open_leagues(
    conn: AsyncConnection,
) -> None:
    store_id = await _make_store(conn)
    await _make_league(conn, store_id, status="open")
    with pytest.raises(UniqueViolation):
        await _make_league(conn, store_id, status="open")


async def test_leagues_shard_after_closing_full_league(conn: AsyncConnection) -> None:
    store_id = await _make_store(conn)
    await _make_league(conn, store_id, status="closed")
    await _make_league(conn, store_id, status="open")
