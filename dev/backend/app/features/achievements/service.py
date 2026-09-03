from datetime import UTC, datetime, timedelta

from psycopg import AsyncConnection

from app.core.clock import now
from app.features.achievements import database
from app.features.achievements.models import AchievementContext, AchievementRow, AchievementView
from app.features.achievements.rules import evaluate
from app.features.challenges.models import ChallengeProgressDelta
from app.features.domovoy import service as domovoy_service
from app.features.receipts import service as receipts_service
from app.features.receipts.models import ReceiptDetail
from app.features.referrals import service as referrals_service
from app.features.savings import service as savings_service
from app.features.users import service as users_service
from app.game_rules import ACHIEVEMENT_EXPLORER_WINDOW_DAYS, XP_ACHIEVEMENT

ACHIEVEMENT_TITLES: dict[str, str] = {
    "first_receipt": "Первый чек",
    "first_challenge": "Первый челлендж",
    "streak_4": "Четыре недели подряд",
    "saver_1000": "Тысяча сэкономлено",
    "explorer": "Исследователь сетей",
    "neighbour": "Хороший сосед",
    "league_top3": "Топ-3 недели",
}

NEIGHBOUR_CODE = "neighbour"
_EARLIEST_POSSIBLE_RECEIPT = datetime(2000, 1, 1, tzinfo=UTC)


async def list_for_user(conn: AsyncConnection, user_id: int) -> list[AchievementView]:
    await users_service.get_user(conn, user_id)
    rows = await database.list_achievements_for_user(conn, user_id=user_id)
    return [_to_view(row) for row in rows]


def _to_view(row: AchievementRow) -> AchievementView:
    return AchievementView(
        code=row.code, title=ACHIEVEMENT_TITLES[row.code], unlocked_at=row.unlocked_at
    )


async def on_challenge_completed(
    conn: AsyncConnection, user_id: int, challenge_deltas: list[ChallengeProgressDelta]
) -> list[str]:
    if not any(delta.completed for delta in challenge_deltas):
        return []
    return await _unlock_many(conn, user_id, ["first_challenge"])


async def on_receipt(
    conn: AsyncConnection,
    user_id: int,
    *,
    receipt: ReceiptDetail,
    challenge_deltas: list[ChallengeProgressDelta],
    referral_status: str | None,
) -> list[str]:
    unlocked = await on_challenge_completed(conn, user_id, challenge_deltas)
    ctx = await _build_context(conn, user_id, receipt)
    unlocked += await _unlock_many(conn, user_id, evaluate(ctx))
    # neighbour достаётся рефереру, а не пользователю этого события — в unlocked не попадает
    await _check_neighbour(conn, user_id, referral_status)
    return unlocked


async def unlock(conn: AsyncConnection, user_id: int, code: str) -> str | None:
    row = await database.insert_achievement(conn, user_id=user_id, code=code)
    if row is None:
        return None
    await domovoy_service.add_xp(
        conn,
        user_id,
        XP_ACHIEVEMENT,
        kind="achievement",
        ref_type="achievement",
        ref_id=row.id,
        points_delta=0,
    )
    return code


async def _check_neighbour(
    conn: AsyncConnection, user_id: int, referral_status: str | None
) -> str | None:
    if referral_status != "rewarded":
        return None
    referrer_id = await _referrer_user_id(conn, user_id)
    if referrer_id is None:
        return None
    return await unlock(conn, referrer_id, NEIGHBOUR_CODE)


async def _referrer_user_id(conn: AsyncConnection, referee_user_id: int) -> int | None:
    referral = await referrals_service.get_referral_by_referee(conn, referee_user_id)
    return referral.referrer_user_id if referral is not None else None


async def _unlock_many(conn: AsyncConnection, user_id: int, codes: list[str]) -> list[str]:
    unlocked: list[str] = []
    for code in codes:
        result = await unlock(conn, user_id, code)
        if result is not None:
            unlocked.append(result)
    return unlocked


async def _build_context(
    conn: AsyncConnection, user_id: int, receipt: ReceiptDetail
) -> AchievementContext:
    state = await domovoy_service.get_state(conn, user_id)
    savings = await savings_service.summary(conn, user_id, period="month")
    return AchievementContext(
        is_first_receipt=await _is_first_counted_receipt(conn, user_id, receipt),
        streak_weeks=state.streak_weeks,
        savings_month=savings.amount,
        chains_last_30d=await _chains_last_30_days(conn, user_id),
    )


async def _is_first_counted_receipt(
    conn: AsyncConnection, user_id: int, receipt: ReceiptDetail
) -> bool:
    if not receipt.counted:
        return False
    receipts = await receipts_service.list_counted_receipts_with_items(
        conn, user_id=user_id, since=_EARLIEST_POSSIBLE_RECEIPT
    )
    return len(receipts) == 1


async def _chains_last_30_days(conn: AsyncConnection, user_id: int) -> list[str]:
    since = now() - timedelta(days=ACHIEVEMENT_EXPLORER_WINDOW_DAYS)
    receipts = await receipts_service.list_counted_receipts_with_items(
        conn, user_id=user_id, since=since
    )
    store_ids = list({receipt.store_id for receipt in receipts})
    stores = await users_service.get_stores_by_ids(conn, store_ids=store_ids)
    return [store.chain for store in stores]
