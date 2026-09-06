import asyncio
from typing import Any

import httpx

from app.ml import eval as eval_module
from app.ml.llm_client import ChatClient, ChatResult, LLMConfig
from app.ml.tracing import EvalRunHeader, TraceRecorder

_ENGAGE = {
    "thinking": "this offer fits my week, worth one extra trip",
    "promo_decision": "use_offer",
    "extra_visits": 1,
    "completed_challenge": True,
    "rationale": "relevant and cheap enough to bother",
}


def _settings() -> eval_module.EvalSettings:
    return eval_module.EvalSettings(
        seed=7,
        profile_count=1,
        horizon_weeks=12,
        cut_week=6,
        planner_model="test",
        actor_model="test",
        null_test=False,
    )


def _recorder(settings: eval_module.EvalSettings) -> TraceRecorder:
    return TraceRecorder(
        EvalRunHeader(
            seed=settings.seed,
            profiles=settings.profile_count,
            horizon_weeks=settings.horizon_weeks,
            cut_week=settings.cut_week,
            planner_model=settings.planner_model,
            actor_model=settings.actor_model,
            null_test=False,
            no_llm=False,
        )
    )


async def _fake_engage(
    messages: list[dict[str, str]],
    schema_name: str,
    json_schema: dict[str, Any],
    temperature: float = 0.0,
    max_tokens: int = 300,
    top_p: float | None = None,
    enable_thinking: bool = False,
) -> ChatResult:
    return ChatResult(parsed=dict(_ENGAGE), raw_text='{"promo_decision":"use_offer"}')


def test_treatment_offers_every_tail_week_and_accumulates() -> None:
    settings = _settings()
    recorder = _recorder(settings)
    tail_weeks = settings.horizon_weeks - settings.cut_week

    async def run() -> eval_module.EvalReport:
        async with httpx.AsyncClient() as http:
            actor = ChatClient(LLMConfig("http://actor.test", "actor-test"), http)
            actor.emit_json_messages = _fake_engage  # type: ignore[method-assign]
            clients = eval_module.EvalClients(planner=None, actor=actor)
            return await eval_module.run_eval(clients, settings, recorder)

    report = asyncio.run(run())
    branch = report.results[0].branches["treatment_llm"]
    assert branch.incremental_visits == tail_weeks

    profile_trace = recorder.profiles()[0]
    llm_branch = next(b for b in profile_trace.branches if b.branch == "treatment_llm")
    assert len(llm_branch.weeks) == tail_weeks
    assert all(week.challenge_active for week in llm_branch.weeks)
