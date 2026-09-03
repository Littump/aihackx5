from psycopg import AsyncConnection
from psycopg.rows import class_row

from app.features.domovoy.models import DomovoyLevelRow, DomovoyStateRow

DOMOVOY_LEVELS_SELECT = (
    "SELECT user_id, level FROM domovoy_states WHERE user_id = ANY(%(user_ids)s)"
)
DOMOVOY_STATE_INSERT = (
    "INSERT INTO domovoy_states (user_id, xp, level, mood, mood_reason, streak_weeks, "
    "streak_freeze_available, items) "
    "VALUES (%(user_id)s, %(xp)s, %(level)s, %(mood)s, %(mood_reason)s, %(streak_weeks)s, "
    "%(streak_freeze_available)s, %(items)s) "
    "RETURNING user_id, xp, level, mood, mood_reason, streak_weeks, streak_freeze_available, "
    "items, last_fed_at, updated_at"
)


async def insert_domovoy_state(conn: AsyncConnection, params: dict[str, object]) -> DomovoyStateRow:
    async with conn.cursor(row_factory=class_row(DomovoyStateRow)) as cur:
        await cur.execute(DOMOVOY_STATE_INSERT, params)
        row = await cur.fetchone()
        assert row is not None
        return row


async def list_levels(conn: AsyncConnection, *, user_ids: list[int]) -> list[DomovoyLevelRow]:
    async with conn.cursor(row_factory=class_row(DomovoyLevelRow)) as cur:
        await cur.execute(DOMOVOY_LEVELS_SELECT, {"user_ids": user_ids})
        return await cur.fetchall()
