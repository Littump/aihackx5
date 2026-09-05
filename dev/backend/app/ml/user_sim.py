import asyncio

from app.ml import config, llm_client, tool_schemas, tracing
from app.ml.llm_client import ChatClient
from app.ml.schemas import ChallengeOffer, OfferResponse, PlannerInput, UserProfile
from app.ml.tracing import ActorTurn, LlmCall

_SCHEMA_NAME = "offer_response"
_MAX_TOKENS = 700

_NULL_RESPONSE = OfferResponse(
    thinking="Null test: no offer effect is simulated for this shopper.",
    promo_decision="ignore",
    extra_visits=0,
    completed_challenge=False,
    rationale="offer ignored (null test)",
)

CONTROL_OFFER_SUMMARY = (
    "Обезличенная массовая акция X5: 10% кешбэк на весь чек этой недели, "
    "без персонализации под привычки покупателя."
)


async def offer_response(
    client: ChatClient | None,
    profile: UserProfile,
    planner_input: PlannerInput,
    offer_summary: str,
    tail_weeks: int,
    baseline_tail_visits: int,
    null_test: bool,
    label: str,
) -> ActorTurn:
    if null_test or client is None:
        return ActorTurn(response=_NULL_RESPONSE.model_copy(), call=None)
    system_prompt = llm_client.load_prompt("user_sim_system.md")
    user_prompt = _render_user_prompt(
        profile, planner_input, offer_summary, tail_weeks, baseline_tail_visits
    )
    schema = tool_schemas.offer_response_schema()
    last_call: LlmCall | None = None
    for attempt in range(config.ACTOR_RETRY_MAX + 1):
        result = await client.emit_json(
            system_prompt, user_prompt, _SCHEMA_NAME, schema, max_tokens=_MAX_TOKENS
        )
        call = tracing.build_llm_call(
            role="actor",
            label=label,
            model=client.model,
            base_url=client.base_url,
            attempt=attempt,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            result=result,
        )
        parsed = _parse_response(result.parsed)
        if parsed is not None:
            return ActorTurn(response=parsed, call=call)
        last_call = call
        if attempt < config.ACTOR_RETRY_MAX:
            await asyncio.sleep(config.ACTOR_RETRY_BACKOFF_S * (attempt + 1))
    return ActorTurn(response=_NULL_RESPONSE.model_copy(), call=last_call)


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
        archetype=profile.archetype,
        persona_brief=profile.persona_brief,
        deal_attitude=profile.deal_attitude,
        routine_rigidity=profile.routine_rigidity,
        visits_per_week=profile.visits_per_week,
        avg_basket=profile.avg_basket,
        promo_sensitivity=profile.promo_sensitivity,
        churn_risk=planner_input.features.churn_risk,
        favorite_categories=", ".join(profile.favorite_categories),
        tail_weeks=tail_weeks,
        baseline_tail_visits=baseline_tail_visits,
        offer_summary=offer_summary,
    )


def _parse_response(arguments: dict[str, object] | None) -> OfferResponse | None:
    if arguments is None:
        return None
    try:
        return OfferResponse.model_validate(arguments)
    except ValueError:
        return None
