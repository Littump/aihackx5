import asyncio
from collections.abc import Iterable

from app.ml import catalog as catalog_module
from app.ml import config, history, insight, planner, profiles, tracing, user_sim
from app.ml.llm_client import ChatClient
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
from app.ml.tracing import (
    ActorTurn,
    BranchTrace,
    LlmCall,
    ProfileTrace,
    TraceRecorder,
)

_CONTROL_CASHBACK_RATE = 0.10


class EvalClients:
    def __init__(self, planner: ChatClient | None, actor: ChatClient | None) -> None:
        self.planner = planner
        self.actor = actor


class EvalSettings:
    def __init__(
        self,
        seed: int,
        profile_count: int,
        horizon_weeks: int,
        cut_week: int,
        planner_model: str,
        actor_model: str,
        null_test: bool,
        max_concurrency: int = config.EVAL_MAX_CONCURRENCY,
    ) -> None:
        self.seed = seed
        self.profile_count = profile_count
        self.horizon_weeks = horizon_weeks
        self.cut_week = cut_week
        self.planner_model = planner_model
        self.actor_model = actor_model
        self.null_test = null_test
        self.max_concurrency = max_concurrency


async def run_eval(
    clients: EvalClients | None,
    settings: EvalSettings,
    recorder: TraceRecorder | None = None,
) -> EvalReport:
    catalog = catalog_module.build_catalog(settings.seed)
    eligible = catalog_module.eligible_catalog(catalog)
    people = profiles.build_profiles(settings.seed, settings.profile_count)
    semaphore = asyncio.Semaphore(settings.max_concurrency)

    async def _guarded(profile: UserProfile) -> ProfileEvalResult:
        async with semaphore:
            return await _evaluate_profile(clients, profile, eligible, settings, recorder)

    results = await asyncio.gather(*[_guarded(profile) for profile in people])
    aggregates = _aggregate(results)
    uplift = _business_metric_uplift(aggregates)
    return EvalReport(
        seed=settings.seed,
        profiles=settings.profile_count,
        horizon_weeks=settings.horizon_weeks,
        cut_week=settings.cut_week,
        planner_model=settings.planner_model,
        actor_model=settings.actor_model,
        null_test=settings.null_test,
        business_metric_purchases=config.BUSINESS_METRIC_PURCHASES,
        business_metric_window_weeks=config.BUSINESS_METRIC_WINDOW_WEEKS,
        aggregates=aggregates,
        business_metric_uplift_pp=uplift,
        results=list(results),
    )


async def _evaluate_profile(
    clients: EvalClients | None,
    profile: UserProfile,
    eligible: list[SkuCatalogItem],
    settings: EvalSettings,
    recorder: TraceRecorder | None = None,
) -> ProfileEvalResult:
    full = history.simulate_history(profile, settings.seed, settings.horizon_weeks)
    past = history.slice_history(full, settings.cut_week)
    baseline_tail = history.tail_visits(full, settings.cut_week)
    planner_input = insight.build_insight(profile, past, eligible, [])
    tail_weeks = settings.horizon_weeks - settings.cut_week

    planner_client = clients.planner if clients is not None else None
    actor_client = clients.actor if clients is not None else None

    planner_calls: list[LlmCall] = []
    llm_plan = await planner.plan_challenge(planner_client, planner_input, planner_calls)
    rules_plan = _rules_only_plan(planner_input)

    control_outcome, control_trace = await _control_branch(
        actor_client, profile, planner_input, baseline_tail, tail_weeks, settings
    )
    llm_outcome, llm_trace = await _treatment_branch(
        actor_client,
        profile,
        planner_input,
        llm_plan,
        "treatment_llm",
        baseline_tail,
        tail_weeks,
        settings,
    )
    rules_outcome, rules_trace = await _treatment_branch(
        actor_client,
        profile,
        planner_input,
        rules_plan,
        "treatment_rules",
        baseline_tail,
        tail_weeks,
        settings,
    )
    branches: dict[str, BranchOutcome] = {
        "control_x5": control_outcome,
        "treatment_llm": llm_outcome,
        "treatment_rules": rules_outcome,
    }
    if recorder is not None:
        recorder.add_profile(
            ProfileTrace(
                snapshot=tracing.profile_snapshot(profile, planner_input.features.churn_risk),
                plan_source=llm_plan.plan_source,
                planner_calls=planner_calls,
                branches=[control_trace, llm_trace, rules_trace],
            )
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
    actor_client: ChatClient | None,
    profile: UserProfile,
    planner_input: PlannerInput,
    baseline_tail: list[ShopVisit],
    tail_weeks: int,
    settings: EvalSettings,
) -> tuple[BranchOutcome, BranchTrace]:
    turn = await user_sim.offer_response(
        actor_client,
        profile,
        planner_input,
        user_sim.CONTROL_OFFER_SUMMARY,
        tail_weeks,
        len(baseline_tail),
        settings.null_test,
        "actor_control_x5",
    )
    response = turn.response
    incremental_visits = response.extra_visits if response.engaged else 0
    incremental_revenue = incremental_visits * profile.avg_basket
    reward_cost = round(_CONTROL_CASHBACK_RATE * incremental_revenue, 2)
    outcome = _build_outcome(
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
    trace = _branch_trace(outcome, turn, user_sim.CONTROL_OFFER_SUMMARY)
    return outcome, trace


async def _treatment_branch(
    actor_client: ChatClient | None,
    profile: UserProfile,
    planner_input: PlannerInput,
    validated: ValidatedPlan,
    branch: Branch,
    baseline_tail: list[ShopVisit],
    tail_weeks: int,
    settings: EvalSettings,
) -> tuple[BranchOutcome, BranchTrace]:
    offer = validated.offers[0]
    offer_summary = user_sim.offer_summary_for(offer)
    turn = await user_sim.offer_response(
        actor_client,
        profile,
        planner_input,
        offer_summary,
        tail_weeks,
        len(baseline_tail),
        settings.null_test,
        f"actor_{branch}",
    )
    response = turn.response
    incremental_visits = response.extra_visits if response.engaged else 0
    completed = response.completed_challenge and response.engaged
    reward_cost = offer.reward.reward_cost_rub if completed else 0.0
    outcome = _build_outcome(
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
    trace = _branch_trace(outcome, turn, offer_summary)
    return outcome, trace


def _branch_trace(outcome: BranchOutcome, turn: ActorTurn, offer_summary: str) -> BranchTrace:
    source = _decision_source(turn)
    return BranchTrace(
        branch=outcome.branch,
        offer_summary=offer_summary,
        plan_source=outcome.plan_source,
        relevance_hit=outcome.relevance_hit,
        decision=tracing.actor_decision(turn.response, source),
        incremental_visits=outcome.incremental_visits,
        reward_cost_rub=outcome.reward_cost_rub,
        net_effect_rub=outcome.net_effect_rub,
        llm_call=turn.call,
    )


def _decision_source(turn: ActorTurn) -> str:
    if turn.call is None:
        return "null"
    return "actor_llm" if turn.call.parse_ok else "fallback_null"


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
