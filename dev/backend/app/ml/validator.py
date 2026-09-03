import re

from app.ml import config, economics, rules
from app.ml.schemas import (
    ChallengeOffer,
    ChallengePlan,
    ChallengeStep,
    PlannerInput,
    RewardKind,
    RewardLevel,
    SkuCatalogItem,
    ValidatedPlan,
)

_NUMBER_PATTERN = re.compile(r"\d+")


class ValidationResult:
    def __init__(self, errors: list[str], normalized: ChallengePlan) -> None:
        self.errors = errors
        self.normalized = normalized

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_plan(plan: ChallengePlan, planner_input: PlannerInput) -> ValidationResult:
    errors: list[str] = []
    catalog_ids = {item.sku_id for item in planner_input.catalog}
    if not 1 <= len(plan.steps) <= config.MAX_PLAN_STEPS:
        errors.append(f"steps length {len(plan.steps)} outside 1..{config.MAX_PLAN_STEPS}")
    normalized_steps = [
        _normalize_step(step, planner_input, catalog_ids, errors) for step in plan.steps
    ]
    if not _rationale_has_insight_number(plan.rationale, planner_input):
        errors.append("rationale lacks a number from insight")
    normalized = ChallengePlan(
        steps=normalized_steps or plan.steps,
        insight_used=plan.insight_used,
        rationale=plan.rationale,
    )
    return ValidationResult(errors, normalized)


def _normalize_step(
    step: ChallengeStep,
    planner_input: PlannerInput,
    catalog_ids: set[str],
    errors: list[str],
) -> ChallengeStep:
    baseline = baseline_for_step(step, planner_input)
    target = step.target
    if not rules.target_in_corridor(baseline, target):
        errors.append(f"target {target} outside corridor for baseline {baseline}")
        target = rules.clamp_target(baseline, target)
    valid_refs = [sku_id for sku_id in step.sku_refs if sku_id in catalog_ids]
    if len(valid_refs) != len(step.sku_refs):
        errors.append("plan references unknown sku_id")
    category = step.category
    if category is not None and (
        category not in config.CATEGORIES or category in config.EXCLUDED_CATEGORIES
    ):
        errors.append(f"category {category} not allowed")
        category = None
    reward_kind, reward_level = _normalize_reward(step, errors)
    deadline = max(1, min(14, step.deadline_days))
    return ChallengeStep(
        challenge_type=step.challenge_type,
        target=target,
        category=category,
        sku_refs=valid_refs,
        reward_kind=reward_kind,
        reward_level=reward_level,
        deadline_days=deadline,
    )


def _normalize_reward(step: ChallengeStep, errors: list[str]) -> tuple[RewardKind, RewardLevel]:
    reward_kind = step.reward_kind
    reward_level = step.reward_level
    if reward_kind == "none" and reward_level != "none":
        errors.append("reward_kind=none requires reward_level=none")
        reward_level = "none"
    if reward_kind != "none" and reward_level == "none":
        errors.append("reward_level=none requires reward_kind=none")
        reward_kind = "none"
    return reward_kind, reward_level


def baseline_for_step(step: ChallengeStep, planner_input: PlannerInput) -> int:
    if step.challenge_type == "frequency":
        return planner_input.features.baseline_visits
    return 0


def _rationale_has_insight_number(rationale: str, planner_input: PlannerInput) -> bool:
    insight_numbers = _insight_numbers(planner_input)
    tokens = {int(match) for match in _NUMBER_PATTERN.findall(rationale)}
    return bool(tokens & insight_numbers)


def _insight_numbers(planner_input: PlannerInput) -> set[int]:
    features = planner_input.features
    numbers: set[int] = {
        features.recency_days,
        features.baseline_visits,
        round(features.frequency_per_week),
        round(features.cadence_days),
        round(features.avg_basket),
    }
    for series in planner_input.category_timeseries:
        numbers.add(series.visits)
        numbers.add(round(series.cadence_days))
        numbers.add(round(series.days_overdue))
    return {value for value in numbers if value > 0}


def finalize_plan(
    plan: ChallengePlan, planner_input: PlannerInput, plan_source: str, repair_count: int
) -> ValidatedPlan:
    offers: list[ChallengeOffer] = []
    for index, step in enumerate(plan.steps):
        baseline = baseline_for_step(step, planner_input)
        reward = economics.compute_reward(
            baseline=baseline,
            target=step.target,
            avg_basket=planner_input.features.avg_basket,
            reward_kind=step.reward_kind,
            reward_level=step.reward_level,
            level=planner_input.user.level,
            tenure_weeks=planner_input.user.tenure_weeks,
        )
        offers.append(
            ChallengeOffer(
                plan_step=index,
                challenge_type=step.challenge_type,
                category=step.category,
                baseline=baseline,
                target=step.target,
                sku_refs=step.sku_refs,
                deadline_days=step.deadline_days,
                reward=reward,
                rationale=plan.rationale,
            )
        )
    return ValidatedPlan(
        offers=offers,
        plan_source=plan_source,  # type: ignore[arg-type]
        is_valid=plan_source == "llm",
        repair_count=repair_count,
        insight_used=plan.insight_used,
    )


def catalog_id_set(catalog: list[SkuCatalogItem]) -> set[str]:
    return {item.sku_id for item in catalog}
