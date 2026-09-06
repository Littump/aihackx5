from typing import Any

from pydantic import BaseModel

from app.ml import langfuse_export
from app.ml.langfuse_export import LoadedTraces
from app.ml.schemas import BranchOutcome, EvalReport
from app.ml.tracing import ProfileTrace

_BRANCH_ORDER: tuple[str, ...] = ("control_x5", "treatment_llm", "treatment_rules")


class BranchBusinessSummary(BaseModel):
    branch: str
    profiles: int
    sum_incremental_visits: float
    sum_incremental_revenue_rub: float
    sum_incremental_margin_rub: float
    sum_reward_cost_rub: float
    sum_infra_cost_rub: float
    sum_net_effect_rub: float
    count_reached_business_metric: int
    count_completed_challenge: int
    count_relevance_hit: int
    count_high_margin_hit: int
    business_metric_share: float
    completion_rate: float
    relevance_hit_rate: float


class TechSummary(BaseModel):
    profiles: int
    llm_plan_count: int
    rules_plan_count: int
    llm_plan_share: float
    planner_parse_ok_rate: float
    planner_repair_total: int
    actor_fallback_null_count: int
    actor_branch_count: int


class IterationSummary(BaseModel):
    iteration: str
    seed: int
    profiles: int
    profile_ids: list[str]
    planner_model: str
    actor_model: str
    high_margin_mandate: bool
    business_metric_uplift_pp: float
    branches: list[BranchBusinessSummary]
    tech: TechSummary


def _branch_business(branch: str, outcomes: list[BranchOutcome]) -> BranchBusinessSummary:
    count = len(outcomes)
    reached = sum(1 for outcome in outcomes if outcome.reached_business_metric)
    completed = sum(1 for outcome in outcomes if outcome.completed_challenge)
    relevance = sum(1 for outcome in outcomes if outcome.relevance_hit)
    high_margin = sum(1 for outcome in outcomes if outcome.high_margin_hit)
    return BranchBusinessSummary(
        branch=branch,
        profiles=count,
        sum_incremental_visits=round(sum(o.incremental_visits for o in outcomes), 2),
        sum_incremental_revenue_rub=round(sum(o.incremental_revenue_rub for o in outcomes), 2),
        sum_incremental_margin_rub=round(sum(o.incremental_margin_rub for o in outcomes), 2),
        sum_reward_cost_rub=round(sum(o.reward_cost_rub for o in outcomes), 2),
        sum_infra_cost_rub=round(sum(o.infra_cost_rub for o in outcomes), 2),
        sum_net_effect_rub=round(sum(o.net_effect_rub for o in outcomes), 2),
        count_reached_business_metric=reached,
        count_completed_challenge=completed,
        count_relevance_hit=relevance,
        count_high_margin_hit=high_margin,
        business_metric_share=round(reached / count, 4) if count else 0.0,
        completion_rate=round(completed / count, 4) if count else 0.0,
        relevance_hit_rate=round(relevance / count, 4) if count else 0.0,
    )


def _tech_summary(profiles: list[ProfileTrace]) -> TechSummary:
    llm_plans = sum(1 for profile in profiles if profile.plan_source == "llm")
    rules_plans = sum(1 for profile in profiles if profile.plan_source != "llm")
    parse_ok = 0
    parse_total = 0
    repair_total = 0
    for profile in profiles:
        parse_total += len(profile.planner_calls)
        parse_ok += sum(1 for call in profile.planner_calls if call.parse_ok)
        if profile.plan_source == "llm" and profile.planner_calls:
            repair_total += max(call.attempt for call in profile.planner_calls)
    fallback_null = 0
    branch_count = 0
    for profile in profiles:
        for branch in profile.branches:
            branch_count += 1
            if branch.decision.source == "fallback_null":
                fallback_null += 1
    total = len(profiles)
    return TechSummary(
        profiles=total,
        llm_plan_count=llm_plans,
        rules_plan_count=rules_plans,
        llm_plan_share=round(llm_plans / total, 4) if total else 0.0,
        planner_parse_ok_rate=round(parse_ok / parse_total, 4) if parse_total else 0.0,
        planner_repair_total=repair_total,
        actor_fallback_null_count=fallback_null,
        actor_branch_count=branch_count,
    )


def build_iteration_summary(report: EvalReport, loaded: LoadedTraces) -> IterationSummary:
    header = loaded.header
    branches: list[BranchBusinessSummary] = []
    for branch in _BRANCH_ORDER:
        outcomes = [
            result.branches[branch] for result in report.results if branch in result.branches
        ]
        if outcomes:
            branches.append(_branch_business(branch, outcomes))
    profile_ids = header.profile_ids or [result.profile_id for result in report.results]
    return IterationSummary(
        iteration=header.iteration,
        seed=report.seed,
        profiles=report.profiles,
        profile_ids=profile_ids,
        planner_model=report.planner_model,
        actor_model=report.actor_model,
        high_margin_mandate=report.high_margin_mandate,
        business_metric_uplift_pp=report.business_metric_uplift_pp,
        branches=branches,
        tech=_tech_summary(loaded.profiles),
    )


def iteration_scores(summary: IterationSummary) -> dict[str, float]:
    scores: dict[str, float] = {
        "business_metric_uplift_pp": float(summary.business_metric_uplift_pp),
    }
    for branch in summary.branches:
        suffix = branch.branch
        scores[f"sum_incremental_visits__{suffix}"] = float(branch.sum_incremental_visits)
        scores[f"sum_incremental_margin_rub__{suffix}"] = float(branch.sum_incremental_margin_rub)
        scores[f"sum_reward_cost_rub__{suffix}"] = float(branch.sum_reward_cost_rub)
        scores[f"sum_net_effect_rub__{suffix}"] = float(branch.sum_net_effect_rub)
        scores[f"count_business_metric__{suffix}"] = float(branch.count_reached_business_metric)
        scores[f"business_metric_share__{suffix}"] = float(branch.business_metric_share)
        scores[f"completion_rate__{suffix}"] = float(branch.completion_rate)
        scores[f"relevance_hit_rate__{suffix}"] = float(branch.relevance_hit_rate)
    tech = summary.tech
    scores["tech_llm_plan_share"] = float(tech.llm_plan_share)
    scores["tech_planner_parse_ok_rate"] = float(tech.planner_parse_ok_rate)
    scores["tech_planner_repair_total"] = float(tech.planner_repair_total)
    scores["tech_actor_fallback_null_count"] = float(tech.actor_fallback_null_count)
    return scores


def _summary_tags(summary: IterationSummary) -> list[str]:
    return [
        "eval:summary",
        f"iteration:{summary.iteration}",
        f"seed:{summary.seed}",
    ]


def push_iteration_summary(
    loaded: LoadedTraces,
    summary: IterationSummary,
    public_key: str,
    secret_key: str,
    host: str,
) -> int:
    client = langfuse_export.open_langfuse_client(public_key, secret_key, host)
    fingerprint = langfuse_export.run_fingerprint(loaded)
    trace_id = langfuse_export._stable_trace_id(
        client, langfuse_export.iteration_summary_trace_key(fingerprint, loaded.header)
    )
    scores = iteration_scores(summary)
    name = f"iteration {summary.iteration} summary (seed={summary.seed})"
    metadata: dict[str, Any] = {
        "iteration": summary.iteration,
        "seed": summary.seed,
        "profiles": summary.profiles,
        "profile_ids": summary.profile_ids,
        "planner_model": summary.planner_model,
        "actor_model": summary.actor_model,
        "high_margin_mandate": summary.high_margin_mandate,
    }
    with client.start_as_current_observation(
        name=name,
        as_type="span",
        trace_context={"trace_id": trace_id},
        input={"profiles": summary.profiles, "profile_ids": summary.profile_ids},
        output=summary.model_dump(),
        metadata=metadata,
    ):
        client.update_current_trace(
            name=name,
            user_id="eval-summary",
            tags=_summary_tags(summary),
            metadata=metadata,
        )
    for score_name, value in scores.items():
        client.create_score(
            name=score_name,
            value=value,
            trace_id=trace_id,
            data_type="NUMERIC",
            score_id=f"{trace_id}-{score_name}",
        )
    client.flush()
    return len(scores)
