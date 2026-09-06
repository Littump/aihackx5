from typing import Any

from app.ml import iteration_summary
from app.ml.schemas import Branch, BranchOutcome, EvalReport, ProfileEvalResult
from app.ml.tracing import (
    ActorDecision,
    BranchTrace,
    EvalRunHeader,
    LlmCall,
    ProfileSnapshot,
    ProfileTrace,
)

_BRANCHES = ("control_x5", "treatment_llm", "treatment_rules")


def _outcome(branch: str, plan_source: str, **kw: Any) -> BranchOutcome:
    base: dict[str, Any] = dict(
        baseline_tail_visits=0,
        tail_visits=0,
        incremental_visits=0,
        incremental_revenue_rub=0.0,
        incremental_margin_rub=0.0,
        reward_cost_rub=0.0,
        infra_cost_rub=1.5,
        net_effect_rub=0.0,
        purchases_in_window=0,
        reached_business_metric=False,
        completed_challenge=False,
        relevance_hit=False,
        high_margin_hit=False,
    )
    base.update(kw)
    return BranchOutcome(branch=branch, plan_source=plan_source, **base)  # type: ignore[arg-type]


def _result(pid: str, plan_source: str, llm_kw: dict, rules_kw: dict) -> ProfileEvalResult:
    return ProfileEvalResult(
        profile_id=pid,
        segment="regular_mid",
        persona_label="x",
        churn_risk="none",
        branches={
            "control_x5": _outcome("control_x5", "rules"),
            "treatment_llm": _outcome("treatment_llm", plan_source, **llm_kw),
            "treatment_rules": _outcome("treatment_rules", "rules", **rules_kw),
        },
    )


def _report() -> EvalReport:
    results = [
        _result(
            "P0000",
            "llm",
            dict(
                incremental_visits=2,
                incremental_revenue_rub=1200.0,
                incremental_margin_rub=300.0,
                reward_cost_rub=50.0,
                net_effect_rub=248.5,
                purchases_in_window=9,
                reached_business_metric=True,
                completed_challenge=True,
                relevance_hit=True,
            ),
            dict(incremental_visits=1, net_effect_rub=100.0),
        ),
        _result(
            "P0001",
            "rules",
            dict(
                incremental_visits=1,
                incremental_revenue_rub=600.0,
                incremental_margin_rub=150.0,
                reward_cost_rub=30.0,
                net_effect_rub=118.5,
                purchases_in_window=7,
                high_margin_hit=True,
            ),
            dict(incremental_visits=0, net_effect_rub=-3.0),
        ),
    ]
    return EvalReport(
        seed=7,
        profiles=2,
        horizon_weeks=12,
        cut_week=6,
        planner_model="qwen",
        actor_model="minimax",
        null_test=False,
        high_margin_mandate=True,
        business_metric_purchases=8,
        business_metric_window_weeks=4,
        aggregates={},
        business_metric_uplift_pp=25.0,
        results=results,
    )


def _decision(source: str) -> ActorDecision:
    return ActorDecision(
        promo_decision="use_offer",
        engaged=True,
        extra_visits=1,
        completed_challenge=True,
        thinking="t",
        rationale="r",
        source=source,
    )


def _call(parse_ok: bool, attempt: int) -> LlmCall:
    return LlmCall(
        role="planner",
        label=f"planner_attempt_{attempt}",
        model="qwen",
        base_url="http://x/v1",
        attempt=attempt,
        system_prompt="s",
        user_prompt="u",
        response_text="{}",
        parsed={} if parse_ok else None,
        parse_ok=parse_ok,
    )


def _snapshot(pid: str) -> ProfileSnapshot:
    return ProfileSnapshot(
        profile_id=pid,
        segment="regular_mid",
        persona_label="x",
        persona_brief="b",
        archetype="a",
        deal_attitude="promo_skeptic",
        routine_rigidity=0.5,
        visits_per_week=1.5,
        avg_basket=600.0,
        promo_sensitivity=0.3,
        favorite_categories=["dairy"],
        churn_risk="none",
    )


def _branch_trace(branch: Branch, plan_source: str, source: str) -> BranchTrace:
    return BranchTrace(
        branch=branch,
        offer_summary="o",
        plan_source=plan_source,
        relevance_hit=True,
        decision=_decision(source),
        incremental_visits=1,
        reward_cost_rub=0.0,
        net_effect_rub=0.0,
        llm_call=None,
    )


def _loaded() -> iteration_summary.LoadedTraces:
    header = EvalRunHeader(
        seed=7,
        profiles=2,
        horizon_weeks=12,
        cut_week=6,
        planner_model="qwen",
        actor_model="minimax",
        null_test=False,
        no_llm=False,
        iteration="iter20",
        profile_ids=["P0000", "P0001"],
    )
    p0 = ProfileTrace(
        snapshot=_snapshot("P0000"),
        plan_source="llm",
        planner_calls=[_call(True, 0)],
        branches=[
            _branch_trace("control_x5", "rules", "actor_llm"),
            _branch_trace("treatment_llm", "llm", "actor_llm"),
            _branch_trace("treatment_rules", "rules", "actor_llm"),
        ],
    )
    p1 = ProfileTrace(
        snapshot=_snapshot("P0001"),
        plan_source="rules",
        planner_calls=[_call(False, 0), _call(False, 1)],
        branches=[
            _branch_trace("control_x5", "rules", "fallback_null"),
            _branch_trace("treatment_llm", "rules", "actor_llm"),
            _branch_trace("treatment_rules", "rules", "actor_llm"),
        ],
    )
    return iteration_summary.LoadedTraces(header=header, profiles=[p0, p1])


def test_business_sums_per_branch() -> None:
    summary = iteration_summary.build_iteration_summary(_report(), _loaded())
    llm = next(b for b in summary.branches if b.branch == "treatment_llm")
    assert llm.sum_incremental_visits == 3.0
    assert llm.sum_net_effect_rub == 367.0
    assert llm.sum_reward_cost_rub == 80.0
    assert llm.sum_incremental_margin_rub == 450.0
    assert llm.count_reached_business_metric == 1
    assert llm.count_completed_challenge == 1
    assert llm.count_relevance_hit == 1
    assert llm.count_high_margin_hit == 1
    assert llm.business_metric_share == 0.5
    assert summary.business_metric_uplift_pp == 25.0
    assert summary.iteration == "iter20"
    assert summary.profile_ids == ["P0000", "P0001"]


def test_tech_metrics() -> None:
    summary = iteration_summary.build_iteration_summary(_report(), _loaded()).tech
    assert summary.llm_plan_count == 1
    assert summary.rules_plan_count == 1
    assert summary.llm_plan_share == 0.5
    assert summary.actor_fallback_null_count == 1
    assert summary.actor_branch_count == 6
    assert round(summary.planner_parse_ok_rate, 4) == round(1 / 3, 4)


def test_iteration_scores_are_flat_numeric() -> None:
    summary = iteration_summary.build_iteration_summary(_report(), _loaded())
    scores = iteration_summary.iteration_scores(summary)
    assert scores["sum_net_effect_rub__treatment_llm"] == 367.0
    assert scores["business_metric_uplift_pp"] == 25.0
    assert scores["tech_llm_plan_share"] == 0.5
    assert scores["tech_actor_fallback_null_count"] == 1.0
    assert all(isinstance(v, float) for v in scores.values())
