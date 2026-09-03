from datetime import timedelta

from psycopg import AsyncConnection
from psycopg.types.json import Jsonb

from app.core.clock import now
from app.features.challenges import service as challenges_service
from app.features.challenges.models import RewardKind
from app.features.domovoy import database
from app.features.domovoy.models import DomovoyDelta, DomovoyLevelRow, DomovoyStateRow, Mood
from app.features.domovoy.progression import level_for_xp, mood_for_week
from app.features.receipts import service as receipts_service
from app.features.receipts.models import ReceiptRow
from app.game_rules import MOOD_SLEEPY_INACTIVITY_DAYS, XP_RECEIPT


async def get_levels(conn: AsyncConnection, *, user_ids: list[int]) -> list[DomovoyLevelRow]:
    if not user_ids:
        return []
    return await database.list_levels(conn, user_ids=user_ids)


async def get_state(conn: AsyncConnection, user_id: int) -> DomovoyStateRow:
    existing = await database.get_domovoy_state(conn, user_id=user_id)
    if existing is not None:
        return existing
    return await database.insert_domovoy_state(conn, _default_state_params(user_id))


def _default_state_params(user_id: int) -> dict[str, object]:
    return {
        "user_id": user_id,
        "xp": 0,
        "level": 1,
        "mood": "bored",
        "mood_reason": "",
        "streak_weeks": 0,
        "streak_freeze_available": True,
        "items": Jsonb([]),
    }


async def add_xp(
    conn: AsyncConnection,
    user_id: int,
    xp: int,
    *,
    kind: RewardKind,
    ref_type: str | None,
    ref_id: int | None,
) -> DomovoyStateRow:
    state = await get_state(conn, user_id)
    await challenges_service.record_reward(
        conn,
        user_id=user_id,
        kind=kind,
        xp_delta=xp,
        points_delta=0,
        ref_type=ref_type,
        ref_id=ref_id,
    )
    new_xp = state.xp + xp
    return await database.update_domovoy_xp(
        conn, user_id=user_id, xp=new_xp, level=level_for_xp(new_xp)
    )


async def on_receipt(conn: AsyncConnection, user_id: int, receipt: ReceiptRow) -> DomovoyDelta:
    xp_delta = XP_RECEIPT if receipt.counted else 0
    if xp_delta:
        state = await add_xp(
            conn, user_id, xp_delta, kind="receipt_xp", ref_type="receipt", ref_id=receipt.id
        )
    else:
        state = await get_state(conn, user_id)
    mood, mood_reason = await _recompute_mood(conn, user_id)
    last_fed_at = receipt.purchased_at if receipt.counted else state.last_fed_at
    updated = await database.update_domovoy_mood(
        conn, user_id=user_id, mood=mood, mood_reason=mood_reason, last_fed_at=last_fed_at
    )
    return DomovoyDelta(
        xp_delta=xp_delta,
        xp=updated.xp,
        level=updated.level,
        mood=updated.mood,
        mood_reason=updated.mood_reason,
        last_fed_at=updated.last_fed_at,
    )


async def _recompute_mood(conn: AsyncConnection, user_id: int) -> tuple[Mood, str]:
    since = now() - timedelta(days=MOOD_SLEEPY_INACTIVITY_DAYS)
    receipts = await receipts_service.list_counted_receipts_with_items(
        conn, user_id=user_id, since=since
    )
    return mood_for_week(receipts)
