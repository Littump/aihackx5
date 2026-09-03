from decimal import ROUND_FLOOR, Decimal

from app import game_rules
from app.features.challenges.models import ChallengeDraft, ChallengeEconomics
from app.features.user_features.models import UserFeaturesRow


def evaluate(draft: ChallengeDraft, features: UserFeaturesRow) -> ChallengeEconomics:
    incremental_purchases = draft.target - draft.baseline
    incremental_revenue = incremental_purchases * features.avg_basket
    contribution_margin = Decimal(str(game_rules.CONTRIBUTION_MARGIN))
    incremental_margin = incremental_revenue * contribution_margin
    reward_share_max = Decimal(str(game_rules.REWARD_SHARE_MAX))
    max_reward_rub = incremental_margin * reward_share_max
    return ChallengeEconomics(
        avg_basket=float(features.avg_basket),
        expected_incremental_purchases=float(incremental_purchases),
        expected_incremental_margin=float(incremental_margin),
        max_reward_rub=float(max_reward_rub),
        contribution_margin=float(contribution_margin),
        reward_share_max=float(reward_share_max),
    )


def max_reward_points(max_reward_rub: Decimal) -> int:
    step = Decimal(game_rules.REWARD_POINTS_ROUNDING_STEP)
    floored_steps = (max_reward_rub / step).to_integral_value(rounding=ROUND_FLOOR)
    points = int(floored_steps * step)
    if points < game_rules.REWARD_POINTS_MIN:
        return 0
    return min(points, game_rules.REWARD_POINTS_MAX_WEEKLY)
