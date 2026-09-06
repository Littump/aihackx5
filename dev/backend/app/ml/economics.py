from decimal import ROUND_FLOOR, Decimal

from app import game_rules
from app.ml import config
from app.ml.schemas import PointsLevel, RewardComputation, XpLevel

_LADDER_MULTIPLIER_MAX = 1.5
_LADDER_MULTIPLIER_MIN = 0.5
_LADDER_LEVEL_DECAY = 0.1
_LADDER_TENURE_DECAY = 0.01


def max_reward_rub(baseline: int, target: int, avg_basket: float) -> Decimal:
    incremental_purchases = Decimal(target - baseline)
    if incremental_purchases <= 0:
        return Decimal(0)
    incremental_revenue = incremental_purchases * Decimal(str(avg_basket))
    incremental_margin = incremental_revenue * Decimal(str(config.CONTRIBUTION_MARGIN))
    return incremental_margin * Decimal(str(config.REWARD_SHARE_MAX))


def reward_points_for_level(max_reward_rub_value: Decimal, points_level: PointsLevel) -> int:
    share = Decimal(str(config.POINTS_LEVEL_SHARE[points_level]))
    scaled = max_reward_rub_value * share
    step = Decimal(config.REWARD_POINTS_ROUNDING_STEP)
    floored = (scaled / step).to_integral_value(rounding=ROUND_FLOOR)
    points = int(floored * step)
    return min(points, config.REWARD_POINTS_MAX_WEEKLY)


def grade_multiplier(level: int, tenure_weeks: int) -> float:
    raw = _LADDER_MULTIPLIER_MAX - _LADDER_LEVEL_DECAY * (level - 1)
    raw -= _LADDER_TENURE_DECAY * tenure_weeks
    return max(_LADDER_MULTIPLIER_MIN, min(_LADDER_MULTIPLIER_MAX, raw))


def xp_amount(xp_level: XpLevel, level: int, tenure_weeks: int) -> int:
    base = config.XP_CHALLENGE * config.XP_LEVEL_MULTIPLIER[xp_level]
    return round(base * grade_multiplier(level, tenure_weeks))


def compute_reward(
    baseline: int,
    target: int,
    avg_basket: float,
    xp_level: XpLevel,
    points_level: PointsLevel,
    level: int,
    tenure_weeks: int,
) -> RewardComputation:
    budget = max_reward_rub(baseline, target, avg_basket)
    raw_points = reward_points_for_level(budget, points_level) if points_level != "none" else 0
    if raw_points < config.REWARD_POINTS_MIN:
        points = 0
        effective_points_level: PointsLevel = "none"
    else:
        points = raw_points
        effective_points_level = points_level
    cost = round(points * game_rules.POINT_COST_RUB, 2)
    return RewardComputation(
        xp_level=xp_level,
        points_level=effective_points_level,
        xp_amount=xp_amount(xp_level, level, tenure_weeks),
        max_reward_rub=float(round(budget, 2)),
        reward_points=points,
        reward_cost_rub=cost,
    )
