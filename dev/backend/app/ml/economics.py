from decimal import ROUND_FLOOR, Decimal

from app import game_rules
from app.ml import config
from app.ml.schemas import RewardComputation, RewardKind, RewardLevel

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


def reward_points_for_level(max_reward_rub_value: Decimal, reward_level: RewardLevel) -> int:
    share = Decimal(str(config.PROMO_LEVEL_SHARE[reward_level]))
    scaled = max_reward_rub_value * share
    step = Decimal(config.REWARD_POINTS_ROUNDING_STEP)
    floored = (scaled / step).to_integral_value(rounding=ROUND_FLOOR)
    points = int(floored * step)
    return min(points, config.REWARD_POINTS_MAX_WEEKLY)


def grade_multiplier(level: int, tenure_weeks: int) -> float:
    raw = _LADDER_MULTIPLIER_MAX - _LADDER_LEVEL_DECAY * (level - 1)
    raw -= _LADDER_TENURE_DECAY * tenure_weeks
    return max(_LADDER_MULTIPLIER_MIN, min(_LADDER_MULTIPLIER_MAX, raw))


def ladder_bonus_xp(reward_level: RewardLevel, level: int, tenure_weeks: int) -> int:
    base = config.LADDER_STAGE_BASE_XP[reward_level]
    return round(base * grade_multiplier(level, tenure_weeks))


def compute_reward(
    baseline: int,
    target: int,
    avg_basket: float,
    reward_kind: RewardKind,
    reward_level: RewardLevel,
    level: int,
    tenure_weeks: int,
) -> RewardComputation:
    budget = max_reward_rub(baseline, target, avg_basket)
    if reward_kind == "promo":
        points = reward_points_for_level(budget, reward_level)
        cost = round(points * game_rules.POINT_COST_RUB, 2)
        return RewardComputation(
            reward_kind=reward_kind,
            reward_level=reward_level,
            max_reward_rub=float(round(budget, 2)),
            reward_points=points,
            ladder_bonus_xp=0,
            reward_cost_rub=cost,
        )
    if reward_kind == "ladder":
        return RewardComputation(
            reward_kind=reward_kind,
            reward_level=reward_level,
            max_reward_rub=float(round(budget, 2)),
            reward_points=0,
            ladder_bonus_xp=ladder_bonus_xp(reward_level, level, tenure_weeks),
            reward_cost_rub=0.0,
        )
    return RewardComputation(
        reward_kind="none",
        reward_level="none",
        max_reward_rub=float(round(budget, 2)),
        reward_points=0,
        ladder_bonus_xp=0,
        reward_cost_rub=0.0,
    )
