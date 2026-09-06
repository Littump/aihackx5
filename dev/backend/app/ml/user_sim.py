import asyncio

from app.ml import config, llm_client, tool_schemas, tracing
from app.ml import product_knowledge as pk
from app.ml.llm_client import ChatClient
from app.ml.persona import Persona, render_persona_block
from app.ml.schemas import OfferResponse, PlannerInput, ShoppingHabit, UserProfile
from app.ml.tracing import ActorTurn, LlmCall

_SCHEMA_NAME = "offer_response"
_MAX_TOKENS = config.ACTOR_MAX_TOKENS

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
    persona: Persona | None = None,
) -> ActorTurn:
    if null_test or client is None:
        return ActorTurn(response=_NULL_RESPONSE.model_copy(), call=None)
    prompt_file = "user_sim_human_system.md" if persona is not None else "user_sim_system.md"
    system_prompt = llm_client.load_prompt(prompt_file)
    user_prompt = _render_user_prompt(
        profile, planner_input, offer_summary, tail_weeks, baseline_tail_visits, persona
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


def _render_user_prompt(
    profile: UserProfile,
    planner_input: PlannerInput,
    offer_summary: str,
    tail_weeks: int,
    baseline_tail_visits: int,
    persona: Persona | None = None,
) -> str:
    if persona is not None:
        return _render_human_prompt(profile, offer_summary, persona)
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


def _render_human_prompt(
    profile: UserProfile,
    offer_summary: str,
    persona: Persona,
) -> str:
    template = llm_client.load_prompt("user_sim_human_user.md")
    return template.format(
        persona_block=render_persona_block(persona),
        cadence_phrase=_cadence_phrase(profile.visits_per_week),
        avg_basket=f"{profile.avg_basket:.0f}",
        favorite_with_examples=_favorite_with_examples(profile.favorite_categories),
        offer_summary=offer_summary,
    )


def _cadence_phrase(visits_per_week: float) -> str:
    if visits_per_week >= 1.0:
        return f"примерно {visits_per_week:.0f} раз(а) в неделю"
    days = round(7.0 / visits_per_week) if visits_per_week > 0 else 0
    if days == 0:
        return "заходишь совсем редко, от случая к случаю"
    return f"примерно раз в {days} дней (реже раза в неделю)"


def _favorite_with_examples(favorite_categories: list[str]) -> str:
    parts = [f"{pk.category_ru(cat)} ({pk.category_examples(cat)})" for cat in favorite_categories]
    return "; ".join(parts)


def _parse_response(arguments: dict[str, object] | None) -> OfferResponse | None:
    if arguments is None:
        return None
    try:
        return OfferResponse.model_validate(arguments)
    except ValueError:
        return None


_CADENCE_PHRASE: dict[str, str] = {
    "staple": "берёшь почти в каждый заход, это твоя рутина",
    "lapsed": "раньше брал(а) регулярно, но подзабросил(а) — давно не было в корзине",
    "regular": "берёшь время от времени, не в каждый заход",
    "occasional": "берёшь изредка, по случаю",
}


def _habit_line(habit: ShoppingHabit) -> str:
    name = f"{pk.category_ru(habit.category)} ({pk.category_examples(habit.category)})"
    return f"  - {name} — {_CADENCE_PHRASE[habit.cadence_class]}"


def _life_in_numbers(profile: UserProfile, habits: list[ShoppingHabit]) -> str:
    if habits:
        habit_block = "\n".join(_habit_line(habit) for habit in habits)
    else:
        habit_block = f"  - {_favorite_with_examples(profile.favorite_categories)}"
    return (
        "ТВОЯ ОБЫЧНАЯ ЖИЗНЬ (это факт про тебя — важнее любого портрета выше; если портрет звучит "
        "так,\n"
        "будто ты берёшь что-то чаще, верь этим строкам, а не портрету, и не меняй их):\n"
        f"- В магазин ты ходишь {_cadence_phrase(profile.visits_per_week)}, "
        f"средний чек около {profile.avg_basket:.0f} ₽.\n"
        "- Что и как часто ты реально берёшь:\n"
        f"{habit_block}\n"
        "- Без предложений ты просто живёшь в своей колее — ходишь как обычно."
    )


def _persona_system(profile: UserProfile, persona: Persona, habits: list[ShoppingHabit]) -> str:
    base = llm_client.load_prompt("user_sim_human_system.md")
    return f"{base}\n\n{render_persona_block(persona)}\n\n{_life_in_numbers(profile, habits)}"


def _week_user_turn(
    week_number: int, offer_view: str, is_control: bool, challenge_active: bool
) -> str:
    if challenge_active:
        if is_control:
            head = f"НЕДЕЛЯ {week_number}. В приложении X5 массовая акция для всех:"
        else:
            head = f"НЕДЕЛЯ {week_number}. Вот что ты видишь в приложении X5 (Домовой):"
        return (
            f"{head}\n\n{offer_view}\n\n"
            "Ты правда полезешь это выполнять и поменяешь планы — "
            "или закроешь и пойдёшь как обычно? "
            "Порассуждай своими словами от первого лица в `thinking`, "
            "потом дай вердикт по схеме."
        )
    return (
        f"НЕДЕЛЯ {week_number}. Прошла ещё неделя, активных целей и акций в приложении нет — "
        "обычная жизнь. Что делаешь на этой неделе? Рассуждай в `thinking`, "
        "потом вердикт по схеме. "
        "Без активной цели честно ставь `buy_as_usual`/`ignore`, `extra_visits`=0."
    )


async def _weekly_turn(
    client: ChatClient,
    messages: list[dict[str, str]],
    attempt_label: str,
) -> ActorTurn:
    schema = tool_schemas.offer_response_schema()
    last_call: LlmCall | None = None
    for attempt in range(config.ACTOR_RETRY_MAX + 1):
        result = await client.emit_json_messages(
            messages, _SCHEMA_NAME, schema, max_tokens=_MAX_TOKENS
        )
        call = tracing.build_llm_call(
            role="actor",
            label=attempt_label,
            model=client.model,
            base_url=client.base_url,
            attempt=attempt,
            system_prompt=messages[0]["content"],
            user_prompt=messages[-1]["content"],
            result=result,
        )
        parsed = _parse_response(result.parsed)
        if parsed is not None:
            return ActorTurn(response=parsed, call=call)
        last_call = call
        if attempt < config.ACTOR_RETRY_MAX:
            await asyncio.sleep(config.ACTOR_RETRY_BACKOFF_S * (attempt + 1))
    return ActorTurn(response=_NULL_RESPONSE.model_copy(), call=last_call)


class WeeklyChat:
    def __init__(
        self,
        client: ChatClient | None,
        profile: UserProfile,
        persona: Persona,
        habits: list[ShoppingHabit],
        null_test: bool,
        label: str,
    ) -> None:
        self._client = client
        self._label = label
        self._null = null_test or client is None
        self._messages: list[dict[str, str]] = (
            []
            if self._null
            else [{"role": "system", "content": _persona_system(profile, persona, habits)}]
        )

    async def respond(
        self, week_number: int, offer_view: str, is_control: bool, challenge_active: bool
    ) -> ActorTurn:
        if self._null or self._client is None:
            return ActorTurn(response=_NULL_RESPONSE.model_copy(), call=None)
        self._messages.append(
            {
                "role": "user",
                "content": _week_user_turn(week_number, offer_view, is_control, challenge_active),
            }
        )
        turn = await _weekly_turn(self._client, self._messages, f"{self._label}_w{week_number}")
        self._messages.append({"role": "assistant", "content": _history_line(turn)})
        return turn


def _history_line(turn: ActorTurn) -> str:
    if turn.call is not None and turn.call.response_text is not None:
        return turn.call.response_text
    return turn.response.model_dump_json()
