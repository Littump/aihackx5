from psycopg import AsyncConnection

from app.core.models import AppModel
from app.features.challenges import service as challenges_service
from app.features.challenges.models import ChallengeRow
from app.features.domovoy import service as domovoy_service
from app.features.domovoy.models import DomovoyStateRow
from app.features.pm import service as pm_service
from app.features.pm.models import MechanicDecisionContext
from app.features.savings import service as savings_service
from app.features.savings.models import SavingsSummary
from app.features.user_features import service as user_features_service
from app.features.users import recommend
from app.features.users import service as users_service
from app.features.users.models import (
    DomovoyStateSummary,
    RecommendedMechanicRow,
    ReferralTeaserRow,
    UserRow,
)
from app.game_rules import level_for_xp, xp_to_next_level
from app.llm import domovoy_copy

# лиги нет до BE-016, has_league для recommend.choose_mechanic всегда false
HAS_LEAGUE = False


class HomeAggregate(AppModel):
    user: UserRow
    domovoy: DomovoyStateSummary
    savings: SavingsSummary
    insight: str
    hero_challenge: ChallengeRow | None
    referral: ReferralTeaserRow
    recommended_mechanic: RecommendedMechanicRow


async def get_home(conn: AsyncConnection, user_id: int) -> HomeAggregate:
    user = await users_service.get_user(conn, user_id)
    domovoy_state = await domovoy_service.get_state(conn, user_id)
    savings = await savings_service.summary(conn, user_id, "month")
    hero_challenge = await _ensure_hero_challenge(conn, user_id)
    completed_count = await challenges_service.count_completed(conn, user_id)
    recommended = recommend.choose_mechanic(
        completed_challenges_count=completed_count,
        has_league=HAS_LEAGUE,
        social_propensity=user.social_propensity,
    )
    await pm_service.record_decision(
        conn,
        user_id=user_id,
        mechanic=recommended.mechanic,
        reason=recommended.reason,
        context=MechanicDecisionContext(
            completed_challenges_count=completed_count,
            has_league=HAS_LEAGUE,
            social_propensity=user.social_propensity,
        ),
    )
    features = await user_features_service.get(conn, user_id)
    insight = await domovoy_copy.render_insight(features=features, savings=savings)
    return HomeAggregate(
        user=user,
        domovoy=_domovoy_summary(domovoy_state),
        savings=savings,
        insight=insight,
        hero_challenge=hero_challenge,
        referral=ReferralTeaserRow(code=user.referral_code, invited_count=0, rewarded_count=0),
        recommended_mechanic=recommended,
    )


async def _ensure_hero_challenge(conn: AsyncConnection, user_id: int) -> ChallengeRow | None:
    result = await challenges_service.get_list(conn, user_id)
    if result.hero is not None or result.side:
        return result.hero
    refreshed = await challenges_service.refresh_weekly(conn, user_id)
    return refreshed.hero


def _domovoy_summary(state: DomovoyStateRow) -> DomovoyStateSummary:
    return DomovoyStateSummary(
        xp=state.xp,
        level=level_for_xp(state.xp),
        xp_to_next_level=xp_to_next_level(state.xp),
        mood=state.mood,
        mood_reason=state.mood_reason,
        streak_weeks=state.streak_weeks,
        items=state.items,
    )
