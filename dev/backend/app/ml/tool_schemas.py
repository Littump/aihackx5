from typing import Any

from app.ml import config


def challenge_plan_schema() -> dict[str, Any]:
    category_enum: list[Any] = [
        category for category in config.CATEGORIES if category not in config.EXCLUDED_CATEGORIES
    ]
    category_enum.append(None)
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["steps", "insight_used", "rationale"],
        "properties": {
            "steps": {
                "type": "array",
                "minItems": 1,
                "maxItems": config.MAX_PLAN_STEPS,
                "description": "1..MAX_PLAN_STEPS steps; only steps[0] is shown to the user",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "challenge_type",
                        "target",
                        "category",
                        "sku_refs",
                        "reward_kind",
                        "reward_level",
                        "deadline_days",
                    ],
                    "properties": {
                        "challenge_type": {
                            "type": "string",
                            "enum": list(config.CHALLENGE_LIBRARY),
                            "description": "mechanic from the fixed library",
                        },
                        "target": {
                            "type": "integer",
                            "minimum": 1,
                            "description": "weekly target; code validates the corridor vs baseline",
                        },
                        "category": {
                            "type": ["string", "null"],
                            "enum": category_enum,
                            "description": "macro category or null",
                        },
                        "sku_refs": {
                            "type": "array",
                            "items": {"type": "string"},
                            "maxItems": 3,
                            "description": "sku_id values taken from the provided catalog",
                        },
                        "reward_kind": {
                            "type": "string",
                            "enum": list(config.REWARD_KINDS),
                            "description": "promo=money, ladder=bonus XP, none=self-rewarding",
                        },
                        "reward_level": {
                            "type": "string",
                            "enum": list(config.REWARD_LEVELS),
                            "description": "reward stage; code computes the amount, not you",
                        },
                        "deadline_days": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 14,
                            "description": "code clamps to the week bounds",
                        },
                    },
                },
            },
            "insight_used": {
                "type": "array",
                "items": {"type": "string"},
                "description": "insight feature keys actually used",
            },
            "rationale": {
                "type": "string",
                "maxLength": 200,
                "description": "explanation referencing a number from the insight",
            },
        },
    }


def offer_response_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "thinking",
            "promo_decision",
            "extra_visits",
            "completed_challenge",
            "rationale",
        ],
        "properties": {
            "thinking": {
                "type": "string",
                "maxLength": 1200,
                "description": (
                    "First-person reasoning AS this shopper: weigh the offer against what you "
                    "actually buy, the effort of extra trips, and whether the reward is worth "
                    "breaking your routine. Buying as usual is the honest default. "
                    "Fill this BEFORE deciding."
                ),
            },
            "promo_decision": {
                "type": "string",
                "enum": ["use_offer", "buy_as_usual", "ignore"],
                "description": (
                    "verdict: use_offer=you change behaviour to chase this challenge; "
                    "buy_as_usual=you keep shopping exactly as before, offer changes nothing; "
                    "ignore=irrelevant, you do not even consider it"
                ),
            },
            "extra_visits": {
                "type": "integer",
                "minimum": 0,
                "maximum": 6,
                "description": (
                    "extra store visits over the whole tail caused ONLY by the offer; 0 unless "
                    "promo_decision=use_offer; a real person rarely adds more than 1-2"
                ),
            },
            "completed_challenge": {
                "type": "boolean",
                "description": (
                    "true only if your normal cadence plus the extra visits actually reaches the "
                    "challenge target before the deadline"
                ),
            },
            "rationale": {
                "type": "string",
                "maxLength": 400,
                "description": "one-sentence justification of the verdict in the shopper's voice",
            },
        },
    }
