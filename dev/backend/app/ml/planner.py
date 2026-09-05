import json
from typing import Any

from pydantic import ValidationError

from app.ml import config, llm_client, rules, tool_schemas, tracing, validator
from app.ml.llm_client import ChatClient
from app.ml.schemas import ChallengePlan, PlannerInput, ValidatedPlan
from app.ml.tracing import LlmCall

_SCHEMA_NAME = "challenge_plan"
_MAX_TOKENS = 700


async def plan_challenge(
    client: ChatClient | None,
    planner_input: PlannerInput,
    calls: list[LlmCall] | None = None,
) -> ValidatedPlan:
    if client is None:
        return _fallback(planner_input)
    system_prompt = llm_client.load_prompt("planner_system.md")
    base_user_prompt = _render_user_prompt(planner_input)
    schema = tool_schemas.challenge_plan_schema()
    feedback = ""
    for attempt in range(config.PLANNER_REPAIR_MAX + 1):
        user_prompt = base_user_prompt + feedback
        chat_result = await client.emit_json(
            system_prompt, user_prompt, _SCHEMA_NAME, schema, max_tokens=_MAX_TOKENS
        )
        if calls is not None:
            calls.append(
                tracing.build_llm_call(
                    role="planner",
                    label=f"planner_attempt_{attempt}",
                    model=client.model,
                    base_url=client.base_url,
                    attempt=attempt,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    result=chat_result,
                )
            )
        plan = _parse_plan(chat_result.parsed)
        if plan is None:
            feedback = "\n\nPrevious answer was not valid JSON for the schema. Try again."
            continue
        result = validator.validate_plan(plan, planner_input)
        if result.ok:
            return validator.finalize_plan(result.normalized, planner_input, "llm", attempt)
        feedback = "\n\nYour previous plan failed validation:\n- " + "\n- ".join(result.errors)
    return _fallback(planner_input)


def _fallback(planner_input: PlannerInput) -> ValidatedPlan:
    plan = rules.fallback_plan(planner_input)
    return validator.finalize_plan(plan, planner_input, "rules", 0)


def _parse_plan(arguments: dict[str, Any] | None) -> ChallengePlan | None:
    if arguments is None:
        return None
    try:
        return ChallengePlan.model_validate(arguments)
    except ValidationError:
        return None


def _render_user_prompt(planner_input: PlannerInput) -> str:
    template = llm_client.load_prompt("planner_user.md")
    insight_json = json.dumps(_compact_insight(planner_input), ensure_ascii=False, indent=2)
    return template.format(
        insight_json=insight_json,
        library=", ".join(planner_input.challenge_library),
    )


def _compact_insight(planner_input: PlannerInput) -> dict[str, Any]:
    return {
        "user": planner_input.user.model_dump(),
        "features": planner_input.features.model_dump(),
        "category_timeseries": [
            series.model_dump() for series in planner_input.category_timeseries
        ],
        "previous_plans": [plan.model_dump() for plan in planner_input.previous_plans],
        "catalog": [
            {
                "sku_id": item.sku_id,
                "name": item.name,
                "category": item.category,
                "regular_price": item.regular_price,
            }
            for item in planner_input.catalog
        ],
    }
