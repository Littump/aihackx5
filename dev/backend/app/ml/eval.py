import asyncio
from collections.abc import Iterable
from typing import Literal

from app.ml import app_view, config, history, insight, planner, profiles, tracing, user_sim
from app.ml import catalog as catalog_module
from app.ml import persona as persona_module
from app.ml.llm_client import ChatClient
from app.ml.schemas import (
    Branch,
    BranchAggregate,
    BranchOutcome,
    ChallengeOffer,
    EvalReport,
    PlannerInput,
    PlanSource,
    PreviousPlan,
    ProfileEvalResult,
    PurchaseHistory,
    ShoppingHabit,
    ShopVisit,
    SkuCatalogItem,
    UserProfile,
    ValidatedPlan,
)
from app.ml.tracing import (
    ActorDecision,
    BranchTrace,
    LlmCall,
    ProfileTrace,
    TraceRecorder,
    WeekTrace,
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
        iteration: str = "adhoc",
        profile_ids: list[str] | None = None,
    ) -> None:
        self.seed = seed
        self.profile_count = profile_count
        self.horizon_weeks = horizon_weeks
        self.cut_week = cut_week
        self.planner_model = planner_model
        self.actor_model = actor_model
        self.null_test = null_test
        self.max_concurrency = max_concurrency
        self.iteration = iteration
        self.profile_ids = profile_ids


def _select_profiles(settings: "EvalSettings") -> list[UserProfile]:
    people = profiles.build_profiles(settings.seed, settings.profile_count)
    if not settings.profile_ids:
        return people
    by_id = {profile.profile_id: profile for profile in people}
    missing = [pid for pid in settings.profile_ids if pid not in by_id]
    if missing:
        raise ValueError(f"profile_ids not in generated set: {', '.join(missing)}")
    return [by_id[pid] for pid in settings.profile_ids]


async def run_eval(
    clients: EvalClients | None,
    settings: EvalSettings,
    recorder: TraceRecorder | None = None,
    personas: dict[str, persona_module.Persona] | None = None,
) -> EvalReport:
    catalog = catalog_module.build_catalog(settings.seed)
    eligible = catalog_module.eligible_catalog(catalog)
    people = _select_profiles(settings)
    semaphore = asyncio.Semaphore(settings.max_concurrency)

    async def _guarded(profile: UserProfile) -> ProfileEvalResult:
        async with semaphore:
            return await _evaluate_profile(clients, profile, eligible, settings, recorder, personas)

    results = await asyncio.gather(*[_guarded(profile) for profile in people])
    aggregates = _aggregate(results)
    uplift = _business_metric_uplift(aggregates)
    return EvalReport(
        seed=settings.seed,
        profiles=len(people),
        horizon_weeks=settings.horizon_weeks,
        cut_week=settings.cut_week,
        planner_model=settings.planner_model,
        actor_model=settings.actor_model,
        null_test=settings.null_test,
        high_margin_mandate=config.HIGH_MARGIN_MANDATE_ENABLED,
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
    personas: dict[str, persona_module.Persona] | None = None,
) -> ProfileEvalResult:
    shopper_persona = (personas or {}).get(profile.profile_id) or (
        persona_module.build_fallback_persona(profile)
    )
    full = history.simulate_history(profile, settings.seed, settings.horizon_weeks)
    t_input = insight.build_insight(
        profile, history.slice_history(full, settings.cut_week), eligible, []
    )
    observed_habits = insight.shopping_habits(
        t_input.category_timeseries, profile.favorite_categories
    )
    tail_weeks = settings.horizon_weeks - settings.cut_week

    planner_client = clients.planner if clients is not None else None
    actor_client = clients.actor if clients is not None else None
    planner_calls: list[LlmCall] = []

    control_outcome, control_trace = await _control_branch(
        actor_client, profile, full, tail_weeks, settings, shopper_persona, observed_habits
    )
    llm_outcome, llm_trace = await _treatment_branch(
        actor_client,
        planner_client,
        profile,
        full,
        eligible,
        tail_weeks,
        settings,
        "treatment_llm",
        True,
        shopper_persona,
        observed_habits,
        planner_calls,
    )
    rules_outcome, rules_trace = await _treatment_branch(
        actor_client,
        planner_client,
        profile,
        full,
        eligible,
        tail_weeks,
        settings,
        "treatment_rules",
        False,
        shopper_persona,
        observed_habits,
        None,
    )
    branches: dict[str, BranchOutcome] = {
        "control_x5": control_outcome,
        "treatment_llm": llm_outcome,
        "treatment_rules": rules_outcome,
    }
    if recorder is not None:
        recorder.add_profile(
            ProfileTrace(
                snapshot=tracing.profile_snapshot(
                    profile,
                    t_input.features.churn_risk,
                    shopper_persona,
                    observed_habits,
                ),
                plan_source=llm_outcome.plan_source,
                planner_calls=planner_calls,
                branches=[control_trace, llm_trace, rules_trace],
            )
        )
    return ProfileEvalResult(
        profile_id=profile.profile_id,
        segment=profile.segment,
        persona_label=profile.persona_label,
        churn_risk=t_input.features.churn_risk,
        branches=branches,
    )


def _rules_only_plan(planner_input: PlannerInput) -> ValidatedPlan:
    return planner._fallback(planner_input)


async def _control_branch(
    actor_client: ChatClient | None,
    profile: UserProfile,
    full: PurchaseHistory,
    tail_weeks: int,
    settings: EvalSettings,
    shopper_persona: persona_module.Persona,
    observed_habits: list[ShoppingHabit],
) -> tuple[BranchOutcome, BranchTrace]:
    baseline_tail = history.tail_visits(full, settings.cut_week)
    weekly_baseline = _weekly_baseline(baseline_tail, settings.cut_week, tail_weeks)
    chat = user_sim.WeeklyChat(
        actor_client,
        profile,
        shopper_persona,
        observed_habits,
        settings.null_test,
        "actor_control_x5",
    )
    incremental = 0
    incremental_in_window = 0
    completed_any = False
    cumulative = 0
    weeks: list[WeekTrace] = []
    first_decision: ActorDecision | None = None
    first_call: LlmCall | None = None
    for offset in range(tail_weeks):
        week_index = settings.cut_week + offset
        base = weekly_baseline[offset]
        turn = await chat.respond(offset + 1, user_sim.CONTROL_OFFER_SUMMARY, True, True)
        extra = turn.response.extra_visits if turn.response.engaged else 0
        completed = turn.response.completed_challenge and turn.response.engaged
        incremental += extra
        if offset < config.BUSINESS_METRIC_WINDOW_WEEKS:
            incremental_in_window += extra
        completed_any = completed_any or completed
        cumulative += base + extra
        source = "null" if turn.call is None else "actor_control_x5"
        decision = tracing.actor_decision(turn.response, source)
        weeks.append(
            WeekTrace(
                week_index=week_index,
                challenge_active=True,
                baseline_visits=base,
                extra_visits=extra,
                cumulative_visits=cumulative,
                decision=decision,
                llm_call=turn.call,
            )
        )
        if first_decision is None:
            first_decision = decision
            first_call = turn.call
    assert first_decision is not None
    reward_cost = round(_CONTROL_CASHBACK_RATE * incremental * profile.avg_basket, 2)
    outcome = _build_outcome(
        branch="control_x5",
        plan_source="rules",
        profile=profile,
        baseline_tail=baseline_tail,
        settings=settings,
        incremental_visits=incremental,
        incremental_in_window=incremental_in_window,
        reward_cost=reward_cost,
        infra_cost=0.0,
        completed=completed_any,
        relevance_hit=False,
        high_margin_hit=False,
    )
    trace = BranchTrace(
        branch="control_x5",
        offer_summary=user_sim.CONTROL_OFFER_SUMMARY,
        plan_source="rules",
        relevance_hit=False,
        decision=first_decision,
        incremental_visits=incremental,
        reward_cost_rub=outcome.reward_cost_rub,
        net_effect_rub=outcome.net_effect_rub,
        llm_call=first_call,
        weeks=weeks,
    )
    return outcome, trace


async def _treatment_branch(
    actor_client: ChatClient | None,
    planner_client: ChatClient | None,
    profile: UserProfile,
    full: PurchaseHistory,
    eligible: list[SkuCatalogItem],
    tail_weeks: int,
    settings: EvalSettings,
    branch: Branch,
    use_llm: bool,
    shopper_persona: persona_module.Persona,
    observed_habits: list[ShoppingHabit],
    planner_calls: list[LlmCall] | None,
) -> tuple[BranchOutcome, BranchTrace]:
    baseline_tail = history.tail_visits(full, settings.cut_week)
    weekly_baseline = _weekly_baseline(baseline_tail, settings.cut_week, tail_weeks)
    chat = user_sim.WeeklyChat(
        actor_client,
        profile,
        shopper_persona,
        observed_habits,
        settings.null_test,
        f"actor_{branch}",
    )
    previous_plans: list[PreviousPlan] = []
    incremental = 0
    incremental_in_window = 0
    reward_cost = 0.0
    completed_any = False
    any_llm = False
    any_relevant = False
    any_high_margin = False
    cumulative = 0
    weeks: list[WeekTrace] = []
    first_decision: ActorDecision | None = None
    first_call: LlmCall | None = None
    first_offer_summary = ""
    for offset in range(tail_weeks):
        week_index = settings.cut_week + offset
        past = history.slice_history(full, week_index)
        planner_input = insight.build_insight(profile, past, eligible, previous_plans)
        if use_llm:
            plan = await planner.plan_challenge(planner_client, planner_input, planner_calls)
        else:
            plan = _rules_only_plan(planner_input)
        offer = plan.offers[0]
        offer_view = app_view.render_app_view(plan, profile.level)
        if offset == 0:
            first_offer_summary = offer_view
        relevant = _is_relevant(offer, planner_input)
        high_margin = any(config.is_high_margin(candidate.category) for candidate in plan.offers)
        base = weekly_baseline[offset]
        turn = await chat.respond(offset + 1, offer_view, False, True)
        engaged = turn.response.engaged
        extra = turn.response.extra_visits if engaged else 0
        completed = turn.response.completed_challenge and engaged
        incremental += extra
        if offset < config.BUSINESS_METRIC_WINDOW_WEEKS:
            incremental_in_window += extra
        if completed:
            reward_cost += offer.reward.reward_cost_rub
        completed_any = completed_any or completed
        any_llm = any_llm or plan.plan_source == "llm"
        any_relevant = any_relevant or relevant
        any_high_margin = any_high_margin or high_margin
        cumulative += base + extra
        source = "null" if turn.call is None else f"actor_{branch}"
        decision = tracing.actor_decision(turn.response, source)
        weeks.append(
            WeekTrace(
                week_index=week_index,
                challenge_active=True,
                baseline_visits=base,
                extra_visits=extra,
                cumulative_visits=cumulative,
                decision=decision,
                llm_call=turn.call,
            )
        )
        if first_decision is None:
            first_decision = decision
            first_call = turn.call
        previous_plans.append(_as_previous_plan(offset + 1, offer, engaged, completed))
    assert first_decision is not None
    plan_source: PlanSource = "llm" if any_llm else "rules"
    outcome = _build_outcome(
        branch=branch,
        plan_source=plan_source,
        profile=profile,
        baseline_tail=baseline_tail,
        settings=settings,
        incremental_visits=incremental,
        incremental_in_window=incremental_in_window,
        reward_cost=reward_cost,
        infra_cost=config.INFRA_COST_PER_USER_MONTH_RUB,
        completed=completed_any,
        relevance_hit=any_relevant,
        high_margin_hit=any_high_margin,
    )
    trace = BranchTrace(
        branch=branch,
        offer_summary=first_offer_summary,
        plan_source=plan_source,
        relevance_hit=any_relevant,
        decision=first_decision,
        incremental_visits=incremental,
        reward_cost_rub=outcome.reward_cost_rub,
        net_effect_rub=outcome.net_effect_rub,
        llm_call=first_call,
        weeks=weeks,
    )
    return outcome, trace


def _as_previous_plan(
    week: int, offer: ChallengeOffer, used: bool, completed: bool
) -> PreviousPlan:
    status: Literal["completed", "expired"] = "completed" if completed else "expired"
    return PreviousPlan(
        week=week,
        challenge_type=offer.challenge_type,
        xp_level=offer.reward.xp_level,
        points_level=offer.reward.points_level,
        status=status,
        used=used,
    )


def _weekly_baseline(baseline_tail: list[ShopVisit], cut_week: int, tail_weeks: int) -> list[int]:
    counts = [0] * tail_weeks
    for visit in baseline_tail:
        week = visit.day_index // 7 - cut_week
        if 0 <= week < tail_weeks:
            counts[week] += 1
    return counts


def _build_outcome(
    branch: Branch,
    plan_source: PlanSource,
    profile: UserProfile,
    baseline_tail: list[ShopVisit],
    settings: EvalSettings,
    incremental_visits: int,
    incremental_in_window: int,
    reward_cost: float,
    infra_cost: float,
    completed: bool,
    relevance_hit: bool,
    high_margin_hit: bool,
) -> BranchOutcome:
    incremental_revenue = round(incremental_visits * profile.avg_basket, 2)
    incremental_margin = round(incremental_revenue * config.CONTRIBUTION_MARGIN, 2)
    net_effect = round(incremental_margin - reward_cost - infra_cost, 2)
    baseline_window = _visits_in_window(baseline_tail, settings.cut_week)
    purchases_in_window = baseline_window + incremental_in_window
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
        high_margin_hit=high_margin_hit,
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
            high_margin_share=round(sum(o.high_margin_hit for o in outcomes) / total, 4),
        )
    return aggregates


def _business_metric_uplift(aggregates: dict[str, BranchAggregate]) -> float:
    treatment = aggregates["treatment_llm"].business_metric_share
    control = aggregates["control_x5"].business_metric_share
    return round((treatment - control) * 100, 2)


def _mean(values: Iterable[float]) -> float:
    collected = list(values)
    return sum(collected) / len(collected) if collected else 0.0
