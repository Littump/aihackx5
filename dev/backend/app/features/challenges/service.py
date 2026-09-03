from datetime import datetime
from decimal import Decimal

from psycopg import AsyncConnection

from app.core.clock import week_end, week_start
from app.core.errors import AppError
from app.features.challenges import candidate, database, economics, personalization
from app.features.challenges.models import (
    ChallengeDraft,
    ChallengeListResult,
    ChallengeRow,
    RewardKind,
    RewardLedgerEntry,
)
from app.features.user_features import service as user_features_service
from app.features.user_features.models import UserFeaturesRow
from app.features.users import service as users_service
from app.game_rules import XP_CHALLENGE
from app.llm import domovoy_copy


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
