from decimal import Decimal

from app.features.users.models import RecommendedMechanicRow
from app.game_rules import (
    RECOMMENDED_MECHANIC_LEAGUE_MIN_COMPLETED,
    RECOMMENDED_MECHANIC_REFERRAL_MIN_COMPLETED,
    RECOMMENDED_MECHANIC_REFERRAL_MIN_SOCIAL_PROPENSITY,
)

REASON_FIRST_CHALLENGE = "Начни с первого челленджа"
REASON_LEAGUE = "Ты уже опытный — пора помериться силами в лиге"
REASON_REFERRAL = "Пригласи друзей — с ними копить веселее"
REASON_DEFAULT = "Выполни ещё один челлендж"


def choose_mechanic(
    *, completed_challenges_count: int, has_league: bool, social_propensity: Decimal
) -> RecommendedMechanicRow:
    if completed_challenges_count == 0:
        return RecommendedMechanicRow(mechanic="challenge", reason=REASON_FIRST_CHALLENGE)
    if completed_challenges_count >= RECOMMENDED_MECHANIC_LEAGUE_MIN_COMPLETED and has_league:
        return RecommendedMechanicRow(mechanic="league", reason=REASON_LEAGUE)
    if _referral_ready(completed_challenges_count, social_propensity):
        return RecommendedMechanicRow(mechanic="referral", reason=REASON_REFERRAL)
    return RecommendedMechanicRow(mechanic="challenge", reason=REASON_DEFAULT)


def _referral_ready(completed_challenges_count: int, social_propensity: Decimal) -> bool:
    propensity_min = Decimal(str(RECOMMENDED_MECHANIC_REFERRAL_MIN_SOCIAL_PROPENSITY))
    return (
        social_propensity >= propensity_min
        and completed_challenges_count >= RECOMMENDED_MECHANIC_REFERRAL_MIN_COMPLETED
    )
