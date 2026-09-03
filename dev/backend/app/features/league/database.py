from datetime import date

from psycopg import AsyncConnection
from psycopg.rows import class_row

from app.features.league.models import (
    LeagueMemberRow,
    LeagueMembership,
    LeagueMemberUserRow,
    LeagueRankedMemberRow,
    LeagueRow,
    LeagueStoreWeekRow,
)

LEAGUE_COLUMNS = "id, store_id, division, week_start, status"
LEAGUE_INSERT = (
    f"INSERT INTO leagues (store_id, division, week_start, status) "
    "VALUES (%(store_id)s, %(division)s, %(week_start)s, %(status)s) "
    f"RETURNING {LEAGUE_COLUMNS}"
)
LEAGUE_GET_OPEN = (
    f"SELECT {LEAGUE_COLUMNS} FROM leagues WHERE store_id = %(store_id)s "
    "AND division = %(division)s AND week_start = %(week_start)s AND status = 'open'"
)
LEAGUE_GET_BY_ID = f"SELECT {LEAGUE_COLUMNS} FROM leagues WHERE id = %(league_id)s"
LEAGUE_CLOSE = "UPDATE leagues SET status = 'closed' WHERE id = %(league_id)s"
LEAGUE_MEMBER_INSERT = (
    "INSERT INTO league_members (league_id, user_id, score) "
    "VALUES (%(league_id)s, %(user_id)s, 0) "
    "RETURNING league_id, user_id, score, joined_at"
)
LEAGUE_MEMBER_COUNT = "SELECT count(*) FROM league_members WHERE league_id = %(league_id)s"
LEAGUE_MEMBER_UPDATE_SCORE = (
    "UPDATE league_members SET score = %(score)s "
    "WHERE league_id = %(league_id)s AND user_id = %(user_id)s "
    "RETURNING league_id, user_id, score, joined_at"
)
LEAGUE_MEMBERSHIP_FOR_WEEK = (
    "SELECT l.id AS league_id, l.division AS division, l.store_id AS store_id "
    "FROM league_members lm JOIN leagues l ON l.id = lm.league_id "
    "WHERE lm.user_id = %(user_id)s AND l.week_start = %(week_start)s"
)
LATEST_DIVISION = (
    "SELECT l.division FROM league_members lm JOIN leagues l ON l.id = lm.league_id "
    "WHERE lm.user_id = %(user_id)s ORDER BY l.week_start DESC LIMIT 1"
)
MEMBER_RANK = (
    "WITH ranked AS (SELECT user_id, RANK() OVER (ORDER BY score DESC, user_id ASC) AS rnk "
    "FROM league_members WHERE league_id = %(league_id)s) "
    "SELECT rnk FROM ranked WHERE user_id = %(user_id)s"
)
RANKED_MEMBERS = (
    "SELECT user_id, score, RANK() OVER (ORDER BY score DESC, user_id ASC) AS rank "
    "FROM league_members WHERE league_id = %(league_id)s ORDER BY rank ASC, user_id ASC"
)
MEMBER_USER_IDS_FOR_STORE_WEEK = (
    "SELECT DISTINCT lm.user_id AS user_id FROM league_members lm "
    "JOIN leagues l ON l.id = lm.league_id "
    "WHERE l.store_id = %(store_id)s AND l.week_start = %(week_start)s"
)
STORE_IDS_WITH_LEAGUES = (
    "SELECT DISTINCT store_id AS store_id FROM leagues WHERE week_start = %(week_start)s"
)


async def insert_league(
    conn: AsyncConnection, *, store_id: int, division: int, week_start: date, status: str
) -> LeagueRow:
    params: dict[str, object] = {
        "store_id": store_id,
        "division": division,
        "week_start": week_start,
        "status": status,
    }
    return await insert_league_row(conn, params)


async def insert_league_row(conn: AsyncConnection, params: dict[str, object]) -> LeagueRow:
    # raw-параметры нужны только tests/factories.make_league для гибких фикстур
    async with conn.cursor(row_factory=class_row(LeagueRow)) as cur:
        await cur.execute(LEAGUE_INSERT, params)
        row = await cur.fetchone()
        assert row is not None
        return row


async def get_open_league(
    conn: AsyncConnection, *, store_id: int, division: int, week_start: date
) -> LeagueRow | None:
    params = {"store_id": store_id, "division": division, "week_start": week_start}
    async with conn.cursor(row_factory=class_row(LeagueRow)) as cur:
        await cur.execute(LEAGUE_GET_OPEN, params)
        return await cur.fetchone()


async def get_league_by_id(conn: AsyncConnection, *, league_id: int) -> LeagueRow | None:
    async with conn.cursor(row_factory=class_row(LeagueRow)) as cur:
        await cur.execute(LEAGUE_GET_BY_ID, {"league_id": league_id})
        return await cur.fetchone()


async def close_league(conn: AsyncConnection, *, league_id: int) -> None:
    async with conn.cursor() as cur:
        await cur.execute(LEAGUE_CLOSE, {"league_id": league_id})


async def insert_member(conn: AsyncConnection, *, league_id: int, user_id: int) -> LeagueMemberRow:
    params = {"league_id": league_id, "user_id": user_id}
    async with conn.cursor(row_factory=class_row(LeagueMemberRow)) as cur:
        await cur.execute(LEAGUE_MEMBER_INSERT, params)
        row = await cur.fetchone()
        assert row is not None
        return row


async def count_members(conn: AsyncConnection, *, league_id: int) -> int:
    async with conn.cursor() as cur:
        await cur.execute(LEAGUE_MEMBER_COUNT, {"league_id": league_id})
        row = await cur.fetchone()
        assert row is not None
        return int(row[0])


async def update_member_score(
    conn: AsyncConnection, *, league_id: int, user_id: int, score: int
) -> LeagueMemberRow:
    params = {"league_id": league_id, "user_id": user_id, "score": score}
    async with conn.cursor(row_factory=class_row(LeagueMemberRow)) as cur:
        await cur.execute(LEAGUE_MEMBER_UPDATE_SCORE, params)
        row = await cur.fetchone()
        assert row is not None
        return row


async def get_membership_for_week(
    conn: AsyncConnection, *, user_id: int, week_start: date
) -> LeagueMembership | None:
    params = {"user_id": user_id, "week_start": week_start}
    async with conn.cursor(row_factory=class_row(LeagueMembership)) as cur:
        await cur.execute(LEAGUE_MEMBERSHIP_FOR_WEEK, params)
        return await cur.fetchone()


async def get_latest_division(conn: AsyncConnection, *, user_id: int) -> int | None:
    async with conn.cursor() as cur:
        await cur.execute(LATEST_DIVISION, {"user_id": user_id})
        row = await cur.fetchone()
        return int(row[0]) if row is not None else None


async def get_member_rank(conn: AsyncConnection, *, league_id: int, user_id: int) -> int | None:
    params = {"league_id": league_id, "user_id": user_id}
    async with conn.cursor() as cur:
        await cur.execute(MEMBER_RANK, params)
        row = await cur.fetchone()
        return int(row[0]) if row is not None else None


async def list_ranked_members(
    conn: AsyncConnection, *, league_id: int
) -> list[LeagueRankedMemberRow]:
    async with conn.cursor(row_factory=class_row(LeagueRankedMemberRow)) as cur:
        await cur.execute(RANKED_MEMBERS, {"league_id": league_id})
        return await cur.fetchall()


async def list_member_user_ids_for_store_week(
    conn: AsyncConnection, *, store_id: int, week_start: date
) -> list[LeagueMemberUserRow]:
    params = {"store_id": store_id, "week_start": week_start}
    async with conn.cursor(row_factory=class_row(LeagueMemberUserRow)) as cur:
        await cur.execute(MEMBER_USER_IDS_FOR_STORE_WEEK, params)
        return await cur.fetchall()


async def list_store_ids_with_leagues(
    conn: AsyncConnection, *, week_start: date
) -> list[LeagueStoreWeekRow]:
    async with conn.cursor(row_factory=class_row(LeagueStoreWeekRow)) as cur:
        await cur.execute(STORE_IDS_WITH_LEAGUES, {"week_start": week_start})
        return await cur.fetchall()
