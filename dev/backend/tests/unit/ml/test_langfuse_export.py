import importlib.util
from pathlib import Path

import pytest

from app.ml import langfuse_export
from app.ml.tracing import (
    ActorDecision,
    BranchTrace,
    EvalRunHeader,
    LlmCall,
    ProfileSnapshot,
    ProfileTrace,
)


def _header() -> EvalRunHeader:
    return EvalRunHeader(
        seed=7,
        profiles=1,
        horizon_weeks=12,
        cut_week=6,
        planner_model="qwen",
        actor_model="deepseek",
        null_test=False,
        no_llm=False,
    )


def _profile() -> ProfileTrace:
    snapshot = ProfileSnapshot(
        profile_id="P0001",
        segment="regular_mid",
        persona_label="родитель",
        archetype="человек привычки",
        deal_attitude="promo_skeptic",
        routine_rigidity=0.7,
        visits_per_week=1.4,
        avg_basket=590.0,
        promo_sensitivity=0.3,
        favorite_categories=["dairy", "bakery", "grocery"],
        churn_risk="elevated",
    )
    decision = ActorDecision(
        promo_decision="use_offer",
        engaged=True,
        extra_visits=1,
        completed_challenge=True,
        thinking="dairy is overdue, worth one trip",
        rationale="on-target and cheap effort",
        source="actor_llm",
    )
    call = LlmCall(
        role="actor",
        label="actor_treatment_llm",
        model="deepseek",
        base_url="http://localhost:18017/v1",
        attempt=0,
        system_prompt="sys",
        user_prompt="usr",
        response_text='{"promo_decision":"use_offer"}',
        parsed={"promo_decision": "use_offer"},
        parse_ok=True,
    )
    branch = BranchTrace(
        branch="treatment_llm",
        offer_summary="dairy replenishment",
        plan_source="llm",
        relevance_hit=True,
        decision=decision,
        incremental_visits=1,
        reward_cost_rub=7.0,
        net_effect_rub=60.0,
        llm_call=call,
    )
    return ProfileTrace(snapshot=snapshot, plan_source="llm", planner_calls=[], branches=[branch])


def test_generations_expose_promo_decision_and_rationale() -> None:
    generations = langfuse_export.to_langfuse_generations(_header(), _profile())
    assert len(generations) == 1
    generation = generations[0]
    assert generation.trace_id == "eval-7-P0001"
    assert generation.metadata["promo_decision"] == "use_offer"
    assert generation.metadata["rationale"] == "on-target and cheap effort"
    assert generation.metadata["decision_source"] == "actor_llm"
    assert generation.output["parsed"] == {"promo_decision": "use_offer"}


def test_write_generations_json(tmp_path: Path) -> None:
    loaded = langfuse_export.LoadedTraces(header=_header(), profiles=[_profile()])
    out = tmp_path / "gen.json"
    count = langfuse_export.write_generations_json(loaded, out)
    assert count == 1
    assert out.exists()


def test_push_without_sdk_raises_helpful_error() -> None:
    if importlib.util.find_spec("langfuse") is not None:
        pytest.skip("langfuse SDK installed; offline error path not applicable")
    loaded = langfuse_export.LoadedTraces(header=_header(), profiles=[_profile()])
    with pytest.raises(RuntimeError, match="langfuse SDK is not installed"):
        langfuse_export.push_to_langfuse(loaded, "pk", "sk", "http://localhost:3000")
