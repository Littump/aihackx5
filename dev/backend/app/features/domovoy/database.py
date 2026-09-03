from datetime import datetime

from psycopg import AsyncConnection
from psycopg.rows import class_row

from app.features.domovoy.models import DomovoyLevelRow, DomovoyStateRow, Mood

DOMOVOY_STATE_COLUMNS = (
    "user_id, xp, level, mood, mood_reason, streak_weeks, streak_freeze_available, "
    "items, last_fed_at, updated_at"
)
DOMOVOY_LEVELS_SELECT = (
    "SELECT user_id, level FROM domovoy_states WHERE user_id = ANY(%(user_ids)s)"
)
DOMOVOY_STATE_GET = (
    f"SELECT {DOMOVOY_STATE_COLUMNS} FROM domovoy_states WHERE user_id = %(user_id)s"
)
DOMOVOY_STATE_INSERT = (
    "INSERT INTO domovoy_states (user_id, xp, level, mood, mood_reason, streak_weeks, "
    "streak_freeze_available, items) "
    "VALUES (%(user_id)s, %(xp)s, %(level)s, %(mood)s, %(mood_reason)s, %(streak_weeks)s, "
    "%(streak_freeze_available)s, %(items)s) "
    f"RETURNING {DOMOVOY_STATE_COLUMNS}"
)
DOMOVOY_STATE_UPDATE_XP = (
    "UPDATE domovoy_states SET xp = %(xp)s, level = %(level)s, updated_at = now() "
    f"WHERE user_id = %(user_id)s RETURNING {DOMOVOY_STATE_COLUMNS}"
)
DOMOVOY_STATE_UPDATE_MOOD = (
    "UPDATE domovoy_states SET mood = %(mood)s, mood_reason = %(mood_reason)s, "
    "last_fed_at = %(last_fed_at)s, updated_at = now() "
    f"WHERE user_id = %(user_id)s RETURNING {DOMOVOY_STATE_COLUMNS}"
)


async def insert_domovoy_state(conn: AsyncConnection, params: dict[str, object]) -> DomovoyStateRow:
    async with conn.cursor(row_factory=class_row(DomovoyStateRow)) as cur:
        await cur.execute(DOMOVOY_STATE_INSERT, params)
        row = await cur.fetchone()
        assert row is not None
        return row


async def get_domovoy_state(conn: AsyncConnection, *, user_id: int) -> DomovoyStateRow | None:
    async with conn.cursor(row_factory=class_row(DomovoyStateRow)) as cur:
        await cur.execute(DOMOVOY_STATE_GET, {"user_id": user_id})
        return await cur.fetchone()


async def update_domovoy_xp(
    conn: AsyncConnection, *, user_id: int, xp: int, level: int
) -> DomovoyStateRow:
    async with conn.cursor(row_factory=class_row(DomovoyStateRow)) as cur:
        await cur.execute(DOMOVOY_STATE_UPDATE_XP, {"user_id": user_id, "xp": xp, "level": level})
        row = await cur.fetchone()
        assert row is not None
        return row


async def update_domovoy_mood(
    conn: AsyncConnection,
    *,
    user_id: int,
    mood: Mood,
    mood_reason: str,
    last_fed_at: datetime | None,
) -> DomovoyStateRow:
    params = {
        "user_id": user_id,
        "mood": mood,
        "mood_reason": mood_reason,
        "last_fed_at": last_fed_at,
    }
    async with conn.cursor(row_factory=class_row(DomovoyStateRow)) as cur:
        await cur.execute(DOMOVOY_STATE_UPDATE_MOOD, params)
        row = await cur.fetchone()
        assert row is not None
        return row


async def list_levels(conn: AsyncConnection, *, user_ids: list[int]) -> list[DomovoyLevelRow]:
    async with conn.cursor(row_factory=class_row(DomovoyLevelRow)) as cur:
        await cur.execute(DOMOVOY_LEVELS_SELECT, {"user_ids": user_ids})
        return await cur.fetchall()
