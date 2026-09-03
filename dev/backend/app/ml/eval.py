import asyncio
from collections.abc import Iterable

from app.ml import catalog as catalog_module
from app.ml import config, history, insight, planner, profiles, user_sim
from app.ml.llm_client import QwenClient
from app.ml.schemas import (
    Branch,
    BranchAggregate,
    BranchOutcome,
    ChallengeOffer,
    EvalReport,
    PlannerInput,
    PlanSource,
    ProfileEvalResult,
    ShopVisit,
    SkuCatalogItem,
    UserProfile,
    ValidatedPlan,
)

_CONTROL_CASHBACK_RATE = 0.10
_MAX_CONCURRENCY = 8


class EvalSettings:
    def __init__(
        self,
        seed: int,
        profile_count: int,
        horizon_weeks: int,
        cut_week: int,
        model: str,
        null_test: bool,
    ) -> None:
        self.seed = seed
        self.profile_count = profile_count
        self.horizon_weeks = horizon_weeks
        self.cut_week = cut_week
        self.model = model
        self.null_test = null_test


async def run_eval(client: QwenClient | None, settings: EvalSettings) -> EvalReport:
    catalog = catalog_module.build_catalog(settings.seed)
    eligible = catalog_module.eligible_catalog(catalog)
    people = profiles.build_profiles(settings.seed, settings.profile_count)
    semaphore = asyncio.Semaphore(_MAX_CONCURRENCY)

    async def _guarded(profile: UserProfile) -> ProfileEvalResult:
        async with semaphore:
            return await _evaluate_profile(client, profile, eligible, settings)

    results = await asyncio.gather(*[_guarded(profile) for profile in people])
    aggregates = _aggregate(results)
    uplift = _business_metric_uplift(aggregates)
    return EvalReport(
        seed=settings.seed,
        profiles=settings.profile_count,
        horizon_weeks=settings.horizon_weeks,
        cut_week=settings.cut_week,
        model=settings.model,
        null_test=settings.null_test,
        business_metric_purchases=config.BUSINESS_METRIC_PURCHASES,
        business_metric_window_weeks=config.BUSINESS_METRIC_WINDOW_WEEKS,
        aggregates=aggregates,
        business_metric_uplift_pp=uplift,
        results=list(results),
    )


async def _evaluate_profile(
    client: QwenClient | None,
    profile: UserProfile,
    eligible: list[SkuCatalogItem],
    settings: EvalSettings,
) -> ProfileEvalResult:
    full = history.simulate_history(profile, settings.seed, settings.horizon_weeks)
    past = history.slice_history(full, settings.cut_week)
    baseline_tail = history.tail_visits(full, settings.cut_week)
    planner_input = insight.build_insight(profile, past, eligible, [])
    tail_weeks = settings.horizon_weeks - settings.cut_week

    llm_plan = await planner.plan_challenge(client, planner_input)
    rules_plan = _rules_only_plan(planner_input)

    branches: dict[str, BranchOutcome] = {}
    branches["control_x5"] = await _control_branch(
        client, profile, planner_input, baseline_tail, tail_weeks, settings
    )
    branches["treatment_llm"] = await _treatment_branch(
        client,
        profile,
        planner_input,
        llm_plan,
        "treatment_llm",
        baseline_tail,
        tail_weeks,
        settings,
    )
    branches["treatment_rules"] = await _treatment_branch(
        client,
        profile,
        planner_input,
        rules_plan,
        "treatment_rules",
        baseline_tail,
        tail_weeks,
        settings,
    )
    return ProfileEvalResult(
        profile_id=profile.profile_id,
        segment=profile.segment,
        persona_label=profile.persona_label,
        churn_risk=planner_input.features.churn_risk,
        branches=branches,
    )


def _rules_only_plan(planner_input: PlannerInput) -> ValidatedPlan:
    return planner._fallback(planner_input)


async def _control_branch(
    client: QwenClient | None,
    profile: UserProfile,
    planner_input: PlannerInput,
    baseline_tail: list[ShopVisit],
    tail_weeks: int,
    settings: EvalSettings,
) -> BranchOutcome:
    response = await user_sim.offer_response(
        client,
        profile,
        planner_input,
        user_sim.CONTROL_OFFER_SUMMARY,
        tail_weeks,
        len(baseline_tail),
        settings.null_test,
    )
    incremental_visits = response.extra_visits if response.engaged else 0
    incremental_revenue = incremental_visits * profile.avg_basket
    reward_cost = round(_CONTROL_CASHBACK_RATE * incremental_revenue, 2)
    return _build_outcome(
        branch="control_x5",
        plan_source="rules",
        profile=profile,
        planner_input=planner_input,
        baseline_tail=baseline_tail,
        settings=settings,
        incremental_visits=incremental_visits,
        reward_cost=reward_cost,
        infra_cost=0.0,
        completed=response.completed_challenge and response.engaged,
        relevance_hit=False,
    )


async def _treatment_branch(
    client: QwenClient | None,
    profile: UserProfile,
    planner_input: PlannerInput,
    validated: ValidatedPlan,
    branch: Branch,
    baseline_tail: list[ShopVisit],
    tail_weeks: int,
    settings: EvalSettings,
) -> BranchOutcome:
    offer = validated.offers[0]
    response = await user_sim.offer_response(
        client,
        profile,
        planner_input,
        user_sim.offer_summary_for(offer),
        tail_weeks,
        len(baseline_tail),
        settings.null_test,
    )
    incremental_visits = response.extra_visits if response.engaged else 0
    completed = response.completed_challenge and response.engaged
    reward_cost = offer.reward.reward_cost_rub if completed else 0.0
    return _build_outcome(
        branch=branch,
        plan_source=validated.plan_source,
        profile=profile,
        planner_input=planner_input,
        baseline_tail=baseline_tail,
        settings=settings,
        incremental_visits=incremental_visits,
        reward_cost=reward_cost,
        infra_cost=config.INFRA_COST_PER_USER_MONTH_RUB,
        completed=completed,
        relevance_hit=_is_relevant(offer, planner_input),
    )


def _build_outcome(
    branch: Branch,
    plan_source: PlanSource,
    profile: UserProfile,
    planner_input: PlannerInput,
    baseline_tail: list[ShopVisit],
    settings: EvalSettings,
    incremental_visits: int,
    reward_cost: float,
    infra_cost: float,
    completed: bool,
    relevance_hit: bool,
) -> BranchOutcome:
    incremental_revenue = round(incremental_visits * profile.avg_basket, 2)
    incremental_margin = round(incremental_revenue * config.CONTRIBUTION_MARGIN, 2)
    net_effect = round(incremental_margin - reward_cost - infra_cost, 2)
    baseline_window = _visits_in_window(baseline_tail, settings.cut_week)
    purchases_in_window = baseline_window + incremental_visits
    reached = purchases_in_window >= config.BUSINESS_METRIC_PURCHASES
    return BranchOutcome(
        branch=branch,
        plan_source=plan_source,
        baseline_tail_visits=len(baseline_tail),
        tail_visits=len(baseline_tail) + incremental_visits,
        incremental_visits=incremental_visits,
        incremental_revenue_rub=incremental_revenue,
        incremental_margin_rub=incremental_margin,
        reward_cost_rub=round(reward_cost, 2),
        infra_cost_rub=infra_cost,
        net_effect_rub=net_effect,
        purchases_in_window=purchases_in_window,
        reached_business_metric=reached,
        completed_challenge=completed,
        relevance_hit=relevance_hit,
    )


def _visits_in_window(tail: list[ShopVisit], cut_week: int) -> int:
    start = cut_week * 7
    end = start + config.BUSINESS_METRIC_WINDOW_WEEKS * 7
    return sum(1 for visit in tail if start <= visit.day_index < end)


def _is_relevant(offer: ChallengeOffer, planner_input: PlannerInput) -> bool:
    if offer.challenge_type == "frequency" and planner_input.features.churn_risk != "none":
        return True
    if offer.category is None:
        return False
    for series in planner_input.category_timeseries:
        if series.category == offer.category and (series.days_overdue > 0 or series.share >= 0.10):
            return True
    return False


def _aggregate(results: list[ProfileEvalResult]) -> dict[str, BranchAggregate]:
    branch_names: tuple[Branch, ...] = ("control_x5", "treatment_llm", "treatment_rules")
    aggregates: dict[str, BranchAggregate] = {}
    total = len(results) or 1
    for name in branch_names:
        outcomes = [result.branches[name] for result in results]
        aggregates[name] = BranchAggregate(
            branch=name,
            profiles=len(outcomes),
            avg_incremental_visits=round(_mean(o.incremental_visits for o in outcomes), 3),
            avg_incremental_margin_rub=round(_mean(o.incremental_margin_rub for o in outcomes), 2),
            avg_reward_cost_rub=round(_mean(o.reward_cost_rub for o in outcomes), 2),
            avg_net_effect_rub=round(_mean(o.net_effect_rub for o in outcomes), 2),
            business_metric_share=round(
                sum(o.reached_business_metric for o in outcomes) / total, 4
            ),
            completion_rate=round(sum(o.completed_challenge for o in outcomes) / total, 4),
            relevance_hit_rate=round(sum(o.relevance_hit for o in outcomes) / total, 4),
            plan_source_llm_share=round(sum(o.plan_source == "llm" for o in outcomes) / total, 4),
        )
    return aggregates


def _business_metric_uplift(aggregates: dict[str, BranchAggregate]) -> float:
    treatment = aggregates["treatment_llm"].business_metric_share
    control = aggregates["control_x5"].business_metric_share
    return round((treatment - control) * 100, 2)


def _mean(values: Iterable[float]) -> float:
    collected = list(values)
    return sum(collected) / len(collected) if collected else 0.0
