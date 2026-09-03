from psycopg import AsyncConnection
from psycopg.rows import class_row

from app.features.achievements.models import AchievementRow

ACHIEVEMENT_COLUMNS = "id, user_id, code, unlocked_at"
ACHIEVEMENT_INSERT = (
    f"INSERT INTO achievements (user_id, code) VALUES (%(user_id)s, %(code)s) "
    "ON CONFLICT (user_id, code) DO NOTHING "
    f"RETURNING {ACHIEVEMENT_COLUMNS}"
)
ACHIEVEMENT_LIST_FOR_USER = (
    f"SELECT {ACHIEVEMENT_COLUMNS} FROM achievements WHERE user_id = %(user_id)s "
    "ORDER BY unlocked_at ASC, id ASC"
)


async def insert_achievement(
    conn: AsyncConnection, *, user_id: int, code: str
) -> AchievementRow | None:
    async with conn.cursor(row_factory=class_row(AchievementRow)) as cur:
        await cur.execute(ACHIEVEMENT_INSERT, {"user_id": user_id, "code": code})
        return await cur.fetchone()


async def list_achievements_for_user(
    conn: AsyncConnection, *, user_id: int
) -> list[AchievementRow]:
    async with conn.cursor(row_factory=class_row(AchievementRow)) as cur:
        await cur.execute(ACHIEVEMENT_LIST_FOR_USER, {"user_id": user_id})
        return await cur.fetchall()
