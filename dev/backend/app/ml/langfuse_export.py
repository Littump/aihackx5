import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.ml.tracing import EvalRunHeader, LlmCall, ProfileTrace


class LoadedTraces(BaseModel):
    header: EvalRunHeader
    profiles: list[ProfileTrace]


class LangfuseGeneration(BaseModel):
    trace_id: str
    trace_name: str
    name: str
    model: str
    input: dict[str, Any]
    output: dict[str, Any]
    metadata: dict[str, Any]


def read_trace_file(path: Path) -> LoadedTraces:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"empty trace file: {path}")
    header = EvalRunHeader.model_validate_json(lines[0])
    profiles = [ProfileTrace.model_validate_json(line) for line in lines[1:]]
    return LoadedTraces(header=header, profiles=profiles)


def trace_metadata(header: EvalRunHeader, profile: ProfileTrace) -> dict[str, Any]:
    return {
        "seed": header.seed,
        "null_test": header.null_test,
        "no_llm": header.no_llm,
        "planner_model": header.planner_model,
        "actor_model": header.actor_model,
        "plan_source": profile.plan_source,
        "segment": profile.snapshot.segment,
        "persona_label": profile.snapshot.persona_label,
        "archetype": profile.snapshot.archetype,
        "deal_attitude": profile.snapshot.deal_attitude,
        "churn_risk": profile.snapshot.churn_risk,
    }


def to_langfuse_generations(
    header: EvalRunHeader, profile: ProfileTrace
) -> list[LangfuseGeneration]:
    trace_id = f"eval-{header.seed}-{profile.snapshot.profile_id}"
    trace_name = f"profile {profile.snapshot.profile_id} ({profile.snapshot.segment})"
    generations: list[LangfuseGeneration] = []
    for call in profile.planner_calls:
        generations.append(_call_generation(trace_id, trace_name, call, extra={}))
    for branch in profile.branches:
        extra = {
            "branch": branch.branch,
            "offer_summary": branch.offer_summary,
            "promo_decision": branch.decision.promo_decision,
            "engaged": branch.decision.engaged,
            "extra_visits": branch.decision.extra_visits,
            "completed_challenge": branch.decision.completed_challenge,
            "rationale": branch.decision.rationale,
            "thinking": branch.decision.thinking,
            "decision_source": branch.decision.source,
            "relevance_hit": branch.relevance_hit,
            "incremental_visits": branch.incremental_visits,
            "reward_cost_rub": branch.reward_cost_rub,
            "net_effect_rub": branch.net_effect_rub,
        }
        if branch.llm_call is not None:
            generations.append(_call_generation(trace_id, trace_name, branch.llm_call, extra=extra))
        else:
            generations.append(_decision_generation(trace_id, trace_name, branch.branch, extra))
    return generations


def _call_generation(
    trace_id: str, trace_name: str, call: LlmCall, extra: dict[str, Any]
) -> LangfuseGeneration:
    return LangfuseGeneration(
        trace_id=trace_id,
        trace_name=trace_name,
        name=f"{call.role}:{call.label}",
        model=call.model,
        input={"system": call.system_prompt, "user": call.user_prompt},
        output={"raw_text": call.response_text, "parsed": call.parsed},
        metadata={"attempt": call.attempt, "parse_ok": call.parse_ok, **extra},
    )


def _decision_generation(
    trace_id: str, trace_name: str, branch: str, extra: dict[str, Any]
) -> LangfuseGeneration:
    return LangfuseGeneration(
        trace_id=trace_id,
        trace_name=trace_name,
        name=f"actor:{branch}",
        model="deterministic-null",
        input={"offer_summary": extra.get("offer_summary")},
        output={"promo_decision": extra.get("promo_decision")},
        metadata=extra,
    )


def push_to_langfuse(
    loaded: LoadedTraces,
    public_key: str,
    secret_key: str,
    host: str,
) -> int:
    client = _langfuse_client(public_key, secret_key, host)
    if hasattr(client, "start_observation"):
        sent = _push_v3(client, loaded)
    elif hasattr(client, "trace"):
        sent = _push_v2(client, loaded)
    else:
        raise RuntimeError("unsupported langfuse SDK: no start_observation or trace API")
    client.flush()
    return sent


def _stable_trace_id(client: Any, key: str) -> str:
    create = getattr(client, "create_trace_id", None)
    if callable(create):
        try:
            return str(create(seed=key))
        except TypeError:
            return str(create())
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]


def _push_v3(client: Any, loaded: LoadedTraces) -> int:
    from langfuse import propagate_attributes

    sent = 0
    for profile in loaded.profiles:
        generations = to_langfuse_generations(loaded.header, profile)
        if not generations:
            continue
        metadata = trace_metadata(loaded.header, profile)
        trace_id = _stable_trace_id(client, generations[0].trace_id)
        trace_attributes = {key: str(value) for key, value in metadata.items()}
        with propagate_attributes(
            user_id=profile.snapshot.profile_id,
            trace_name=generations[0].trace_name,
            metadata=trace_attributes,
        ):
            root = client.start_observation(
                name=generations[0].trace_name,
                as_type="span",
                trace_context={"trace_id": trace_id},
                metadata=metadata,
            )
            for generation in generations:
                observation = root.start_observation(
                    name=generation.name,
                    as_type="generation",
                    model=generation.model,
                    input=generation.input,
                    metadata=generation.metadata,
                )
                observation.update(output=generation.output)
                observation.end()
                sent += 1
            root.end()
    return sent


def _push_v2(client: Any, loaded: LoadedTraces) -> int:
    sent = 0
    for profile in loaded.profiles:
        generations = to_langfuse_generations(loaded.header, profile)
        if not generations:
            continue
        metadata = trace_metadata(loaded.header, profile)
        trace = client.trace(
            id=generations[0].trace_id,
            name=generations[0].trace_name,
            user_id=profile.snapshot.profile_id,
            metadata=metadata,
        )
        for generation in generations:
            trace.generation(
                name=generation.name,
                model=generation.model,
                input=generation.input,
                output=generation.output,
                metadata=generation.metadata,
            )
            sent += 1
    return sent


def _langfuse_client(public_key: str, secret_key: str, host: str) -> Any:
    try:
        from langfuse import Langfuse
    except ImportError as error:
        raise RuntimeError(
            "langfuse SDK is not installed; run `uv add langfuse` to enable --to langfuse export"
        ) from error
    return Langfuse(public_key=public_key, secret_key=secret_key, host=host)


def write_generations_json(loaded: LoadedTraces, path: Path) -> int:
    payload: list[dict[str, Any]] = []
    for profile in loaded.profiles:
        for generation in to_langfuse_generations(loaded.header, profile):
            payload.append(generation.model_dump())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(payload)
