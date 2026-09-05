import asyncio

import httpx
import pytest

from app.ml import config, tool_schemas, tracing, user_sim
from app.ml import profiles as profiles_module
from app.ml.llm_client import ChatClient, ChatResult, LLMConfig
from app.ml.schemas import OfferResponse, PromoDecision
from tests.unit.ml import data


def _response(decision: PromoDecision) -> OfferResponse:
    return OfferResponse(
        thinking="t",
        promo_decision=decision,
        extra_visits=2,
        completed_challenge=True,
        rationale="r",
    )


def test_engaged_is_true_only_for_use_offer() -> None:
    assert _response("use_offer").engaged is True
    assert _response("buy_as_usual").engaged is False
    assert _response("ignore").engaged is False


def test_offer_response_schema_forces_thinking_then_verdict() -> None:
    schema = tool_schemas.offer_response_schema()
    required = schema["required"]
    assert required[0] == "thinking"
    assert "promo_decision" in required and "rationale" in required
    assert schema["properties"]["promo_decision"]["enum"] == [
        "use_offer",
        "buy_as_usual",
        "ignore",
    ]
    assert "engaged" not in schema["properties"]


def test_null_actor_turn_has_no_llm_call() -> None:
    profile = profiles_module.build_profiles(7, 1)[0]
    planner_input = data.sample_planner_input()
    turn = asyncio.run(
        user_sim.offer_response(
            None, profile, planner_input, "offer", 6, 3, True, "actor_control_x5"
        )
    )
    assert turn.call is None
    assert turn.response.promo_decision == "ignore"
    assert turn.response.engaged is False


def test_build_llm_call_records_raw_and_parse_status() -> None:
    raw = '{"promo_decision":"use_offer"}'
    ok = ChatResult(parsed={"promo_decision": "use_offer"}, raw_text=raw)
    call = tracing.build_llm_call(
        role="actor",
        label="actor_control_x5",
        model="deepseek-v4-flash",
        base_url="http://localhost:18017/v1",
        attempt=0,
        system_prompt="sys",
        user_prompt="usr",
        result=ok,
    )
    assert call.parse_ok is True
    assert call.response_text == '{"promo_decision":"use_offer"}'

    broken = ChatResult(parsed=None, raw_text="not json")
    broken_call = tracing.build_llm_call(
        role="actor",
        label="actor_control_x5",
        model="m",
        base_url="b",
        attempt=0,
        system_prompt="s",
        user_prompt="u",
        result=broken,
    )
    assert broken_call.parse_ok is False


def test_real_actor_path_parses_traces_and_renders_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = profiles_module.build_profiles(7, 1)[0]
    planner_input = data.sample_planner_input()
    captured: dict[str, str] = {}

    async def fake_emit_json(
        system_prompt: str,
        user_prompt: str,
        schema_name: str,
        json_schema: dict[str, object],
        temperature: float = 0.0,
        max_tokens: int = 300,
    ) -> ChatResult:
        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt
        return ChatResult(
            parsed={
                "thinking": "dairy is on my regular list and I am due this week",
                "promo_decision": "use_offer",
                "extra_visits": 1,
                "completed_challenge": True,
                "rationale": "relevant and worth one extra trip",
            },
            raw_text='{"promo_decision":"use_offer"}',
        )

    async def run() -> tracing.ActorTurn:
        async with httpx.AsyncClient() as http:
            client = ChatClient(LLMConfig("http://localhost:18017/v1", "deepseek-v4-flash"), http)
            monkeypatch.setattr(client, "emit_json", fake_emit_json)
            return await user_sim.offer_response(
                client, profile, planner_input, "offer", 6, 3, False, "actor_treatment_ai"
            )

    turn = asyncio.run(run())
    assert turn.response.promo_decision == "use_offer"
    assert turn.response.engaged is True
    assert turn.response.extra_visits == 1
    assert turn.call is not None
    assert turn.call.parse_ok is True
    assert turn.call.label == "actor_treatment_ai"
    assert turn.call.model == "deepseek-v4-flash"
    assert profile.deal_attitude in captured["user_prompt"]
    assert profile.favorite_categories[0] in captured["user_prompt"]


def test_real_actor_path_unparsable_falls_back_and_keeps_raw(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = profiles_module.build_profiles(7, 1)[0]
    planner_input = data.sample_planner_input()

    async def fake_emit_json(
        system_prompt: str,
        user_prompt: str,
        schema_name: str,
        json_schema: dict[str, object],
        temperature: float = 0.0,
        max_tokens: int = 300,
    ) -> ChatResult:
        return ChatResult(parsed=None, raw_text="model went off-script")

    async def run() -> tracing.ActorTurn:
        async with httpx.AsyncClient() as http:
            client = ChatClient(LLMConfig("http://localhost:18017/v1", "deepseek-v4-flash"), http)
            monkeypatch.setattr(client, "emit_json", fake_emit_json)
            return await user_sim.offer_response(
                client, profile, planner_input, "offer", 6, 3, False, "actor_treatment_ai"
            )

    turn = asyncio.run(run())
    assert turn.response.promo_decision == "ignore"
    assert turn.response.engaged is False
    assert turn.call is not None
    assert turn.call.parse_ok is False
    assert turn.call.response_text == "model went off-script"


def test_actor_retries_transient_http_failure_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(config, "ACTOR_RETRY_BACKOFF_S", 0.0)
    profile = profiles_module.build_profiles(7, 1)[0]
    planner_input = data.sample_planner_input()
    attempts = {"n": 0}

    async def flaky_emit_json(
        system_prompt: str,
        user_prompt: str,
        schema_name: str,
        json_schema: dict[str, object],
        temperature: float = 0.0,
        max_tokens: int = 300,
    ) -> ChatResult:
        attempts["n"] += 1
        if attempts["n"] <= 2:
            return ChatResult(parsed=None, raw_text=None)
        return ChatResult(
            parsed={
                "thinking": "on-target after the server settled",
                "promo_decision": "use_offer",
                "extra_visits": 1,
                "completed_challenge": True,
                "rationale": "relevant and worth one trip",
            },
            raw_text='{"promo_decision":"use_offer"}',
        )

    async def run() -> tracing.ActorTurn:
        async with httpx.AsyncClient() as http:
            client = ChatClient(LLMConfig("http://localhost:18017/v1", "deepseek-v4-flash"), http)
            monkeypatch.setattr(client, "emit_json", flaky_emit_json)
            return await user_sim.offer_response(
                client, profile, planner_input, "offer", 6, 3, False, "actor_treatment_ai"
            )

    turn = asyncio.run(run())
    assert attempts["n"] == 3
    assert turn.response.promo_decision == "use_offer"
    assert turn.call is not None
    assert turn.call.parse_ok is True
    assert turn.call.attempt == 2


def test_actor_exhausts_retries_and_falls_back_visibly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(config, "ACTOR_RETRY_BACKOFF_S", 0.0)
    profile = profiles_module.build_profiles(7, 1)[0]
    planner_input = data.sample_planner_input()
    attempts = {"n": 0}

    async def always_fail(
        system_prompt: str,
        user_prompt: str,
        schema_name: str,
        json_schema: dict[str, object],
        temperature: float = 0.0,
        max_tokens: int = 300,
    ) -> ChatResult:
        attempts["n"] += 1
        return ChatResult(parsed=None, raw_text=None)

    async def run() -> tracing.ActorTurn:
        async with httpx.AsyncClient() as http:
            client = ChatClient(LLMConfig("http://localhost:18017/v1", "deepseek-v4-flash"), http)
            monkeypatch.setattr(client, "emit_json", always_fail)
            return await user_sim.offer_response(
                client, profile, planner_input, "offer", 6, 3, False, "actor_treatment_ai"
            )

    turn = asyncio.run(run())
    assert attempts["n"] == config.ACTOR_RETRY_MAX + 1
    assert turn.response.promo_decision == "ignore"
    assert turn.call is not None
    assert turn.call.parse_ok is False
    assert turn.call.attempt == config.ACTOR_RETRY_MAX
