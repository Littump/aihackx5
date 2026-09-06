import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.ml.tracing import BranchTrace, EvalRunHeader, LlmCall, ProfileTrace


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


JUDGE_QUESTIONS: tuple[str, ...] = (
    "Buyer read: do the classification keywords and label match the shopper's real "
    "metrics (lifecycle from overdue_ratio/momentum, modifiers from basket/headroom)?",
    "Goal fit: is goal.target (visit_frequency or basket_value) plus its proxy the right "
    "next-best-action for this buyer, and does the hero mechanic serve that target?",
    "Strategy fit: does the hero challenge aim at an INCREMENTAL visit or a bigger basket, "
    "not a staple they already buy every trip?",
    "Reward fit: does the two-currency reward match posture (xp always on; points none for "
    "promo_immune, capped for value_selective, up to high for deal_driven)?",
    "High-margin: when the mandate is on, is one challenge on a high-margin category to earn "
    "more per trip without eroding the rest of the plan?",
    "Rationale honesty: do goal and challenge rationales cite a real number from the insight?",
    "Actor realism: is the synthetic shopper's verdict consistent with their persona_brief, "
    "deal_attitude and their own thinking?",
    "Over-cooperation: is the shopper too agreeable — using/completing an offer a skeptic of this "
    "profile would ignore or buy as usual — or is engagement in line with their personality?",
)


def read_trace_file(path: Path) -> LoadedTraces:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"empty trace file: {path}")
    header = EvalRunHeader.model_validate_json(lines[0])
    profiles = [ProfileTrace.model_validate_json(line) for line in lines[1:]]
    return LoadedTraces(header=header, profiles=profiles)


def trace_metadata(header: EvalRunHeader, profile: ProfileTrace) -> dict[str, Any]:
    snapshot = profile.snapshot
    return {
        "seed": header.seed,
        "null_test": header.null_test,
        "no_llm": header.no_llm,
        "planner_model": header.planner_model,
        "actor_model": header.actor_model,
        "plan_source": profile.plan_source,
        "segment": snapshot.segment,
        "persona_label": snapshot.persona_label,
        "persona_brief": snapshot.persona_brief,
        "archetype": snapshot.archetype,
        "deal_attitude": snapshot.deal_attitude,
        "churn_risk": snapshot.churn_risk,
        "promo_sensitivity": snapshot.promo_sensitivity,
        "visits_per_week": snapshot.visits_per_week,
        "favorite_categories": snapshot.favorite_categories,
    }


def _latest_parsed_plan(profile: ProfileTrace) -> dict[str, Any] | None:
    for call in reversed(profile.planner_calls):
        if call.parsed is not None:
            return call.parsed
    return None


def _branch(profile: ProfileTrace, name: str) -> BranchTrace | None:
    for branch in profile.branches:
        if branch.branch == name:
            return branch
    return None


def shopper_view(profile: ProfileTrace) -> dict[str, Any]:
    snapshot = profile.snapshot
    view: dict[str, Any] = {
        "profile_id": snapshot.profile_id,
        "who_they_are": snapshot.persona_brief,
        "persona_label": snapshot.persona_label,
        "archetype": snapshot.archetype,
        "segment": snapshot.segment,
        "deal_attitude": snapshot.deal_attitude,
        "churn_risk": snapshot.churn_risk,
        "visits_per_week": snapshot.visits_per_week,
        "avg_basket": snapshot.avg_basket,
        "promo_sensitivity": snapshot.promo_sensitivity,
        "routine_rigidity": snapshot.routine_rigidity,
        "favorite_categories": snapshot.favorite_categories,
        "observed_habits": [habit.model_dump() for habit in snapshot.observed_habits],
    }
    human = snapshot.shopper_persona
    if human:
        view["who_they_are"] = (
            f"{human.get('full_name')}, {human.get('age')}, {human.get('occupation')}"
        )
        view["persona"] = human
    return view


def _dict(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def planner_strategy_view(profile: ProfileTrace) -> dict[str, Any]:
    parsed = _latest_parsed_plan(profile)
    llm_branch = _branch(profile, "treatment_llm")
    classification = _dict(parsed.get("classification")) if parsed else None
    goal = _dict(parsed.get("goal")) if parsed else None
    challenges = parsed.get("challenges") if parsed else None
    hero: dict[str, Any] | None = None
    if isinstance(challenges, list) and challenges:
        hero = next(
            (_dict(item) for item in challenges if _dict(item) and item.get("role") == "hero"),
            _dict(challenges[0]),
        )
    reward = _dict(hero.get("reward")) if hero else None
    insights = parsed.get("insights") if parsed else None
    insight_names = (
        [item.get("name") for item in insights if isinstance(item, dict)]
        if isinstance(insights, list)
        else None
    )
    return {
        "plan_source": profile.plan_source,
        "offer_shown_to_user": llm_branch.offer_summary if llm_branch is not None else None,
        "buyer_label": classification.get("label") if classification else None,
        "buyer_keywords": classification.get("keywords") if classification else None,
        "posture": classification.get("posture") if classification else None,
        "goal_target": goal.get("target") if goal else None,
        "goal_proxy": goal.get("proxy") if goal else None,
        "goal_direction": goal.get("direction") if goal else None,
        "goal_rationale": goal.get("rationale") if goal else None,
        "mechanic": hero.get("challenge_type") if hero else None,
        "category": hero.get("category") if hero else None,
        "target": hero.get("target") if hero else None,
        "reward_xp_level": reward.get("xp_level") if reward else None,
        "reward_points_level": reward.get("points_level") if reward else None,
        "rationale": hero.get("rationale") if hero else None,
        "insight_names": insight_names,
    }


def weekly_series(branch: BranchTrace) -> list[dict[str, Any]]:
    return [
        {
            "week_index": week.week_index,
            "challenge_active": week.challenge_active,
            "baseline_visits": week.baseline_visits,
            "extra_visits": week.extra_visits,
            "cumulative_visits": week.cumulative_visits,
            "promo_decision": week.decision.promo_decision if week.decision is not None else None,
        }
        for week in branch.weeks
    ]


def branch_metric_scores(branch: BranchTrace) -> dict[str, float]:
    scores = {
        f"{branch.branch}_incremental_visits": float(branch.incremental_visits),
        f"{branch.branch}_net_effect_rub": float(branch.net_effect_rub),
        f"{branch.branch}_reward_cost_rub": float(branch.reward_cost_rub),
    }
    for week in branch.weeks:
        scores[f"{branch.branch}_cum_visits_T{week.week_index}"] = float(week.cumulative_visits)
    return scores


def branch_decision_view(branch: BranchTrace) -> dict[str, Any]:
    decision = branch.decision
    return {
        "branch": branch.branch,
        "offer": branch.offer_summary,
        "shopper_verdict": decision.promo_decision,
        "shopper_thinking": decision.thinking,
        "shopper_rationale": decision.rationale,
        "extra_visits": decision.extra_visits,
        "completed_challenge": decision.completed_challenge,
        "decision_source": decision.source,
        "relevance_hit": branch.relevance_hit,
        "incremental_visits": branch.incremental_visits,
        "reward_cost_rub": branch.reward_cost_rub,
        "net_effect_rub": branch.net_effect_rub,
        "weekly_progression": weekly_series(branch),
    }


def profile_story(profile: ProfileTrace) -> dict[str, dict[str, Any]]:
    return {
        "input": {
            "shopper": shopper_view(profile),
            "planner_strategy": planner_strategy_view(profile),
        },
        "output": {
            "branch_decisions": [branch_decision_view(branch) for branch in profile.branches],
            "how_to_judge": list(JUDGE_QUESTIONS),
        },
    }


def to_langfuse_generations(
    header: EvalRunHeader, profile: ProfileTrace
) -> list[LangfuseGeneration]:
    trace_id = f"eval-{header.seed}-{profile.snapshot.profile_id}"
    trace_name = f"profile {profile.snapshot.profile_id} ({profile.snapshot.segment})"
    strategy = planner_strategy_view(profile)
    generations: list[LangfuseGeneration] = []
    for call in profile.planner_calls:
        planner_extra = {
            "buyer_label": strategy["buyer_label"],
            "goal_target": strategy["goal_target"],
            "goal_proxy": strategy["goal_proxy"],
            "mechanic": strategy["mechanic"],
            "target": strategy["target"],
            "reward_xp_level": strategy["reward_xp_level"],
            "reward_points_level": strategy["reward_points_level"],
            "plan_source": profile.plan_source,
        }
        generations.append(_call_generation(trace_id, trace_name, call, extra=planner_extra))
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


def profile_trace_key(fingerprint: str, header: EvalRunHeader, profile: ProfileTrace) -> str:
    return f"{fingerprint}-eval-{header.seed}-{profile.snapshot.profile_id}"


def summary_trace_key(fingerprint: str, header: EvalRunHeader) -> str:
    return f"{fingerprint}-judge-summary-{header.seed}"


def iteration_summary_trace_key(fingerprint: str, header: EvalRunHeader) -> str:
    return f"{fingerprint}-iter-{header.iteration}-{header.seed}"


def resolve_summary_trace_id(client: Any, fingerprint: str, header: EvalRunHeader) -> str:
    return _stable_trace_id(client, summary_trace_key(fingerprint, header))


def open_langfuse_client(public_key: str, secret_key: str, host: str) -> Any:
    return _langfuse_client(public_key, secret_key, host)


def resolve_trace_id(
    client: Any, fingerprint: str, header: EvalRunHeader, profile: ProfileTrace
) -> str:
    return _stable_trace_id(client, profile_trace_key(fingerprint, header, profile))


def run_fingerprint(loaded: LoadedTraces) -> str:
    hasher = hashlib.sha256()
    hasher.update(loaded.header.model_dump_json().encode("utf-8"))
    for profile in loaded.profiles:
        for call in profile.planner_calls:
            hasher.update((call.response_text or "").encode("utf-8"))
        for branch in profile.branches:
            if branch.llm_call is not None:
                hasher.update((branch.llm_call.response_text or "").encode("utf-8"))
    return hasher.hexdigest()[:8]


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
    fingerprint = run_fingerprint(loaded)
    for profile in loaded.profiles:
        generations = to_langfuse_generations(loaded.header, profile)
        if not generations:
            continue
        metadata = trace_metadata(loaded.header, profile)
        story = profile_story(profile)
        trace_id = _stable_trace_id(client, profile_trace_key(fingerprint, loaded.header, profile))
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
                input=story["input"],
                output=story["output"],
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
            _emit_week_observations(root, profile)
            root.end()
        _emit_branch_scores(client, trace_id, profile)
    return sent


def _push_v2(client: Any, loaded: LoadedTraces) -> int:
    sent = 0
    fingerprint = run_fingerprint(loaded)
    for profile in loaded.profiles:
        generations = to_langfuse_generations(loaded.header, profile)
        if not generations:
            continue
        metadata = trace_metadata(loaded.header, profile)
        story = profile_story(profile)
        trace = client.trace(
            id=profile_trace_key(fingerprint, loaded.header, profile),
            name=generations[0].trace_name,
            user_id=profile.snapshot.profile_id,
            input=story["input"],
            output=story["output"],
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
        _emit_branch_scores_v2(trace, profile)
    return sent


def _emit_week_observations(root: Any, profile: ProfileTrace) -> None:
    for branch in profile.branches:
        for week in branch.weeks:
            observation = root.start_observation(
                name=f"week:{branch.branch}:T{week.week_index}",
                as_type="span",
                input={"challenge_active": week.challenge_active},
                output={
                    "baseline_visits": week.baseline_visits,
                    "extra_visits": week.extra_visits,
                    "cumulative_visits": week.cumulative_visits,
                },
                metadata={"branch": branch.branch, "week_index": week.week_index},
            )
            observation.end()


def _emit_branch_scores(client: Any, trace_id: str, profile: ProfileTrace) -> None:
    if not hasattr(client, "create_score"):
        return
    for branch in profile.branches:
        for name, value in branch_metric_scores(branch).items():
            client.create_score(
                name=name,
                value=value,
                trace_id=trace_id,
                data_type="NUMERIC",
                score_id=f"{trace_id}-{name}",
            )


def _emit_branch_scores_v2(trace: Any, profile: ProfileTrace) -> None:
    if not hasattr(trace, "score"):
        return
    for branch in profile.branches:
        for name, value in branch_metric_scores(branch).items():
            trace.score(name=name, value=value, data_type="NUMERIC")


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
        story = profile_story(profile)
        payload.append(
            {
                "trace_name": f"profile {profile.snapshot.profile_id} ({profile.snapshot.segment})",
                "story": story,
                "generations": [
                    generation.model_dump()
                    for generation in to_langfuse_generations(loaded.header, profile)
                ],
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(payload)
