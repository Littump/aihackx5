import asyncio
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.ml import config, langfuse_export, llm_client, tool_schemas, tracing
from app.ml.langfuse_export import LoadedTraces
from app.ml.llm_client import ChatClient
from app.ml.schemas import JudgeProposal, JudgeProposals, JudgeVerdict, ProfileJudgement
from app.ml.tracing import EvalRunHeader, LlmCall, ProfileTrace

_SCHEMA_NAME = "judge_verdict"
_SYSTEM_PROMPT_FILE = "judge_system.md"
_META_SCHEMA_NAME = "judge_proposals"
_META_SYSTEM_PROMPT_FILE = "judge_meta_system.md"

_SCORE_DIMENSIONS: tuple[str, ...] = (
    "strategy_fit",
    "mechanic_choice",
    "reward_fit",
    "rationale_honesty",
    "persona_consistency",
)


class JudgeAggregate(BaseModel):
    profiles: int
    parsed: int
    verdict_good: int
    verdict_mixed: int
    verdict_bad: int
    coop_too_cooperative: int
    coop_consistent: int
    coop_too_resistant: int
    mean_strategy_fit: float
    mean_mechanic_choice: float
    mean_reward_fit: float
    mean_rationale_honesty: float
    mean_persona_consistency: float


def _mean(values: list[int]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def build_judge_summary(turns: list["JudgeTurn"]) -> JudgeAggregate:
    verdicts = [turn.verdict for turn in turns if turn.verdict is not None]
    dimension_values: dict[str, list[int]] = {dimension: [] for dimension in _SCORE_DIMENSIONS}
    for verdict in verdicts:
        dumped = verdict.model_dump()
        for dimension in _SCORE_DIMENSIONS:
            dimension_values[dimension].append(int(dumped[dimension]))
    return JudgeAggregate(
        profiles=len(turns),
        parsed=len(verdicts),
        verdict_good=sum(1 for verdict in verdicts if verdict.verdict == "good"),
        verdict_mixed=sum(1 for verdict in verdicts if verdict.verdict == "mixed"),
        verdict_bad=sum(1 for verdict in verdicts if verdict.verdict == "bad"),
        coop_too_cooperative=sum(
            1 for verdict in verdicts if verdict.actor_cooperation == "too_cooperative"
        ),
        coop_consistent=sum(1 for verdict in verdicts if verdict.actor_cooperation == "consistent"),
        coop_too_resistant=sum(
            1 for verdict in verdicts if verdict.actor_cooperation == "too_resistant"
        ),
        mean_strategy_fit=_mean(dimension_values["strategy_fit"]),
        mean_mechanic_choice=_mean(dimension_values["mechanic_choice"]),
        mean_reward_fit=_mean(dimension_values["reward_fit"]),
        mean_rationale_honesty=_mean(dimension_values["rationale_honesty"]),
        mean_persona_consistency=_mean(dimension_values["persona_consistency"]),
    )


def judge_summary_scores(aggregate: JudgeAggregate) -> dict[str, float]:
    return {
        "judge_parsed_count": float(aggregate.parsed),
        "judge_verdict_good_count": float(aggregate.verdict_good),
        "judge_verdict_mixed_count": float(aggregate.verdict_mixed),
        "judge_verdict_bad_count": float(aggregate.verdict_bad),
        "judge_too_cooperative_count": float(aggregate.coop_too_cooperative),
        "judge_consistent_count": float(aggregate.coop_consistent),
        "judge_too_resistant_count": float(aggregate.coop_too_resistant),
        "judge_mean_strategy_fit": float(aggregate.mean_strategy_fit),
        "judge_mean_mechanic_choice": float(aggregate.mean_mechanic_choice),
        "judge_mean_reward_fit": float(aggregate.mean_reward_fit),
        "judge_mean_rationale_honesty": float(aggregate.mean_rationale_honesty),
        "judge_mean_persona_consistency": float(aggregate.mean_persona_consistency),
    }


def push_judge_summary_to_langfuse(
    loaded: LoadedTraces,
    turns: list["JudgeTurn"],
    public_key: str,
    secret_key: str,
    host: str,
) -> int:
    client = langfuse_export.open_langfuse_client(public_key, secret_key, host)
    fingerprint = langfuse_export.run_fingerprint(loaded)
    trace_id = langfuse_export._stable_trace_id(
        client, langfuse_export.iteration_summary_trace_key(fingerprint, loaded.header)
    )
    scores = judge_summary_scores(build_judge_summary(turns))
    for name, value in scores.items():
        client.create_score(
            name=name,
            value=value,
            trace_id=trace_id,
            data_type="NUMERIC",
            score_id=f"{trace_id}-{name}",
        )
    client.flush()
    return len(scores)


class JudgeTurn(BaseModel):
    profile_id: str
    segment: str
    verdict: JudgeVerdict | None
    call: LlmCall


def _render_user_prompt(profile: ProfileTrace) -> str:
    story = langfuse_export.profile_story(profile)
    payload = {
        "shopper": story["input"]["shopper"],
        "planner_strategy": story["input"]["planner_strategy"],
        "branch_decisions": story["output"]["branch_decisions"],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _parse_verdict(parsed: dict[str, Any] | None) -> JudgeVerdict | None:
    if parsed is None:
        return None
    try:
        return JudgeVerdict.model_validate(parsed)
    except ValueError:
        return None


async def judge_profile(
    client: ChatClient, header: EvalRunHeader, profile: ProfileTrace
) -> JudgeTurn:
    system_prompt = llm_client.load_prompt(_SYSTEM_PROMPT_FILE)
    user_prompt = _render_user_prompt(profile)
    schema = tool_schemas.judge_verdict_schema()
    last_call: LlmCall | None = None
    for attempt in range(config.ACTOR_RETRY_MAX + 1):
        result = await client.emit_json(
            system_prompt, user_prompt, _SCHEMA_NAME, schema, max_tokens=config.JUDGE_MAX_TOKENS
        )
        call = tracing.build_llm_call(
            role="judge",
            label=f"judge_{profile.snapshot.profile_id}",
            model=client.model,
            base_url=client.base_url,
            attempt=attempt,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            result=result,
        )
        verdict = _parse_verdict(result.parsed)
        if verdict is not None:
            return JudgeTurn(
                profile_id=profile.snapshot.profile_id,
                segment=profile.snapshot.segment,
                verdict=verdict,
                call=call,
            )
        last_call = call
        if attempt < config.ACTOR_RETRY_MAX:
            await asyncio.sleep(config.ACTOR_RETRY_BACKOFF_S * (attempt + 1))
    assert last_call is not None
    return JudgeTurn(
        profile_id=profile.snapshot.profile_id,
        segment=profile.snapshot.segment,
        verdict=None,
        call=last_call,
    )


async def judge_traces(
    client: ChatClient, loaded: LoadedTraces, max_concurrency: int
) -> list[JudgeTurn]:
    semaphore = asyncio.Semaphore(max(1, max_concurrency))

    async def _run(profile: ProfileTrace) -> JudgeTurn:
        async with semaphore:
            return await judge_profile(client, loaded.header, profile)

    turns = await asyncio.gather(*(_run(profile) for profile in loaded.profiles))
    return list(turns)


def judgements(turns: list[JudgeTurn]) -> list[ProfileJudgement]:
    return [
        ProfileJudgement(profile_id=turn.profile_id, segment=turn.segment, verdict=turn.verdict)
        for turn in turns
        if turn.verdict is not None
    ]


def _score_value(score: int) -> float:
    return round((score - 1) / 4, 4)


def push_scores_to_langfuse(
    loaded: LoadedTraces,
    turns: list[JudgeTurn],
    public_key: str,
    secret_key: str,
    host: str,
) -> int:
    client = langfuse_export.open_langfuse_client(public_key, secret_key, host)
    fingerprint = langfuse_export.run_fingerprint(loaded)
    profiles = {profile.snapshot.profile_id: profile for profile in loaded.profiles}
    sent = 0
    for turn in turns:
        profile = profiles.get(turn.profile_id)
        if profile is None or turn.verdict is None:
            continue
        trace_id = langfuse_export.resolve_trace_id(client, fingerprint, loaded.header, profile)
        _attach_verdict_annotation(client, trace_id, turn)
        sent += _emit_scores(client, trace_id, turn)
    client.flush()
    return sent


def _emit_scores(client: Any, trace_id: str, turn: JudgeTurn) -> int:
    assert turn.verdict is not None
    verdict = turn.verdict
    dumped = verdict.model_dump()
    sent = 0
    for dimension in _SCORE_DIMENSIONS:
        name = f"judge_{dimension}"
        client.create_score(
            name=name,
            value=_score_value(int(dumped[dimension])),
            trace_id=trace_id,
            data_type="NUMERIC",
            comment=verdict.summary,
            score_id=f"{trace_id}-{name}",
        )
        sent += 1
    client.create_score(
        name="judge_actor_cooperation",
        value=verdict.actor_cooperation,
        trace_id=trace_id,
        data_type="CATEGORICAL",
        comment=verdict.summary,
        score_id=f"{trace_id}-judge_actor_cooperation",
    )
    client.create_score(
        name="judge_verdict",
        value=verdict.verdict,
        trace_id=trace_id,
        data_type="CATEGORICAL",
        comment=verdict.summary,
        score_id=f"{trace_id}-judge_verdict",
    )
    return sent + 2


def write_judgements_json(turns: list[JudgeTurn], out: Path) -> int:
    payload = [
        {
            "profile_id": turn.profile_id,
            "segment": turn.segment,
            "verdict": turn.verdict.model_dump() if turn.verdict is not None else None,
            "parse_ok": turn.call.parse_ok,
        }
        for turn in turns
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(payload)


class ProposalsTurn(BaseModel):
    proposals: JudgeProposals | None
    call: LlmCall | None


def _verdict_tags(verdict: JudgeVerdict) -> list[str]:
    tags = [f"judge:{verdict.verdict}"]
    if verdict.actor_cooperation != "consistent":
        tags.append(f"judge:{verdict.actor_cooperation}")
    return tags


def _verdict_level(verdict: JudgeVerdict) -> str:
    if verdict.verdict == "bad":
        return "ERROR"
    if verdict.verdict == "mixed":
        return "WARNING"
    return "DEFAULT"


def _severity_level(severity: str) -> str:
    if severity == "high":
        return "ERROR"
    if severity == "medium":
        return "WARNING"
    return "DEFAULT"


def _attach_verdict_annotation(client: Any, trace_id: str, turn: JudgeTurn) -> None:
    assert turn.verdict is not None
    verdict = turn.verdict
    with client.start_as_current_observation(
        name="judge:verdict",
        as_type="evaluator",
        trace_context={"trace_id": trace_id},
        input={"dimensions": list(_SCORE_DIMENSIONS)},
        output=verdict.model_dump(),
        level=_verdict_level(verdict),
        metadata={"verdict": verdict.verdict, "actor_cooperation": verdict.actor_cooperation},
    ):
        story_name = f"profile {turn.profile_id} ({turn.segment})"
        client.update_current_trace(name=story_name, tags=_verdict_tags(verdict))


def _proposal_digest(loaded: LoadedTraces, turns: list[JudgeTurn]) -> str:
    profiles = {profile.snapshot.profile_id: profile for profile in loaded.profiles}
    rows: list[dict[str, Any]] = []
    for turn in turns:
        if turn.verdict is None:
            continue
        verdict = turn.verdict
        profile = profiles.get(turn.profile_id)
        strategy = langfuse_export.planner_strategy_view(profile) if profile is not None else {}
        rows.append(
            {
                "profile_id": turn.profile_id,
                "segment": turn.segment,
                "mechanic": strategy.get("mechanic"),
                "target": strategy.get("target"),
                "reward_xp_level": strategy.get("reward_xp_level"),
                "reward_points_level": strategy.get("reward_points_level"),
                "scores": {
                    dimension: getattr(verdict, dimension) for dimension in _SCORE_DIMENSIONS
                },
                "actor_cooperation": verdict.actor_cooperation,
                "verdict": verdict.verdict,
                "summary": verdict.summary,
            }
        )
    return json.dumps(rows, ensure_ascii=False, indent=2)


def _parse_proposals(parsed: dict[str, Any] | None) -> JudgeProposals | None:
    if parsed is None:
        return None
    try:
        return JudgeProposals.model_validate(parsed)
    except ValueError:
        return None


def _validate_proposals(
    proposals: JudgeProposals, known_profiles: set[str], min_evidence: int
) -> JudgeProposals:
    kept: list[JudgeProposal] = []
    for proposal in proposals.proposals:
        seen: set[str] = set()
        grounded = []
        for item in proposal.evidence:
            if item.profile_id in known_profiles and item.profile_id not in seen:
                seen.add(item.profile_id)
                grounded.append(item)
        if len(seen) >= min_evidence:
            kept.append(proposal.model_copy(update={"evidence": grounded}))
    return proposals.model_copy(update={"proposals": kept})


async def synthesize_proposals(
    client: ChatClient, loaded: LoadedTraces, turns: list[JudgeTurn], min_evidence: int
) -> ProposalsTurn:
    parsed_turns = [turn for turn in turns if turn.verdict is not None]
    if not parsed_turns:
        return ProposalsTurn(proposals=None, call=None)
    system_prompt = llm_client.load_prompt(_META_SYSTEM_PROMPT_FILE)
    user_prompt = _proposal_digest(loaded, parsed_turns)
    schema = tool_schemas.judge_proposals_schema()
    known_profiles = {turn.profile_id for turn in parsed_turns}
    last_call: LlmCall | None = None
    for attempt in range(config.ACTOR_RETRY_MAX + 1):
        result = await client.emit_json(
            system_prompt,
            user_prompt,
            _META_SCHEMA_NAME,
            schema,
            max_tokens=config.JUDGE_META_MAX_TOKENS,
        )
        call = tracing.build_llm_call(
            role="judge",
            label="judge_proposals",
            model=client.model,
            base_url=client.base_url,
            attempt=attempt,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            result=result,
        )
        proposals = _parse_proposals(result.parsed)
        if proposals is not None:
            validated = _validate_proposals(proposals, known_profiles, min_evidence)
            return ProposalsTurn(proposals=validated, call=call)
        last_call = call
        if attempt < config.ACTOR_RETRY_MAX:
            await asyncio.sleep(config.ACTOR_RETRY_BACKOFF_S * (attempt + 1))
    return ProposalsTurn(proposals=None, call=last_call)


def _summary_tags(proposals: JudgeProposals) -> list[str]:
    tags = ["judge:summary"]
    severities = {proposal.severity for proposal in proposals.proposals}
    tags.extend(f"judge:{severity}" for severity in sorted(severities))
    return tags


def push_proposals_to_langfuse(
    loaded: LoadedTraces,
    proposals: JudgeProposals,
    public_key: str,
    secret_key: str,
    host: str,
) -> int:
    client = langfuse_export.open_langfuse_client(public_key, secret_key, host)
    fingerprint = langfuse_export.run_fingerprint(loaded)
    trace_id = langfuse_export.resolve_summary_trace_id(client, fingerprint, loaded.header)
    name = f"judge run summary (seed={loaded.header.seed})"
    with client.start_as_current_observation(
        name=name,
        as_type="evaluator",
        trace_context={"trace_id": trace_id},
        input={"profiles": len(loaded.profiles), "proposal_count": len(proposals.proposals)},
        output={"analysis": proposals.analysis},
    ) as root:
        client.update_current_trace(
            name=name,
            user_id="judge-summary",
            tags=_summary_tags(proposals),
            metadata={"proposal_count": len(proposals.proposals)},
        )
        for proposal in proposals.proposals:
            child = root.start_observation(
                name=f"proposal: {proposal.title}",
                as_type="evaluator",
                input={
                    "dimension": proposal.dimension,
                    "severity": proposal.severity,
                    "evidence_profiles": [item.profile_id for item in proposal.evidence],
                },
                output=proposal.model_dump(),
                level=_severity_level(proposal.severity),
            )
            child.end()
    client.create_score(
        name="judge_proposal_count",
        value=float(len(proposals.proposals)),
        trace_id=trace_id,
        data_type="NUMERIC",
        comment=proposals.analysis[:480],
        score_id=f"{trace_id}-judge_proposal_count",
    )
    client.flush()
    return len(proposals.proposals)


def write_proposals_json(proposals: JudgeProposals | None, out: Path) -> int:
    payload = (
        proposals.model_dump() if proposals is not None else {"analysis": None, "proposals": []}
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(payload["proposals"])
