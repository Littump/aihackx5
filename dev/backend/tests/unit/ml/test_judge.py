import contextlib
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from app.ml import judge
from app.ml.langfuse_export import LoadedTraces
from app.ml.schemas import (
    JudgeInsight,
    JudgeProposal,
    JudgeProposals,
    JudgeVerdict,
    ProposalEvidence,
)
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
        persona_brief="Родитель, закупается на неделю, к акциям равнодушен",
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
        promo_decision="buy_as_usual",
        engaged=False,
        extra_visits=0,
        completed_challenge=False,
        thinking="dairy overdue but I buy it anyway",
        rationale="offer changes nothing",
        source="actor_llm",
    )
    planner_call = LlmCall(
        role="planner",
        label="planner_attempt_0",
        model="qwen",
        base_url="http://x/v1",
        attempt=0,
        system_prompt="sys",
        user_prompt="usr",
        response_text='{"steps":[]}',
        parsed={
            "thinking": "родитель, пекарня просрочена 2 цикла",
            "classification": {
                "keywords": ["steady", "bakery_lapsed", "day_to_day"],
                "label": "Steady Everyday Parent With A Lapsed Bakery Run",
                "description": "On-cadence weekly parent who let bakery lapse a full cycle.",
                "evidence": ["bakery_lapsed: top_category_overdue_ratio=2.0"],
                "posture": "value_selective",
                "is_ambiguous": False,
            },
            "goal": {
                "target": "visit_frequency",
                "proxy": "lapsed_category_rebuy",
                "direction": "recover",
                "rationale": "bakery 14 days overdue (2x cadence) - the re-buy IS the trip",
            },
            "insights": [
                {
                    "name": "bakery_lapsed",
                    "kind": "category_overdue",
                    "detail": "bakery 14 days overdue",
                    "evidence": "top_category_overdue_ratio=2.0",
                }
            ],
            "challenges": [
                {
                    "role": "hero",
                    "insight_ref": "bakery_lapsed",
                    "challenge_type": "replenishment",
                    "category": "bakery",
                    "target": 1,
                    "reward": {"xp_level": "medium", "points_level": "low"},
                    "deadline_days": 7,
                    "rationale": "Bakery is 14 days overdue (2x cadence).",
                },
                {
                    "role": "side",
                    "insight_ref": "snacks_high_margin",
                    "challenge_type": "collection",
                    "category": "snacks",
                    "target": 1,
                    "reward": {"xp_level": "low", "points_level": "none"},
                    "deadline_days": 7,
                    "rationale": "high-margin snacks (margin 0.3) to earn more per trip, XP-led",
                },
            ],
            "general_strategy": {
                "insight_refs": ["bakery_lapsed", "snacks_high_margin"],
                "rationale": "recover the weekly rhythm via the lapsed bakery re-buy, XP-led",
                "next_week_hint": "drop the proxy once the lapse closes",
            },
        },
        parse_ok=True,
    )
    branch = BranchTrace(
        branch="treatment_llm",
        offer_summary="dairy replenishment",
        plan_source="llm",
        relevance_hit=True,
        decision=decision,
        incremental_visits=0,
        reward_cost_rub=0.0,
        net_effect_rub=-1.5,
        llm_call=None,
    )
    return ProfileTrace(
        snapshot=snapshot, plan_source="llm", planner_calls=[planner_call], branches=[branch]
    )


def _verdict() -> JudgeVerdict:
    return JudgeVerdict(
        planner_insights=[
            JudgeInsight(
                aspect="strategy_fit",
                observation="bakery overdue 2x cadence (overdue_ratio=2.0) - incremental",
                severity="good",
            ),
            JudgeInsight(
                aspect="reward_fit",
                observation="points low to a value_selective skeptic - defensible",
                severity="concern",
            ),
        ],
        persona_insights=[
            JudgeInsight(
                aspect="in_character",
                observation="promo_skeptic bought as usual and ignored the offer - consistent",
                severity="good",
            ),
            JudgeInsight(
                aspect="over_cooperation",
                observation="did not complete an offer they would ignore - no sycophancy",
                severity="good",
            ),
        ],
        strategy_fit=5,
        mechanic_choice=4,
        reward_fit=3,
        rationale_honesty=5,
        persona_consistency=4,
        actor_cooperation="consistent",
        verdict="good",
        summary="Solid incremental bakery re-buy; skeptic stayed in character.",
    )


def _turn(verdict: JudgeVerdict | None) -> judge.JudgeTurn:
    call = LlmCall(
        role="judge",
        label="judge_P0001",
        model="deepseek",
        base_url="http://x/v1",
        attempt=0,
        system_prompt="sys",
        user_prompt="usr",
        response_text="{}",
        parsed=None if verdict is None else verdict.model_dump(),
        parse_ok=verdict is not None,
    )
    return judge.JudgeTurn(profile_id="P0001", segment="regular_mid", verdict=verdict, call=call)


def test_render_user_prompt_has_story_sections() -> None:
    payload = json.loads(judge._render_user_prompt(_profile()))
    assert payload["shopper"]["who_they_are"].startswith("Родитель")
    assert payload["planner_strategy"]["mechanic"] == "replenishment"
    assert payload["branch_decisions"][0]["shopper_verdict"] == "buy_as_usual"


def test_parse_verdict_accepts_valid_and_rejects_invalid() -> None:
    assert judge._parse_verdict(_verdict().model_dump()) is not None
    assert judge._parse_verdict({"strategy_fit": 9}) is None
    assert judge._parse_verdict(None) is None


def test_score_value_maps_1_to_5_onto_unit_interval() -> None:
    assert judge._score_value(1) == 0.0
    assert judge._score_value(3) == 0.5
    assert judge._score_value(5) == 1.0


def test_judgements_drops_unparsed_turns() -> None:
    turns = [_turn(_verdict()), _turn(None)]
    scored = judge.judgements(turns)
    assert len(scored) == 1
    assert scored[0].profile_id == "P0001"


class _FakeSpan:
    def __init__(self, client: "_FakeClient", name: str | None) -> None:
        self.client = client
        self.name = name

    def start_observation(self, **kwargs: Any) -> "_FakeSpan":
        self.client.observations.append(kwargs)
        return _FakeSpan(self.client, kwargs.get("name"))

    def end(self) -> None:
        self.client.ended += 1


class _FakeClient:
    def __init__(self) -> None:
        self.scores: list[dict[str, Any]] = []
        self.observations: list[dict[str, Any]] = []
        self.trace_updates: list[dict[str, Any]] = []
        self.flushed = False
        self.ended = 0

    def create_trace_id(self, seed: str) -> str:
        return f"tid-{seed}"

    def create_score(self, **kwargs: Any) -> None:
        self.scores.append(kwargs)

    @contextlib.contextmanager
    def start_as_current_observation(self, **kwargs: Any) -> Iterator[_FakeSpan]:
        self.observations.append(kwargs)
        yield _FakeSpan(self, kwargs.get("name"))

    def update_current_trace(self, **kwargs: Any) -> None:
        self.trace_updates.append(kwargs)

    def flush(self) -> None:
        self.flushed = True


def test_push_scores_emits_all_dimensions_without_touching_trace_root(monkeypatch: Any) -> None:
    fake = _FakeClient()
    monkeypatch.setattr(judge.langfuse_export, "open_langfuse_client", lambda *a, **k: fake)
    loaded = LoadedTraces(header=_header(), profiles=[_profile()])
    turns = [_turn(_verdict())]
    sent = judge.push_scores_to_langfuse(loaded, turns, "pk", "sk", "http://localhost:3000")
    assert sent == 7
    assert fake.flushed is True
    annotation = next(o for o in fake.observations if o["name"] == "judge:verdict")
    assert annotation["as_type"] == "evaluator"
    assert annotation["output"]["verdict"] == "good"
    assert fake.trace_updates[0]["tags"] == ["judge:good"]
    names = [s["name"] for s in fake.scores]
    assert names == [
        "judge_strategy_fit",
        "judge_mechanic_choice",
        "judge_reward_fit",
        "judge_rationale_honesty",
        "judge_persona_consistency",
        "judge_actor_cooperation",
        "judge_verdict",
    ]
    numeric = next(s for s in fake.scores if s["name"] == "judge_strategy_fit")
    assert numeric["value"] == 1.0
    assert numeric["data_type"] == "NUMERIC"
    assert numeric["comment"].startswith("Solid incremental bakery re-buy")
    assert numeric["score_id"] == f"{numeric['trace_id']}-judge_strategy_fit"
    coop = next(s for s in fake.scores if s["name"] == "judge_actor_cooperation")
    assert coop["value"] == "consistent"
    assert coop["data_type"] == "CATEGORICAL"
    verdict_score = next(s for s in fake.scores if s["name"] == "judge_verdict")
    assert verdict_score["value"] == "good"
    assert verdict_score["data_type"] == "CATEGORICAL"


def test_write_judgements_json(tmp_path: Path) -> None:
    out = tmp_path / "verdicts.json"
    count = judge.write_judgements_json([_turn(_verdict()), _turn(None)], out)
    assert count == 2
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data[0]["verdict"]["verdict"] == "good"
    assert data[1]["verdict"] is None


def _profile_with_persona() -> ProfileTrace:
    profile = _profile()
    profile.snapshot.shopper_persona = {
        "full_name": "Игорь Пчёлкин",
        "age": 41,
        "occupation": "инженер",
        "promo_attitude": "не верит акциям, берёт своё",
        "what_they_ignore": "любые баллы и купоны",
        "voice": "Мне некогда, беру привычное и ухожу.",
    }
    return profile


def test_render_user_prompt_includes_persona_for_action_grounding() -> None:
    payload = json.loads(judge._render_user_prompt(_profile_with_persona()))
    persona = payload["shopper"]["persona"]
    assert persona["promo_attitude"].startswith("не верит")
    assert persona["what_they_ignore"] == "любые баллы и купоны"
    assert payload["branch_decisions"][0]["shopper_thinking"]


def test_judge_schema_matches_verdict_model() -> None:
    from app.ml import tool_schemas

    required = tool_schemas.judge_verdict_schema()["required"]
    assert required[0] == "planner_insights"
    for field in ("persona_insights", "persona_consistency", "actor_cooperation", "strategy_fit"):
        assert field in required
    assert "analysis" not in required
    assert set(required) == set(JudgeVerdict.model_fields)


def _proposals() -> JudgeProposals:
    return JudgeProposals(
        analysis="reward mismatch and staple targeting recur across the batch",
        proposals=[
            JudgeProposal(
                title="Reward too rich for skeptics",
                dimension="reward_fit",
                severity="high",
                problem="high points handed to promo-immune shoppers",
                proposal="cap points at none for promo_immune posture",
                evidence=[
                    ProposalEvidence(
                        profile_id="P0001", observation="promo_immune got points high"
                    ),
                    ProposalEvidence(
                        profile_id="P0002", observation="stable shopper got points high"
                    ),
                ],
            ),
            JudgeProposal(
                title="single-case noise",
                dimension="mechanic_choice",
                severity="low",
                problem="one odd mechanic pick",
                proposal="n/a",
                evidence=[
                    ProposalEvidence(profile_id="P0001", observation="a"),
                    ProposalEvidence(profile_id="P0001", observation="same profile again"),
                ],
            ),
            JudgeProposal(
                title="invented ids",
                dimension="strategy_fit",
                severity="medium",
                problem="hallucinated evidence",
                proposal="n/a",
                evidence=[
                    ProposalEvidence(profile_id="P9999", observation="a"),
                    ProposalEvidence(profile_id="P8888", observation="b"),
                ],
            ),
        ],
    )


def test_validate_proposals_requires_two_distinct_known_profiles() -> None:
    validated = judge._validate_proposals(_proposals(), {"P0001", "P0002"}, 2)
    assert [p.title for p in validated.proposals] == ["Reward too rich for skeptics"]
    assert len(validated.proposals[0].evidence) == 2


def test_verdict_tags_and_level_flag_off_persona_cooperation() -> None:
    bad = _verdict().model_copy(update={"verdict": "bad", "actor_cooperation": "too_cooperative"})
    assert judge._verdict_tags(bad) == ["judge:bad", "judge:too_cooperative"]
    assert judge._verdict_level(bad) == "ERROR"
    assert judge._verdict_tags(_verdict()) == ["judge:good"]
    assert judge._verdict_level(_verdict()) == "DEFAULT"


def test_proposal_digest_includes_scores_and_strategy() -> None:
    loaded = LoadedTraces(header=_header(), profiles=[_profile()])
    rows = json.loads(judge._proposal_digest(loaded, [_turn(_verdict())]))
    assert rows[0]["profile_id"] == "P0001"
    assert rows[0]["mechanic"] == "replenishment"
    assert rows[0]["scores"]["reward_fit"] == 3
    assert rows[0]["verdict"] == "good"


def test_write_proposals_json(tmp_path: Path) -> None:
    out = tmp_path / "proposals.json"
    count = judge.write_proposals_json(_proposals(), out)
    assert count == 3
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["proposals"][0]["dimension"] == "reward_fit"
    assert judge.write_proposals_json(None, tmp_path / "none.json") == 0


def test_push_proposals_creates_summary_trace(monkeypatch: Any) -> None:
    fake = _FakeClient()
    monkeypatch.setattr(judge.langfuse_export, "open_langfuse_client", lambda *a, **k: fake)
    loaded = LoadedTraces(header=_header(), profiles=[_profile()])
    validated = judge._validate_proposals(_proposals(), {"P0001", "P0002"}, 2)
    count = judge.push_proposals_to_langfuse(loaded, validated, "pk", "sk", "host")
    assert count == 1
    names = [o.get("name") for o in fake.observations]
    assert any(n and n.startswith("judge run summary") for n in names)
    assert any(n and n.startswith("proposal:") for n in names)
    assert "judge:summary" in fake.trace_updates[0]["tags"]
    assert "judge:high" in fake.trace_updates[0]["tags"]
    assert any(s["name"] == "judge_proposal_count" for s in fake.scores)
    assert fake.flushed is True


def test_proposals_schema_matches_model() -> None:
    from app.ml import tool_schemas

    required = tool_schemas.judge_proposals_schema()["required"]
    assert required[0] == "analysis"
    assert set(required) == set(JudgeProposals.model_fields)


def _verdict_variant(strat: int, coop: str, label: str) -> JudgeVerdict:
    base = _verdict().model_dump()
    base["strategy_fit"] = strat
    base["actor_cooperation"] = coop
    base["verdict"] = label
    return JudgeVerdict.model_validate(base)


def test_build_judge_summary_counts_and_means() -> None:
    turns = [
        judge.JudgeTurn(
            profile_id="P0000",
            segment="regular_mid",
            verdict=_verdict_variant(5, "consistent", "good"),
            call=_turn(_verdict()).call,
        ),
        judge.JudgeTurn(
            profile_id="P0001",
            segment="light",
            verdict=_verdict_variant(1, "too_cooperative", "bad"),
            call=_turn(_verdict()).call,
        ),
        _turn(None),
    ]
    agg = judge.build_judge_summary(turns)
    assert agg.profiles == 3
    assert agg.parsed == 2
    assert agg.verdict_good == 1
    assert agg.verdict_bad == 1
    assert agg.verdict_mixed == 0
    assert agg.coop_too_cooperative == 1
    assert agg.coop_consistent == 1
    assert agg.mean_strategy_fit == 3.0


def test_judge_summary_scores_flat_numeric() -> None:
    turns = [
        judge.JudgeTurn(
            profile_id="P0000",
            segment="regular_mid",
            verdict=_verdict_variant(4, "consistent", "mixed"),
            call=_turn(_verdict()).call,
        )
    ]
    scores = judge.judge_summary_scores(judge.build_judge_summary(turns))
    assert scores["judge_verdict_mixed_count"] == 1.0
    assert scores["judge_mean_strategy_fit"] == 4.0
    assert scores["judge_parsed_count"] == 1.0
    assert all(isinstance(v, float) for v in scores.values())
