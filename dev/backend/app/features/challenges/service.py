from datetime import datetime
from decimal import Decimal
from typing import Literal

from psycopg import AsyncConnection

from app.core.clock import now, week_end, week_start
from app.core.errors import AppError
from app.features.challenges import candidate, database, economics, personalization
from app.features.challenges.models import (
    ChallengeDraft,
    ChallengeListResult,
    ChallengeProgressDelta,
    ChallengeRow,
    RewardKind,
    RewardLedgerEntry,
)
from app.features.receipts.models import ReceiptDetail
from app.features.user_features import service as user_features_service
from app.features.user_features.models import UserFeaturesRow
from app.features.users import service as users_service
from app.game_rules import CHALLENGE_PROGRESS_STEP, XP_CHALLENGE
from app.llm import domovoy_copy

RETURN_LOOKUP_STATUSES: list[str] = ["active", "completed"]


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
        user_id=user_id,
        kind=kind,
        xp_delta=xp_delta,
        points_delta=points_delta,
        ref_type=ref_type,
        ref_id=ref_id,
    )


async def on_receipt(
    conn: AsyncConnection, user_id: int, receipt: ReceiptDetail
) -> list[ChallengeProgressDelta]:
    if not receipt.counted:
        return []
    challenges = await database.list_active_challenges_for_period(
        conn, user_id=user_id, purchased_at=receipt.purchased_at
    )
    deltas: list[ChallengeProgressDelta] = []
    for challenge in challenges:
        if _matches_receipt(challenge, receipt):
            deltas.append(await _advance_progress(conn, user_id, challenge))
    return deltas


async def on_receipt_returned(
    conn: AsyncConnection, user_id: int, receipt: ReceiptDetail
) -> list[ChallengeProgressDelta]:
    if not receipt.counted:
        return []
    challenges = await database.list_challenges_for_period(
        conn, user_id=user_id, purchased_at=receipt.purchased_at, statuses=RETURN_LOOKUP_STATUSES
    )
    deltas: list[ChallengeProgressDelta] = []
    for challenge in challenges:
        if _matches_receipt(challenge, receipt):
            deltas.append(await _revert_progress(conn, user_id, challenge))
    return deltas


def _matches_receipt(challenge: ChallengeRow, receipt: ReceiptDetail) -> bool:
    if challenge.type == "frequency":
        return True
    categories = {item.category for item in receipt.items}
    return challenge.category in categories


async def _advance_progress(
    conn: AsyncConnection, user_id: int, challenge: ChallengeRow
) -> ChallengeProgressDelta:
    progress_before = challenge.progress
    progress_after = progress_before + Decimal(CHALLENGE_PROGRESS_STEP)
    completed = progress_after >= challenge.target
    status: Literal["active", "completed"] = "completed" if completed else "active"
    updated = await database.update_progress(
        conn,
        challenge_id=challenge.id,
        progress=progress_after,
        status=status,
        completed_at=now() if completed else None,
    )
    if completed:
        await _reward_completion(conn, user_id, challenge)
    return ChallengeProgressDelta(
        challenge_id=challenge.id,
        progress_before=progress_before,
        progress_after=updated.progress,
        target=challenge.target,
        completed=completed,
        reward_points=challenge.reward_points if completed else 0,
        reward_xp=challenge.reward_xp if completed else 0,
    )


async def _reward_completion(conn: AsyncConnection, user_id: int, challenge: ChallengeRow) -> None:
    # отложенный импорт разрывает цикл: domovoy.service импортирует нас
    from app.features.domovoy import service as domovoy_service

    await domovoy_service.add_xp(
        conn,
        user_id,
        challenge.reward_xp,
        kind="challenge",
        ref_type="challenge",
        ref_id=challenge.id,
        points_delta=challenge.reward_points,
    )
    if challenge.is_hero:
        await domovoy_service.advance_streak(conn, user_id, completed_this_week=True)


async def _revert_progress(
    conn: AsyncConnection, user_id: int, challenge: ChallengeRow
) -> ChallengeProgressDelta:
    progress_before = challenge.progress
    progress_after = progress_before - Decimal(CHALLENGE_PROGRESS_STEP)
    reopened = challenge.status == "completed" and progress_after < challenge.target
    status = "active" if reopened else challenge.status
    updated = await database.update_progress(
        conn,
        challenge_id=challenge.id,
        progress=progress_after,
        status=status,
        completed_at=None if reopened else challenge.completed_at,
    )
    if reopened:
        await record_reward(
            conn,
            user_id=user_id,
            kind="challenge",
            xp_delta=0,
            points_delta=-challenge.reward_points,
            ref_type="challenge",
            ref_id=challenge.id,
        )
    return ChallengeProgressDelta(
        challenge_id=challenge.id,
        progress_before=progress_before,
        progress_after=updated.progress,
        target=challenge.target,
        completed=updated.status == "completed",
        reward_points=-challenge.reward_points if reopened else 0,
        reward_xp=0,
    )


async def refresh_weekly(conn: AsyncConnection, user_id: int) -> ChallengeListResult:
    await users_service.get_user(conn, user_id)
    await database.expire_active_challenges(conn, user_id=user_id)
    features = await user_features_service.get(conn, user_id)
    drafts = candidate.build(features)
    hero_draft, side_drafts = personalization.rank(drafts)
    period_start, period_end = week_start(), week_end()
    await _insert_draft(
        conn, hero_draft, features, is_hero=True, period_start=period_start, period_end=period_end
    )
    for draft in side_drafts:
        await _insert_draft(
            conn, draft, features, is_hero=False, period_start=period_start, period_end=period_end
        )
    return await get_list(conn, user_id)


async def get_list(conn: AsyncConnection, user_id: int) -> ChallengeListResult:
    await users_service.get_user(conn, user_id)
    rows = await database.list_challenges_by_user(conn, user_id=user_id)
    hero = next((row for row in rows if row.status == "active" and row.is_hero), None)
    side = [row for row in rows if row.status == "active" and not row.is_hero]
    history = [row for row in rows if row.status != "active"]
    return ChallengeListResult(hero=hero, side=side, history=history)


async def count_completed(conn: AsyncConnection, user_id: int) -> int:
    return await database.count_completed_challenges(conn, user_id=user_id)


async def count_completed_in_period(
    conn: AsyncConnection, *, user_id: int, start: datetime, end: datetime
) -> int:
    return await database.count_completed_challenges_in_period(
        conn, user_id=user_id, start=start, end=end
    )


async def get_one(conn: AsyncConnection, user_id: int, challenge_id: int) -> ChallengeRow:
    await users_service.get_user(conn, user_id)
    row = await database.get_challenge_by_id(conn, challenge_id=challenge_id)
    if row is None or row.user_id != user_id:
        raise AppError("challenge_not_found", "челлендж не найден", 404)
    return row


async def _insert_draft(
    conn: AsyncConnection,
    draft: ChallengeDraft,
    features: UserFeaturesRow,
    *,
    is_hero: bool,
    period_start: datetime,
    period_end: datetime,
) -> ChallengeRow:
    result = economics.evaluate(draft, features)
    reward_points = economics.max_reward_points(Decimal(str(result.max_reward_rub)))
    copy = await domovoy_copy.render_challenge(challenge=draft, features=features)
    return await database.insert_challenge(
        conn,
        user_id=features.user_id,
        draft=draft,
        economics=result,
        status="active",
        is_hero=is_hero,
        progress=Decimal("0"),
        period_start=period_start,
        period_end=period_end,
        reward_xp=XP_CHALLENGE,
        reward_points=reward_points,
        copy_title=copy.title,
        copy_body=copy.body,
        copy_explanation=copy.explanation,
        copy_source=copy.source,
    )
