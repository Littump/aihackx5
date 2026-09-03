import math

from app.ml import config
from app.ml.schemas import (
    ChallengePlan,
    ChallengeStep,
    ChurnRisk,
    PlannerInput,
)

_FREQUENCY_HEADROOM_MAX = 6.0
_RECENCY_MAX_DAYS = 21
_CATEGORY_MIN_SHARE = 0.10
_CATEGORY_MIN_VISITS = 3

_CHURN_TO_LEVEL: dict[ChurnRisk, str] = {"none": "low", "elevated": "medium", "high": "high"}


def target_corridor(baseline: int) -> tuple[int, int]:
    low = max(math.ceil(baseline * 1.2), baseline + 1)
    high = baseline + 2
    return low, max(low, high)


def clamp_target(baseline: int, target: int) -> int:
    low, high = target_corridor(baseline)
    return max(low, min(high, target))


def target_in_corridor(baseline: int, target: int) -> bool:
    low, high = target_corridor(baseline)
    return low <= target <= high


def fallback_plan(planner_input: PlannerInput) -> ChallengePlan:
    reward_level = _CHURN_TO_LEVEL[planner_input.features.churn_risk]
    step = _best_step(planner_input, reward_level)
    number = _first_number(planner_input)
    baseline = planner_input.features.baseline_visits
    rationale = f"rule-based: цель {step.target} при baseline {baseline}, сигнал {number}"
    return ChallengePlan(
        steps=[step], insight_used=["baseline_visits", "churn_risk"], rationale=rationale
    )


def _best_step(planner_input: PlannerInput, reward_level: str) -> ChallengeStep:
    features = planner_input.features
    overdue = _overdue_category(planner_input)
    baseline = features.baseline_visits
    target = clamp_target(baseline, baseline + 1)
    if features.churn_risk != "none" and overdue is not None:
        return ChallengeStep(
            challenge_type="replenishment",
            target=1,
            category=overdue,
            sku_refs=[],
            reward_kind="promo",
            reward_level=reward_level,  # type: ignore[arg-type]
            deadline_days=7,
        )
    if (
        features.frequency_per_week < _FREQUENCY_HEADROOM_MAX
        and features.recency_days <= _RECENCY_MAX_DAYS
    ):
        return ChallengeStep(
            challenge_type="frequency",
            target=target,
            category=None,
            sku_refs=[],
            reward_kind="promo",
            reward_level=reward_level,  # type: ignore[arg-type]
            deadline_days=7,
        )
    category = _top_category(planner_input)
    return ChallengeStep(
        challenge_type="category",
        target=clamp_target(0, 2),
        category=category,
        sku_refs=[],
        reward_kind="promo",
        reward_level=reward_level,  # type: ignore[arg-type]
        deadline_days=7,
    )


def _overdue_category(planner_input: PlannerInput) -> str | None:
    candidates = [
        series
        for series in planner_input.category_timeseries
        if series.days_overdue > 0 and series.category not in config.EXCLUDED_CATEGORIES
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda series: series.days_overdue, reverse=True)
    return candidates[0].category


def _top_category(planner_input: PlannerInput) -> str:
    eligible = [
        series
        for series in planner_input.category_timeseries
        if series.category not in config.EXCLUDED_CATEGORIES
        and series.share >= _CATEGORY_MIN_SHARE
        and series.visits >= _CATEGORY_MIN_VISITS
    ]
    if eligible:
        eligible.sort(key=lambda series: series.share, reverse=True)
        return eligible[0].category
    return "grocery"


def _first_number(planner_input: PlannerInput) -> str:
    features = planner_input.features
    return f"recency_days={features.recency_days}"
