from datetime import date

from psycopg import AsyncConnection

from app.features.league import database
from app.features.league.models import LeagueRow
from app.game_rules import LEAGUE_SIZE


async def find_or_create_open_league(
    conn: AsyncConnection, *, store_id: int, division: int, week_start: date
) -> LeagueRow:
    open_league = await database.get_open_league(
        conn, store_id=store_id, division=division, week_start=week_start
    )
    if open_league is not None:
        size = await database.count_members(conn, league_id=open_league.id)
        if size < LEAGUE_SIZE:
            return open_league
        await database.close_league(conn, league_id=open_league.id)
    return await database.insert_league(
        conn, store_id=store_id, division=division, week_start=week_start, status="open"
    )
