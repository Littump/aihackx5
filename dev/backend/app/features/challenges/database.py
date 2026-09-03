from datetime import datetime
from decimal import Decimal
from typing import Literal

from psycopg import AsyncConnection
from psycopg.rows import class_row
from psycopg.types.json import Jsonb

from app.features.challenges.models import (
    ChallengeDraft,
    ChallengeEconomics,
    ChallengeRow,
    RewardKind,
    RewardLedgerEntry,
)

REWARD_LEDGER_INSERT = (
    "INSERT INTO reward_ledger (user_id, kind, xp_delta, points_delta, ref_type, ref_id) "
    "VALUES (%(user_id)s, %(kind)s, %(xp_delta)s, %(points_delta)s, %(ref_type)s, %(ref_id)s) "
    "RETURNING id, user_id, kind, xp_delta, points_delta, ref_type, ref_id, created_at"
)
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
CHALLENGE_EXPIRE_ACTIVE = (
    "UPDATE challenges SET status = 'expired' WHERE user_id = %(user_id)s AND status = 'active'"
)
CHALLENGE_SELECT_COLUMNS = (
    "id, user_id, type, category, status, is_hero, baseline, target, progress, "
    "period_start, period_end, reward_xp, reward_points, economics, rationale_features, "
    "copy_title, copy_body, copy_explanation, copy_source, created_at, completed_at"
)
CHALLENGE_LIST_BY_USER = (
    f"SELECT {CHALLENGE_SELECT_COLUMNS} FROM challenges "
    "WHERE user_id = %(user_id)s ORDER BY created_at DESC, id DESC"
)
CHALLENGE_GET_BY_ID = (
    f"SELECT {CHALLENGE_SELECT_COLUMNS} FROM challenges WHERE id = %(challenge_id)s"
)
CHALLENGE_LIST_ACTIVE_FOR_PERIOD = (
    f"SELECT {CHALLENGE_SELECT_COLUMNS} FROM challenges "
    "WHERE user_id = %(user_id)s AND status = 'active' "
    "AND period_start <= %(purchased_at)s AND period_end > %(purchased_at)s"
)
CHALLENGE_LIST_FOR_PERIOD_BY_STATUSES = (
    f"SELECT {CHALLENGE_SELECT_COLUMNS} FROM challenges "
    "WHERE user_id = %(user_id)s AND status = ANY(%(statuses)s) "
    "AND period_start <= %(purchased_at)s AND period_end > %(purchased_at)s"
)
CHALLENGE_UPDATE_PROGRESS = (
    "UPDATE challenges SET progress = %(progress)s, status = %(status)s, "
    "completed_at = %(completed_at)s WHERE id = %(challenge_id)s "
    f"RETURNING {CHALLENGE_SELECT_COLUMNS}"
)


async def insert_challenge(
    conn: AsyncConnection,
    *,
    user_id: int,
    draft: ChallengeDraft,
    economics: ChallengeEconomics,
    status: Literal["active", "completed", "failed", "expired"],
    is_hero: bool,
    progress: Decimal,
    period_start: datetime,
    period_end: datetime,
    reward_xp: int,
    reward_points: int,
    copy_title: str,
    copy_body: str,
    copy_explanation: str,
    copy_source: Literal["llm", "template"],
) -> ChallengeRow:
    params: dict[str, object] = {
        "user_id": user_id,
        "type": draft.type,
        "category": draft.category,
        "status": status,
        "is_hero": is_hero,
        "baseline": draft.baseline,
        "target": draft.target,
        "progress": progress,
        "period_start": period_start,
        "period_end": period_end,
        "reward_xp": reward_xp,
        "reward_points": reward_points,
        "economics": Jsonb(economics.model_dump(mode="json")),
        "rationale_features": Jsonb(draft.rationale_features.model_dump(exclude_none=True)),
        "copy_title": copy_title,
        "copy_body": copy_body,
        "copy_explanation": copy_explanation,
        "copy_source": copy_source,
    }
    return await insert_challenge_row(conn, params)


async def insert_challenge_row(conn: AsyncConnection, params: dict[str, object]) -> ChallengeRow:
    # raw-параметры нужны только tests/factories.make_challenge для гибких фикстур
    async with conn.cursor(row_factory=class_row(ChallengeRow)) as cur:
        await cur.execute(CHALLENGE_INSERT, params)
        row = await cur.fetchone()
        assert row is not None
        return row


async def insert_reward_ledger_entry(
    conn: AsyncConnection,
    *,
    user_id: int,
    kind: RewardKind,
    xp_delta: int,
    points_delta: int,
    ref_type: str | None,
    ref_id: int | None,
) -> RewardLedgerEntry:
    params = {
        "user_id": user_id,
        "kind": kind,
        "xp_delta": xp_delta,
        "points_delta": points_delta,
        "ref_type": ref_type,
        "ref_id": ref_id,
    }
    async with conn.cursor(row_factory=class_row(RewardLedgerEntry)) as cur:
        await cur.execute(REWARD_LEDGER_INSERT, params)
        row = await cur.fetchone()
        assert row is not None
        return row


async def expire_active_challenges(conn: AsyncConnection, *, user_id: int) -> None:
    async with conn.cursor() as cur:
        await cur.execute(CHALLENGE_EXPIRE_ACTIVE, {"user_id": user_id})


async def list_challenges_by_user(conn: AsyncConnection, *, user_id: int) -> list[ChallengeRow]:
    async with conn.cursor(row_factory=class_row(ChallengeRow)) as cur:
        await cur.execute(CHALLENGE_LIST_BY_USER, {"user_id": user_id})
        return await cur.fetchall()


async def get_challenge_by_id(conn: AsyncConnection, *, challenge_id: int) -> ChallengeRow | None:
    async with conn.cursor(row_factory=class_row(ChallengeRow)) as cur:
        await cur.execute(CHALLENGE_GET_BY_ID, {"challenge_id": challenge_id})
        return await cur.fetchone()


async def list_active_challenges_for_period(
    conn: AsyncConnection, *, user_id: int, purchased_at: datetime
) -> list[ChallengeRow]:
    async with conn.cursor(row_factory=class_row(ChallengeRow)) as cur:
        params = {"user_id": user_id, "purchased_at": purchased_at}
        await cur.execute(CHALLENGE_LIST_ACTIVE_FOR_PERIOD, params)
        return await cur.fetchall()


async def list_challenges_for_period(
    conn: AsyncConnection, *, user_id: int, purchased_at: datetime, statuses: list[str]
) -> list[ChallengeRow]:
    async with conn.cursor(row_factory=class_row(ChallengeRow)) as cur:
        params = {"user_id": user_id, "purchased_at": purchased_at, "statuses": statuses}
        await cur.execute(CHALLENGE_LIST_FOR_PERIOD_BY_STATUSES, params)
        return await cur.fetchall()


async def update_progress(
    conn: AsyncConnection,
    *,
    challenge_id: int,
    progress: Decimal,
    status: Literal["active", "completed", "failed", "expired"],
    completed_at: datetime | None,
) -> ChallengeRow:
    params: dict[str, object] = {
        "challenge_id": challenge_id,
        "progress": progress,
        "status": status,
        "completed_at": completed_at,
    }
    async with conn.cursor(row_factory=class_row(ChallengeRow)) as cur:
        await cur.execute(CHALLENGE_UPDATE_PROGRESS, params)
        row = await cur.fetchone()
        assert row is not None
        return row
