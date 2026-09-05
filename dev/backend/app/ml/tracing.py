from typing import Any

from pydantic import BaseModel, Field

from app.ml.llm_client import ChatResult
from app.ml.schemas import Branch, OfferResponse, PromoDecision, UserProfile

LlmRole = str


class LlmCall(BaseModel):
    role: LlmRole
    label: str
    model: str
    base_url: str
    attempt: int
    system_prompt: str
    user_prompt: str
    response_text: str | None
    parsed: dict[str, Any] | None
    parse_ok: bool


class ActorDecision(BaseModel):
    promo_decision: PromoDecision
    engaged: bool
    extra_visits: int
    completed_challenge: bool
    thinking: str
    rationale: str
    source: str


class ActorTurn(BaseModel):
    response: OfferResponse
    call: LlmCall | None


class BranchTrace(BaseModel):
    branch: Branch
    offer_summary: str
    plan_source: str
    relevance_hit: bool
    decision: ActorDecision
    incremental_visits: int
    reward_cost_rub: float
    net_effect_rub: float
    llm_call: LlmCall | None


class ProfileSnapshot(BaseModel):
    profile_id: str
    segment: str
    persona_label: str
    archetype: str
    deal_attitude: str
    routine_rigidity: float
    visits_per_week: float
    avg_basket: float
    promo_sensitivity: float
    favorite_categories: list[str]
    churn_risk: str


class ProfileTrace(BaseModel):
    snapshot: ProfileSnapshot
    plan_source: str
    planner_calls: list[LlmCall] = Field(default_factory=list)
    branches: list[BranchTrace] = Field(default_factory=list)


class EvalRunHeader(BaseModel):
    seed: int
    profiles: int
    horizon_weeks: int
    cut_week: int
    planner_model: str
    actor_model: str
    null_test: bool
    no_llm: bool


class TraceRecorder:
    def __init__(self, header: EvalRunHeader) -> None:
        self.header = header
        self._profiles: list[ProfileTrace] = []

    def add_profile(self, trace: ProfileTrace) -> None:
        self._profiles.append(trace)

    def profiles(self) -> list[ProfileTrace]:
        return sorted(self._profiles, key=lambda item: item.snapshot.profile_id)

    def to_jsonl(self) -> str:
        lines = [self.header.model_dump_json()]
        lines.extend(trace.model_dump_json() for trace in self.profiles())
        return "\n".join(lines) + "\n"


def build_llm_call(
    role: LlmRole,
    label: str,
    model: str,
    base_url: str,
    attempt: int,
    system_prompt: str,
    user_prompt: str,
    result: ChatResult,
) -> LlmCall:
    return LlmCall(
        role=role,
        label=label,
        model=model,
        base_url=base_url,
        attempt=attempt,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_text=result.raw_text,
        parsed=result.parsed,
        parse_ok=result.parsed is not None,
    )


def actor_decision(response: OfferResponse, source: str) -> ActorDecision:
    return ActorDecision(
        promo_decision=response.promo_decision,
        engaged=response.engaged,
        extra_visits=response.extra_visits,
        completed_challenge=response.completed_challenge,
        thinking=response.thinking,
        rationale=response.rationale,
        source=source,
    )


def profile_snapshot(profile: UserProfile, churn_risk: str) -> ProfileSnapshot:
    return ProfileSnapshot(
        profile_id=profile.profile_id,
        segment=profile.segment,
        persona_label=profile.persona_label,
        archetype=profile.archetype,
        deal_attitude=profile.deal_attitude,
        routine_rigidity=profile.routine_rigidity,
        visits_per_week=profile.visits_per_week,
        avg_basket=profile.avg_basket,
        promo_sensitivity=profile.promo_sensitivity,
        favorite_categories=profile.favorite_categories,
        churn_risk=churn_risk,
    )
