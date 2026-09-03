from typing import Any

from pydantic import ValidationError

from app.ml import llm_client, tool_schemas
from app.ml.llm_client import QwenClient
from app.ml.schemas import ChallengeOffer, OfferResponse, PlannerInput, UserProfile

_TOOL_NAME = "emit_offer_response"

_NULL_RESPONSE = OfferResponse(
    engaged=False, extra_visits=0, completed_challenge=False, reason="offer ignored (null test)"
)

CONTROL_OFFER_SUMMARY = (
    "Обезличенная массовая акция X5: 10% кешбэк на весь чек этой недели, "
    "без персонализации под привычки покупателя."
)


async def offer_response(
    client: QwenClient | None,
    profile: UserProfile,
    planner_input: PlannerInput,
    offer_summary: str,
    tail_weeks: int,
    baseline_tail_visits: int,
    null_test: bool,
) -> OfferResponse:
    if null_test or client is None:
        return _NULL_RESPONSE.model_copy()
    system_prompt = llm_client.load_prompt("user_sim_system.md")
    user_prompt = _render_user_prompt(
        profile, planner_input, offer_summary, tail_weeks, baseline_tail_visits
    )
    arguments = await client.emit_tool(
        system_prompt, user_prompt, _TOOL_NAME, tool_schemas.offer_response_schema(), max_tokens=300
    )
    parsed = _parse_response(arguments)
    return parsed if parsed is not None else _NULL_RESPONSE.model_copy()


def offer_summary_for(offer: ChallengeOffer) -> str:
    category = offer.category or "любая категория"
    skus = f", товары {offer.sku_refs}" if offer.sku_refs else ""
    return (
        f"Персональный челлендж от ИИ: тип {offer.challenge_type}, {category}, "
        f"цель {offer.target} за {offer.deadline_days} дней, "
        f"награда {offer.reward.reward_kind}/{offer.reward.reward_level}{skus}. "
        f"Обоснование: {offer.rationale}"
    )


def _render_user_prompt(
    profile: UserProfile,
    planner_input: PlannerInput,
    offer_summary: str,
    tail_weeks: int,
    baseline_tail_visits: int,
) -> str:
    template = llm_client.load_prompt("user_sim_user.md")
    return template.format(
        persona_label=profile.persona_label,
        segment=profile.segment,
        visits_per_week=profile.visits_per_week,
        avg_basket=profile.avg_basket,
        promo_sensitivity=profile.promo_sensitivity,
        churn_risk=planner_input.features.churn_risk,
        tail_weeks=tail_weeks,
        baseline_tail_visits=baseline_tail_visits,
        offer_summary=offer_summary,
    )


def _parse_response(arguments: dict[str, Any] | None) -> OfferResponse | None:
    if arguments is None:
        return None
    try:
        return OfferResponse.model_validate(arguments)
    except ValidationError:
        return None
