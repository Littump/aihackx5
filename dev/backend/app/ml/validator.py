import re

from app.ml import config, economics, rules
from app.ml.schemas import (
    BuyerClassification,
    ChallengeOffer,
    ChallengePlan,
    ChallengeReward,
    NamedInsight,
    PlannedChallenge,
    PlannerGoal,
    PlannerInput,
    PointsLevel,
    SkuCatalogItem,
    ValidatedPlan,
)

_NUMBER_PATTERN = re.compile(r"-?\d+(\.\d+)?")
_POINTS_ORDER: tuple[PointsLevel, ...] = ("none", "low", "medium", "high")
_FREQUENCY_MECHANICS = frozenset({"frequency", "replenishment", "category"})
_BASKET_MECHANICS = frozenset({"basket", "collection", "category"})
_VALID_DIRECTIONS: dict[str, frozenset[str]] = {
    "visit_frequency": frozenset({"increase", "recover", "sustain"}),
    "basket_value": frozenset({"increase", "sustain"}),
}
_PROXY_TARGET: dict[str, str] = {
    "lapsed_category_rebuy": "visit_frequency",
    "add_category": "basket_value",
    "high_margin_category": "basket_value",
}


class ValidationResult:
    def __init__(self, errors: list[str], normalized: ChallengePlan) -> None:
        self.errors = errors
        self.normalized = normalized

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_plan(plan: ChallengePlan, planner_input: PlannerInput) -> ValidationResult:
    errors: list[str] = []
    classification = _normalize_classification(plan.classification, errors)
    _check_goal(plan.goal, errors)
    _check_insights(plan.insights, errors)
    insight_names = {insight.name for insight in plan.insights}
    normalized_challenges = [
        _normalize_challenge(challenge, plan, planner_input, insight_names, errors)
        for challenge in plan.challenges
    ]
    _check_hero(normalized_challenges, plan.goal, planner_input, errors)
    _check_strategy_refs(plan, insight_names, errors)
    _check_high_margin_mandate(normalized_challenges, planner_input, errors)
    normalized = ChallengePlan(
        thinking=plan.thinking,
        classification=classification,
        goal=plan.goal,
        insights=plan.insights,
        challenges=normalized_challenges or plan.challenges,
        general_strategy=plan.general_strategy,
    )
    return ValidationResult(errors, normalized)


def _normalize_classification(
    classification: BuyerClassification, errors: list[str]
) -> BuyerClassification:
    keywords = classification.keywords
    if not keywords or keywords[0] not in config.LIFECYCLE_KEYWORDS:
        errors.append("classification.keywords must start with one lifecycle keyword")
        return classification
    kept = [keywords[0]]
    for key in keywords[1:]:
        if key in config.LIFECYCLE_KEYWORDS:
            continue
        if key in config.MODIFIER_KEYWORDS or key.endswith("_lapsed"):
            kept.append(key)
            continue
        errors.append(f"classification keyword {key} not in palette")
    if not classification.evidence:
        errors.append("classification.evidence must cite metrics")
    if len(kept) < 2:
        errors.append("classification needs one lifecycle keyword and at least one modifier")
        return classification
    return classification.model_copy(update={"keywords": kept})


def _check_goal(goal: PlannerGoal, errors: list[str]) -> None:
    if goal.direction not in _VALID_DIRECTIONS[goal.target]:
        errors.append(f"goal direction {goal.direction} invalid for target {goal.target}")
    served = _PROXY_TARGET.get(goal.proxy)
    if served is not None and served != goal.target:
        errors.append(f"proxy {goal.proxy} serves {served}, not {goal.target}")
    if not _NUMBER_PATTERN.search(goal.rationale):
        errors.append("goal.rationale must cite a metric number")


def _check_insights(insights: list[NamedInsight], errors: list[str]) -> None:
    if not config.MIN_INSIGHTS <= len(insights) <= config.MAX_INSIGHTS:
        errors.append(f"insights count {len(insights)} outside 2..{config.MAX_INSIGHTS}")
    kinds = [insight.kind for insight in insights]
    if len(set(kinds)) != len(kinds):
        errors.append("insights must not repeat a kind")
    if not any(kind in config.ACTION_INSIGHT_KINDS for kind in kinds):
        errors.append("at least one insight must be an action kind")
    for insight in insights:
        if not _name_matches_kind(insight.name, insight.kind):
            errors.append(f"insight name {insight.name} does not match kind {insight.kind}")
        if not _NUMBER_PATTERN.search(insight.evidence_metric):
            errors.append(f"insight {insight.name} evidence_metric must resolve to a number")


def _name_matches_kind(name: str, kind: str) -> bool:
    if kind == "lapsed_category":
        return name.endswith("_lapsed")
    if kind == "staple_avoid":
        return name.endswith("_staple_avoid")
    if kind == "high_margin_push":
        return name.endswith("_high_margin")
    return name == kind


def _normalize_challenge(
    challenge: PlannedChallenge,
    plan: ChallengePlan,
    planner_input: PlannerInput,
    insight_names: set[str],
    errors: list[str],
) -> PlannedChallenge:
    baseline = baseline_for_challenge(challenge, planner_input)
    target = challenge.target
    if not rules.target_in_corridor(baseline, target):
        errors.append(f"target {target} outside corridor for baseline {baseline}")
        target = rules.clamp_target(baseline, target)
    category = challenge.category
    if category is not None and (
        category not in config.CATEGORIES or category in config.EXCLUDED_CATEGORIES
    ):
        errors.append(f"category {category} not allowed")
        category = None
    if challenge.insight_ref not in insight_names:
        errors.append(f"insight_ref {challenge.insight_ref} has no matching insight")
    reward = _normalize_reward(challenge.reward, plan.classification, planner_input)
    return PlannedChallenge(
        role=challenge.role,
        insight_ref=challenge.insight_ref,
        challenge_type=challenge.challenge_type,
        category=category,
        target=target,
        reward=reward,
        rationale=challenge.rationale,
    )


def _normalize_reward(
    reward: ChallengeReward, classification: BuyerClassification, planner_input: PlannerInput
) -> ChallengeReward:
    ceiling = config.points_ceiling(classification.posture, planner_input.features.churn_risk)
    points = reward.points_level
    if _POINTS_ORDER.index(points) > _POINTS_ORDER.index(ceiling):
        points = ceiling  # type: ignore[assignment]
    return ChallengeReward(xp_level=reward.xp_level, points_level=points)


def _check_hero(
    challenges: list[PlannedChallenge],
    goal: PlannerGoal,
    planner_input: PlannerInput,
    errors: list[str],
) -> None:
    heroes = [challenge for challenge in challenges if challenge.role == "hero"]
    if len(heroes) != 1:
        errors.append(f"plan must have exactly one hero challenge, found {len(heroes)}")
        return
    allowed = _FREQUENCY_MECHANICS if goal.target == "visit_frequency" else _BASKET_MECHANICS
    if heroes[0].challenge_type not in allowed:
        errors.append(
            f"hero mechanic {heroes[0].challenge_type} does not match target {goal.target}"
        )
    if heroes[0].challenge_type == "frequency" and not rules.frequency_mechanic_ok(
        planner_input.features
    ):
        errors.append(
            f"frequency hero invalid: cadence {planner_input.features.frequency_per_week}/wk "
            f"below {config.FREQUENCY_MECHANIC_MIN_PER_WEEK}/wk - a raw extra-trip ask is a "
            "fantasy; win with a category/replenishment re-buy (target 1) on a loved or lapsed "
            "category, or a basket play"
        )


def _check_strategy_refs(plan: ChallengePlan, insight_names: set[str], errors: list[str]) -> None:
    refs = set(plan.general_strategy.insight_refs)
    if refs != insight_names:
        errors.append("general_strategy.insight_refs must cover exactly all insights")


def _check_high_margin_mandate(
    challenges: list[PlannedChallenge], planner_input: PlannerInput, errors: list[str]
) -> None:
    if not planner_input.high_margin_mandate:
        return
    if not any(config.is_high_margin(challenge.category) for challenge in challenges):
        errors.append("plan must include one challenge on a high-margin category")


def baseline_for_challenge(challenge: PlannedChallenge, planner_input: PlannerInput) -> int:
    if challenge.challenge_type == "frequency":
        return planner_input.features.baseline_visits
    return 0


def finalize_plan(
    plan: ChallengePlan, planner_input: PlannerInput, plan_source: str, repair_count: int
) -> ValidatedPlan:
    offers: list[ChallengeOffer] = []
    for challenge in plan.challenges:
        baseline = baseline_for_challenge(challenge, planner_input)
        reward = economics.compute_reward(
            baseline=baseline,
            target=challenge.target,
            avg_basket=planner_input.features.avg_basket,
            xp_level=challenge.reward.xp_level,
            points_level=challenge.reward.points_level,
            level=planner_input.user.level,
            tenure_weeks=planner_input.user.tenure_weeks,
        )
        offers.append(
            ChallengeOffer(
                role=challenge.role,
                insight_ref=challenge.insight_ref,
                challenge_type=challenge.challenge_type,
                category=challenge.category,
                baseline=baseline,
                target=challenge.target,
                deadline_days=config.CHALLENGE_DEADLINE_DAYS,
                reward=reward,
                rationale=challenge.rationale,
            )
        )
    offers.sort(key=lambda offer: 0 if offer.role == "hero" else 1)
    return ValidatedPlan(
        offers=offers,
        classification=plan.classification,
        goal=plan.goal,
        insights=plan.insights,
        general_strategy=plan.general_strategy,
        plan_source=plan_source,  # type: ignore[arg-type]
        is_valid=plan_source == "llm",
        repair_count=repair_count,
    )


def catalog_id_set(catalog: list[SkuCatalogItem]) -> set[str]:
    return {item.sku_id for item in catalog}
