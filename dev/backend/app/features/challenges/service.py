from psycopg import AsyncConnection

from app.features.challenges import database
from app.features.challenges.models import RewardKind, RewardLedgerEntry


async def record_reward(
    conn: AsyncConnection,
    *,
    user_id: int,
    kind: RewardKind,
    xp_delta: int,
    points_delta: int,
    ref_type: str | None,
    ref_id: int | None,
) -> RewardLedgerEntry:
    return await database.insert_reward_ledger_entry(
        conn,
        {
            "user_id": user_id,
            "kind": kind,
            "xp_delta": xp_delta,
            "points_delta": points_delta,
            "ref_type": ref_type,
            "ref_id": ref_id,
        },
    )
