from psycopg import AsyncConnection
from psycopg.rows import class_row

from app.features.challenges.models import ChallengeRow

CHALLENGE_INSERT = (
    "INSERT INTO challenges (user_id, type, category, status, is_hero, baseline, target, "
    "progress, period_start, period_end, reward_xp, reward_points, economics, "
    "rationale_features, copy_title, copy_body, copy_explanation, copy_source) "
    "VALUES (%(user_id)s, %(type)s, %(category)s, %(status)s, %(is_hero)s, %(baseline)s, "
    "%(target)s, %(progress)s, %(period_start)s, %(period_end)s, %(reward_xp)s, "
    "%(reward_points)s, %(economics)s, %(rationale_features)s, %(copy_title)s, %(copy_body)s, "
    "%(copy_explanation)s, %(copy_source)s) "
    "RETURNING id, user_id, type, category, status, is_hero, baseline, target, progress, "
    "period_start, period_end, reward_xp, reward_points, economics, rationale_features, "
    "copy_title, copy_body, copy_explanation, copy_source, created_at, completed_at"
)


async def insert_challenge(conn: AsyncConnection, params: dict[str, object]) -> ChallengeRow:
    async with conn.cursor(row_factory=class_row(ChallengeRow)) as cur:
        await cur.execute(CHALLENGE_INSERT, params)
        row = await cur.fetchone()
        assert row is not None
        return row
