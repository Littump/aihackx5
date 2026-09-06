import math

from app.ml import config
from app.ml.schemas import (
    BuyerClassification,
    CategoryTimeseries,
    ChallengePlan,
    ChallengeReward,
    GeneralStrategy,
    NamedInsight,
    PlannedChallenge,
    PlannerFeatures,
    PlannerGoal,
    PlannerInput,
    PointsLevel,
    Posture,
    XpLevel,
)

_POINTS_ORDER: tuple[PointsLevel, ...] = ("none", "low", "medium", "high")
_DIRECTION_POINTS: dict[str, PointsLevel] = {
    "recover": "high",
    "increase": "medium",
    "sustain": "none",
}
_DIRECTION_XP: dict[str, XpLevel] = {"recover": "high", "increase": "medium", "sustain": "low"}


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


def frequency_mechanic_ok(features: PlannerFeatures) -> bool:
    return features.frequency_per_week >= config.FREQUENCY_MECHANIC_MIN_PER_WEEK


def lifecycle_keyword(features: PlannerFeatures) -> str:
    if features.overdue_ratio > config.OVERDUE_DORMANT:
        return "dormant"
    if config.OVERDUE_COOLING_MIN < features.overdue_ratio <= config.OVERDUE_DORMANT:
        return "cooling"
    if features.visit_momentum > config.MOMENTUM_RISING:
        return "rising"
    return "steady"


def lapsed_category(planner_input: PlannerInput) -> CategoryTimeseries | None:
    candidates = [
        series
        for series in planner_input.category_timeseries
        if series.category not in config.EXCLUDED_CATEGORIES
        and series.share >= config.CATEGORY_MIN_SHARE
        and series.share < config.STAPLE_SHARE_MIN
        and series.visits >= config.CATEGORY_MIN_VISITS
        and (series.days_overdue + series.cadence_days) / max(series.cadence_days, 1.0)
        >= config.TOP_CATEGORY_OVERDUE_MIN
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda series: series.days_overdue, reverse=True)
    return candidates[0]


def favourite_series(planner_input: PlannerInput) -> CategoryTimeseries | None:
    loved = [
        series
        for series in planner_input.category_timeseries
        if series.category not in config.EXCLUDED_CATEGORIES
        and series.share >= config.CATEGORY_MIN_SHARE
    ]
    if not loved:
        return None
    loved.sort(key=lambda series: series.share, reverse=True)
    return loved[0]


def staple_category(planner_input: PlannerInput) -> CategoryTimeseries | None:
    staples = [
        series
        for series in planner_input.category_timeseries
        if series.share >= config.STAPLE_SHARE_MIN and series.visits >= config.STAPLE_MIN_VISITS
    ]
    staples.sort(key=lambda series: series.share, reverse=True)
    return staples[0] if staples else None


def high_margin_pick(planner_input: PlannerInput) -> str:
    owned = [
        series
        for series in planner_input.category_timeseries
        if series.is_high_margin and series.category not in config.EXCLUDED_CATEGORIES
    ]
    non_staple = [series for series in owned if series.share < config.STAPLE_SHARE_MIN]
    if non_staple:
        non_staple.sort(key=lambda series: series.share, reverse=True)
        return non_staple[0].category
    owned_categories = {series.category for series in owned}
    fresh = [
        category
        for category in config.HIGH_MARGIN_CATEGORIES
        if category not in owned_categories and category not in config.EXCLUDED_CATEGORIES
    ]
    if fresh:
        return max(
            fresh, key=lambda category: config.CATEGORY_CONTRIBUTION_MARGIN.get(category, 0.0)
        )
    if owned:
        owned.sort(key=lambda series: series.share, reverse=True)
        return owned[0].category
    return max(
        config.HIGH_MARGIN_CATEGORIES,
        key=lambda category: config.CATEGORY_CONTRIBUTION_MARGIN.get(category, 0.0),
    )


def posture_for(promo_sensitivity: float) -> Posture:
    low, high = config.POSTURE_PROMO_CUTS
    if promo_sensitivity < low:
        return "promo_immune"
    if promo_sensitivity < high:
        return "value_selective"
    return "deal_driven"


def _modifiers(planner_input: PlannerInput, lapse: CategoryTimeseries | None) -> list[str]:
    features = planner_input.features
    modifiers: list[str] = []
    if features.visit_momentum <= config.MOMENTUM_FORMERLY_ACTIVE:
        modifiers.append("formerly_active")
    if (
        features.visit_headroom_ratio >= config.HEADROOM_HAS_ROOM
        and features.recency_days <= config.HEADROOM_ACTIVE_RECENCY_DAYS
    ):
        modifiers.append("has_headroom")
    if features.visit_headroom_ratio < config.HEADROOM_AT_CEILING:
        modifiers.append("at_ceiling")
    if features.basket_index >= config.BASKET_LARGE_INDEX:
        modifiers.append("large_basket")
    elif features.basket_index <= config.BASKET_SMALL_INDEX:
        modifiers.append("small_basket")
    if features.category_breadth >= config.CATEGORY_BROAD_MIN:
        modifiers.append("broad")
    if staple_category(planner_input) is not None:
        modifiers.append("day_to_day")
    if lapse is not None:
        modifiers.append(f"{lapse.category}_lapsed")
    return modifiers[:4]


def _is_ambiguous(features: PlannerFeatures) -> bool:
    band = config.AMBIGUOUS_BOUNDARY_BAND
    for boundary in (config.OVERDUE_COOLING_MIN, config.OVERDUE_DORMANT):
        if abs(features.overdue_ratio - boundary) <= band:
            return True
    return False


def classify(planner_input: PlannerInput, lapse: CategoryTimeseries | None) -> BuyerClassification:
    features = planner_input.features
    lifecycle = lifecycle_keyword(features)
    keywords = [lifecycle, *_modifiers(planner_input, lapse)][:5]
    label = _compose_label(keywords)
    evidence = _evidence(features, keywords)
    return BuyerClassification(
        keywords=keywords,
        label=label,
        description=f"Rule-derived buyer: {label.lower()} on the observed metrics.",
        evidence=evidence,
        posture=posture_for(features.promo_sensitivity),
        is_ambiguous=_is_ambiguous(features),
    )


def _compose_label(keywords: list[str]) -> str:
    return " ".join(part.replace("_", " ").title() for part in keywords)


def _evidence(features: PlannerFeatures, keywords: list[str]) -> list[str]:
    metrics: dict[str, str] = {
        "rising": f"visit_momentum={features.visit_momentum}",
        "cooling": f"overdue_ratio={features.overdue_ratio}",
        "dormant": f"overdue_ratio={features.overdue_ratio}",
        "steady": f"cadence_regularity={features.cadence_regularity}",
        "formerly_active": f"visit_momentum={features.visit_momentum}",
        "has_headroom": f"visit_headroom_ratio={features.visit_headroom_ratio}",
        "at_ceiling": f"visit_headroom_ratio={features.visit_headroom_ratio}",
        "large_basket": f"basket_index={features.basket_index}",
        "small_basket": f"basket_index={features.basket_index}",
        "broad": f"category_breadth={features.category_breadth}",
        "day_to_day": f"top_category_overdue_ratio={features.top_category_overdue_ratio}",
    }
    evidence = [metrics[key] for key in keywords if key in metrics]
    if any(key.endswith("_lapsed") for key in keywords):
        evidence.append(f"top_category_overdue_ratio={features.top_category_overdue_ratio}")
    return evidence


def choose_goal(
    planner_input: PlannerInput,
    lifecycle: str,
    lapse: CategoryTimeseries | None,
    rebuy: CategoryTimeseries | None,
) -> PlannerGoal:
    features = planner_input.features
    has_headroom = (
        features.visit_headroom_ratio >= config.HEADROOM_HAS_ROOM
        and features.recency_days <= config.HEADROOM_ACTIVE_RECENCY_DAYS
    )
    large_or_broad = (
        features.basket_index >= config.BASKET_LARGE_INDEX
        or features.category_breadth >= config.CATEGORY_BROAD_MIN
    )
    if lifecycle in ("dormant", "cooling"):
        proxy = "lapsed_category_rebuy" if rebuy is not None else "none"
        return _goal("visit_frequency", proxy, "recover", features)
    if lapse is not None:
        return _goal("visit_frequency", "lapsed_category_rebuy", "recover", features)
    if (lifecycle == "rising" or has_headroom) and frequency_mechanic_ok(features):
        return _goal("visit_frequency", "none", "increase", features)
    direction = "increase" if large_or_broad else "sustain"
    return _goal("basket_value", "add_category", direction, features)


def _goal(target: str, proxy: str, direction: str, features: PlannerFeatures) -> PlannerGoal:
    metric = {
        "visit_frequency": f"overdue_ratio={features.overdue_ratio}, "
        f"visit_headroom_ratio={features.visit_headroom_ratio}",
        "basket_value": f"basket_index={features.basket_index}, "
        f"category_breadth={features.category_breadth}",
    }[target]
    proxy_metric = (
        f"; top_category_overdue_ratio={features.top_category_overdue_ratio}"
        if proxy == "lapsed_category_rebuy"
        else ""
    )
    return PlannerGoal(
        target=target,  # type: ignore[arg-type]
        proxy=proxy,  # type: ignore[arg-type]
        direction=direction,  # type: ignore[arg-type]
        rationale=f"{target}/{direction} from {metric}{proxy_metric}",
    )


def _clamp_points(level: PointsLevel, ceiling: PointsLevel) -> PointsLevel:
    return level if _POINTS_ORDER.index(level) <= _POINTS_ORDER.index(ceiling) else ceiling


def reward_for(direction: str, posture: Posture, churn_risk: str) -> ChallengeReward:
    ceiling = config.points_ceiling(posture, churn_risk)
    points = _clamp_points(_DIRECTION_POINTS[direction], ceiling)  # type: ignore[arg-type]
    return ChallengeReward(xp_level=_DIRECTION_XP[direction], points_level=points)


def fallback_plan(planner_input: PlannerInput) -> ChallengePlan:
    features = planner_input.features
    lapse = lapsed_category(planner_input)
    lifecycle = lifecycle_keyword(features)
    rebuy = lapse
    if rebuy is None and lifecycle in ("dormant", "cooling"):
        rebuy = favourite_series(planner_input)
    classification = classify(planner_input, lapse)
    goal = choose_goal(planner_input, lifecycle, lapse, rebuy)
    hero_insight = _hero_insight(planner_input, lifecycle, rebuy)
    hero = _hero_challenge(planner_input, goal, classification.posture, hero_insight, rebuy)
    insights = [hero_insight, _reward_posture_insight(features, classification.posture)]
    challenges = [hero]
    if planner_input.high_margin_mandate and not _has_high_margin(challenges):
        side_insight, side = _high_margin_side(planner_input, classification.posture)
        insights.append(side_insight)
        challenges.append(side)
    names = [insight.name for insight in insights]
    strategy = GeneralStrategy(
        insight_refs=names,
        rationale=(
            f"Rule plan: {goal.target}/{goal.direction} via {goal.proxy}; "
            f"hero {hero.challenge_type}; covers {', '.join(names)}."
        ),
        next_week_hint="Re-derive keywords next week; drop the proxy once the lapse closes.",
    )
    return ChallengePlan(
        thinking=(
            f"lifecycle={lifecycle}, overdue_ratio={features.overdue_ratio}, "
            f"visit_headroom_ratio={features.visit_headroom_ratio} -> "
            f"{goal.target}/{goal.direction}."
        ),
        classification=classification,
        goal=goal,
        insights=insights,
        challenges=challenges,
        general_strategy=strategy,
    )


def _has_high_margin(challenges: list[PlannedChallenge]) -> bool:
    return any(config.is_high_margin(challenge.category) for challenge in challenges)


def _hero_insight(
    planner_input: PlannerInput, lifecycle: str, rebuy: CategoryTimeseries | None
) -> NamedInsight:
    features = planner_input.features
    if rebuy is not None:
        return NamedInsight(
            name=f"{rebuy.category}_lapsed",
            kind="lapsed_category",
            behaviour=f"buys {rebuy.category} every ~{round(rebuy.cadence_days)}d "
            f"but overdue {round(rebuy.days_overdue)}d",
            dod=f"re-buys {rebuy.category} within a week",
            strategy_hint=f"replenishment on {rebuy.category}, target 1",
            evidence_metric=f"top_category_overdue_ratio={features.top_category_overdue_ratio}",
        )
    if lifecycle == "dormant":
        return NamedInsight(
            name="dormant_gap",
            kind="dormant_gap",
            behaviour=f"absent {features.recency_days}d, near-lapsed",
            dod="a single return visit within the deadline",
            strategy_hint="low-friction frequency, target 1, strong reward",
            evidence_metric=f"recency_days={features.recency_days}",
        )
    if lifecycle == "cooling":
        return NamedInsight(
            name="churn_drift",
            kind="churn_drift",
            behaviour=f"last visit {features.recency_days}d ago vs cadence "
            f"{round(features.cadence_days)}d - drifting",
            dod="returns before the deadline",
            strategy_hint="frequency win-back, medium reward",
            evidence_metric=f"overdue_ratio={features.overdue_ratio}",
        )
    if lifecycle == "rising":
        return NamedInsight(
            name="momentum_ride",
            kind="momentum_ride",
            behaviour=f"visiting faster lately (visit_momentum {features.visit_momentum})",
            dod="hold the higher pace one more week",
            strategy_hint="frequency stretch, small reward",
            evidence_metric=f"visit_momentum={features.visit_momentum}",
        )
    if features.visit_headroom_ratio >= config.HEADROOM_HAS_ROOM:
        return NamedInsight(
            name="visit_headroom",
            kind="visit_headroom",
            behaviour=f"visits ~{features.frequency_per_week}/wk, room for one more",
            dod="one extra visit this week",
            strategy_hint="frequency, target baseline+1",
            evidence_metric=f"visit_headroom_ratio={features.visit_headroom_ratio}",
        )
    return NamedInsight(
        name="basket_depth",
        kind="basket_depth",
        behaviour=f"large baskets ~{round(features.avg_basket)}₽ across "
        f"{features.category_breadth} categories",
        dod="adds one complementary category/combo",
        strategy_hint="basket/collection pairing",
        evidence_metric=f"basket_index={features.basket_index}",
    )


def _reward_posture_insight(features: PlannerFeatures, posture: Posture) -> NamedInsight:
    return NamedInsight(
        name="reward_posture",
        kind="reward_posture",
        behaviour=f"promo_sensitivity {features.promo_sensitivity} -> {posture}",
        dod="reward mix matches posture",
        strategy_hint="xp always; points_level per posture and budget",
        evidence_metric=f"promo_sensitivity={features.promo_sensitivity}",
    )


def _hero_challenge(
    planner_input: PlannerInput,
    goal: PlannerGoal,
    posture: Posture,
    hero_insight: NamedInsight,
    rebuy: CategoryTimeseries | None,
) -> PlannedChallenge:
    features = planner_input.features
    reward = reward_for(goal.direction, posture, features.churn_risk)
    if goal.target == "visit_frequency":
        if goal.proxy == "lapsed_category_rebuy" and rebuy is not None:
            return PlannedChallenge(
                role="hero",
                insight_ref=hero_insight.name,
                challenge_type="replenishment",
                category=rebuy.category,
                target=1,
                reward=reward,
                rationale=f"re-buy loved {rebuy.category}, overdue "
                f"{round(rebuy.days_overdue)}d - a timely incremental trip",
            )
        if not frequency_mechanic_ok(features):
            rebuy_category = (
                rebuy.category if rebuy is not None else high_margin_pick(planner_input)
            )
            return PlannedChallenge(
                role="hero",
                insight_ref=hero_insight.name,
                challenge_type="category",
                category=rebuy_category,
                target=1,
                reward=reward,
                rationale=f"single return purchase of {rebuy_category} - one incremental trip "
                f"for a {round(features.frequency_per_week, 2)}/wk shopper (raw frequency ask "
                "would be a fantasy)",
            )
        baseline = features.baseline_visits
        return PlannedChallenge(
            role="hero",
            insight_ref=hero_insight.name,
            challenge_type="frequency",
            category=None,
            target=clamp_target(baseline, baseline + 1),
            reward=reward,
            rationale=f"one incremental trip above baseline {baseline} "
            f"(overdue_ratio={features.overdue_ratio})",
        )
    category = high_margin_pick(planner_input) if goal.proxy == "add_category" else None
    return PlannedChallenge(
        role="hero",
        insight_ref=hero_insight.name,
        challenge_type="collection" if category is not None else "basket",
        category=category,
        target=clamp_target(0, 2),
        reward=reward,
        rationale=f"grow basket_value (basket_index={features.basket_index}) "
        f"by {'adding ' + category if category else 'a bigger basket'}",
    )


def _high_margin_side(
    planner_input: PlannerInput, posture: Posture
) -> tuple[NamedInsight, PlannedChallenge]:
    category = high_margin_pick(planner_input)
    margin = config.CATEGORY_CONTRIBUTION_MARGIN.get(category, config.CONTRIBUTION_MARGIN)
    insight = NamedInsight(
        name=f"{category}_high_margin",
        kind="high_margin_push",
        behaviour=f"{category} is a high-margin category (margin {margin})",
        dod=f"tries {category} to lift store margin per trip",
        strategy_hint=f"collection on {category}, XP-led side quest",
        evidence_metric=f"contribution_margin={margin}",
    )
    points: PointsLevel = "low" if posture == "deal_driven" else "none"
    challenge = PlannedChallenge(
        role="side",
        insight_ref=insight.name,
        challenge_type="collection",
        category=category,
        target=1,
        reward=ChallengeReward(xp_level="low", points_level=points),
        rationale=f"high-margin {category} (margin {margin}) to earn more per trip, XP-led",
    )
    return insight, challenge
