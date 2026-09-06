from typing import Any

from app.ml import config


def challenge_plan_schema() -> dict[str, Any]:
    category_enum: list[Any] = [
        category for category in config.CATEGORIES if category not in config.EXCLUDED_CATEGORIES
    ]
    lapsed_keywords = [f"{category}_lapsed" for category in category_enum]
    keyword_enum = [*config.LIFECYCLE_KEYWORDS, *config.MODIFIER_KEYWORDS, *lapsed_keywords]
    challenge_category_enum: list[Any] = [*category_enum, None]
    reward = {
        "type": "object",
        "additionalProperties": False,
        "required": ["xp_level", "points_level"],
        "properties": {
            "xp_level": {
                "type": "string",
                "enum": list(config.XP_LEVELS),
                "description": "XP stage; always granted, off-budget",
            },
            "points_level": {
                "type": "string",
                "enum": list(config.POINTS_LEVELS),
                "description": "X5 points stage; none unless the budget and posture allow it",
            },
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "thinking",
            "classification",
            "goal",
            "insights",
            "challenges",
            "general_strategy",
        ],
        "properties": {
            "thinking": {
                "type": "string",
                "maxLength": 1500,
                "description": "private reasoning trace; name the buyer, then pick the goal",
            },
            "classification": {
                "type": "object",
                "additionalProperties": False,
                "required": ["keywords", "label", "description", "evidence", "posture"],
                "properties": {
                    "keywords": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 5,
                        "items": {"type": "string", "enum": keyword_enum},
                        "description": (
                            "exactly one lifecycle keyword "
                            "(rising|steady|cooling|dormant) first, then 1..4 modifier "
                            "keywords; never use a second lifecycle word as a modifier"
                        ),
                    },
                    "label": {
                        "type": "string",
                        "maxLength": 140,
                        "description": "short Title-Case buyer name composed from the keywords",
                    },
                    "description": {
                        "type": "string",
                        "maxLength": 280,
                        "description": "one internal sentence grounded in real numbers",
                    },
                    "evidence": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "metric behind each non-obvious keyword",
                    },
                    "posture": {
                        "type": "string",
                        "enum": list(config.POSTURES),
                        "description": "price attitude from promo_sensitivity",
                    },
                    "is_ambiguous": {
                        "type": "boolean",
                        "description": "true if the shopper sits on a lifecycle boundary",
                    },
                },
            },
            "goal": {
                "type": "object",
                "additionalProperties": False,
                "required": ["target", "proxy", "direction", "rationale"],
                "properties": {
                    "target": {
                        "type": "string",
                        "enum": list(config.GOAL_TARGETS),
                        "description": "the one business feature to move",
                    },
                    "proxy": {
                        "type": "string",
                        "enum": list(config.GOAL_PROXIES),
                        "description": "the lever that serves the target, or none",
                    },
                    "direction": {
                        "type": "string",
                        "enum": list(config.GOAL_DIRECTIONS),
                        "description": "increase / recover / sustain",
                    },
                    "rationale": {
                        "type": "string",
                        "maxLength": 300,
                        "description": "must cite the metric behind the target and proxy",
                    },
                },
            },
            "insights": {
                "type": "array",
                "minItems": config.MIN_INSIGHTS,
                "maxItems": config.MAX_INSIGHTS,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "name",
                        "kind",
                        "behaviour",
                        "dod",
                        "strategy_hint",
                        "evidence_metric",
                    ],
                    "properties": {
                        "name": {
                            "type": "string",
                            "maxLength": 60,
                            "description": "snake_case name following the kind convention",
                        },
                        "kind": {
                            "type": "string",
                            "enum": list(config.INSIGHT_KINDS),
                            "description": "one fixed insight kind; do not repeat a kind",
                        },
                        "behaviour": {"type": "string", "maxLength": 220},
                        "dod": {"type": "string", "maxLength": 200},
                        "strategy_hint": {"type": "string", "maxLength": 200},
                        "evidence_metric": {
                            "type": "string",
                            "maxLength": 90,
                            "description": "a real metric=value from the insight input",
                        },
                    },
                },
            },
            "challenges": {
                "type": "array",
                "minItems": 1,
                "maxItems": config.MAX_CHALLENGES,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "role",
                        "insight_ref",
                        "challenge_type",
                        "category",
                        "target",
                        "reward",
                        "rationale",
                    ],
                    "properties": {
                        "role": {
                            "type": "string",
                            "enum": ["hero", "side"],
                            "description": "exactly one hero; the rest are side quests",
                        },
                        "insight_ref": {
                            "type": "string",
                            "maxLength": 60,
                            "description": "must equal one instantiated insight name",
                        },
                        "challenge_type": {
                            "type": "string",
                            "enum": list(config.CHALLENGE_LIBRARY),
                            "description": "mechanic from the fixed library",
                        },
                        "category": {
                            "type": ["string", "null"],
                            "enum": challenge_category_enum,
                            "description": "macro category or null for pure frequency",
                        },
                        "target": {
                            "type": "integer",
                            "minimum": 1,
                            "description": "small step above baseline; code clamps the corridor",
                        },
                        "reward": reward,
                        "rationale": {
                            "type": "string",
                            "maxLength": 240,
                            "description": "must cite a real number from the insight",
                        },
                    },
                },
            },
            "general_strategy": {
                "type": "object",
                "additionalProperties": False,
                "required": ["insight_refs", "rationale"],
                "properties": {
                    "insight_refs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "must cover exactly all instantiated insight names",
                    },
                    "rationale": {"type": "string", "maxLength": 400},
                    "next_week_hint": {"type": "string", "maxLength": 240},
                },
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


def judge_verdict_schema() -> dict[str, Any]:
    score_field = {
        "type": "integer",
        "minimum": 1,
        "maximum": 5,
        "description": "1=fails 2=weak 3=ok 4=good 5=excellent; be strict and cite evidence",
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "planner_insights",
            "persona_insights",
            "strategy_fit",
            "mechanic_choice",
            "reward_fit",
            "rationale_honesty",
            "persona_consistency",
            "actor_cooperation",
            "verdict",
            "summary",
        ],
        "properties": {
            "planner_insights": _insight_array(
                "2..5 DISCRETE findings about the PLANNER (the challenge design). Each is one "
                "aspect (strategy_fit / mechanic_choice / reward_fit / rationale_honesty), one "
                "concrete observation citing a real number or field, plus severity. No walls."
            ),
            "persona_insights": _insight_array(
                "2..5 DISCRETE findings about the SYNTHETIC SHOPPER (the actor) across the three "
                "branches. Each is one aspect (in_character / over_cooperation / effort_realism), "
                "one concrete observation quoting the shopper's decision+thinking, and a severity."
            ),
            "strategy_fit": {
                **score_field,
                "description": (
                    "planner: does the hero challenge target an INCREMENTAL visit/basket, not a "
                    "staple bought every trip? 5=clearly incremental lapsed/headroom target; "
                    "3=partly incremental; 1=pays for an existing staple"
                ),
            },
            "mechanic_choice": {
                **score_field,
                "description": (
                    "planner: is challenge_type justified by the shopper's strongest signal "
                    "(lapsed category / frequency headroom / churn win-back)? "
                    "5=mechanic matches the dominant signal; 1=mechanic ignores it"
                ),
            },
            "reward_fit": {
                **score_field,
                "description": (
                    "planner: does reward match posture and churn_risk? penalise high points to "
                    "a promo-immune/stable shopper and token rewards to a high-churn one. "
                    "5=calibrated; 1=miscalibrated"
                ),
            },
            "rationale_honesty": {
                **score_field,
                "description": (
                    "planner: do goal/challenge rationales cite a REAL number from the insight "
                    "(recency, cadence, days_overdue, baseline, overdue_ratio)? "
                    "5=concrete numbers; 3=one vague number; 1=no number / invented claim"
                ),
            },
            "persona_consistency": {
                **score_field,
                "description": (
                    "actor: across all branches, do the shopper's decision + thinking match their "
                    "documented personality (deal_attitude, promo_attitude, what_they_ignore, "
                    "routine_rigidity, favorite_categories, churn_risk)? "
                    "5=fully in character; 3=minor drift; 1=out of character"
                ),
            },
            "actor_cooperation": {
                "type": "string",
                "enum": ["too_cooperative", "consistent", "too_resistant"],
                "description": (
                    "over-cooperation check: `too_cooperative` if the shopper uses/completes "
                    "an offer a skeptic of this profile would ignore or buy_as_usual (sycophantic "
                    "compliance); `too_resistant` if they reject an offer that clearly fits; "
                    "`consistent` if engagement level matches the persona"
                ),
            },
            "verdict": {
                "type": "string",
                "enum": ["good", "mixed", "bad"],
                "description": "overall judgement of the LLM challenge for this shopper",
            },
            "summary": {
                "type": "string",
                "maxLength": 400,
                "description": (
                    "one short verdict line tying the planner and persona insights together; "
                    "no re-listing, just the bottom line"
                ),
            },
        },
    }


def _insight_array(description: str) -> dict[str, Any]:
    return {
        "type": "array",
        "minItems": 2,
        "maxItems": 5,
        "description": description,
        "items": {
            "type": "object",
            "additionalProperties": False,
            "required": ["aspect", "observation", "severity"],
            "properties": {
                "aspect": {
                    "type": "string",
                    "maxLength": 48,
                    "description": "short label for the finding (one dimension)",
                },
                "observation": {
                    "type": "string",
                    "maxLength": 240,
                    "description": "evidence-bound observation citing a real number or field",
                },
                "severity": {
                    "type": "string",
                    "enum": ["good", "concern", "critical"],
                    "description": "good=works, concern=weak, critical=clearly wrong",
                },
            },
        },
    }


def judge_proposals_schema() -> dict[str, Any]:
    evidence_item = {
        "type": "object",
        "additionalProperties": False,
        "required": ["profile_id", "observation"],
        "properties": {
            "profile_id": {
                "type": "string",
                "description": (
                    "id of a profile in the batch (e.g. P0007) where this pattern appears"
                ),
            },
            "observation": {
                "type": "string",
                "maxLength": 280,
                "description": (
                    "one concrete detail from THAT profile proving the pattern holds there"
                ),
            },
        },
    }
    proposal_item = {
        "type": "object",
        "additionalProperties": False,
        "required": ["title", "dimension", "severity", "problem", "proposal", "evidence"],
        "properties": {
            "title": {
                "type": "string",
                "maxLength": 120,
                "description": "short name of the systemic pattern",
            },
            "dimension": {
                "type": "string",
                "enum": [
                    "strategy_fit",
                    "mechanic_choice",
                    "reward_fit",
                    "rationale_honesty",
                    "persona_consistency",
                    "actor_cooperation",
                ],
                "description": "which failure axis this pattern lives on",
            },
            "severity": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "high=wastes budget or breaks realism widely; low=minor",
            },
            "problem": {
                "type": "string",
                "maxLength": 600,
                "description": (
                    "the recurring failure, stated as a pattern across profiles, not one case"
                ),
            },
            "proposal": {
                "type": "string",
                "maxLength": 600,
                "description": "a concrete, actionable fix to the planner or actor prompt/rules",
            },
            "evidence": {
                "type": "array",
                "minItems": 2,
                "maxItems": 6,
                "items": evidence_item,
                "description": (
                    "at least two DIFFERENT profiles where this pattern is proven; "
                    "cite real profile_ids"
                ),
            },
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["analysis", "proposals"],
        "properties": {
            "analysis": {
                "type": "string",
                "maxLength": 1600,
                "description": (
                    "cluster the per-profile verdicts: name the failure axes that recur, "
                    "then for each "
                    "candidate pattern list which profile_ids show it BEFORE writing "
                    "proposals; keep only "
                    "patterns you can back with >=2 distinct profiles"
                ),
            },
            "proposals": {
                "type": "array",
                "maxItems": 8,
                "items": proposal_item,
                "description": (
                    "systemic proposals, each proven across at least two distinct profiles"
                ),
            },
        },
    }


def persona_schema() -> dict[str, Any]:
    text = {"type": "string", "minLength": 1}
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "full_name",
            "age",
            "occupation",
            "income_band",
            "household",
            "city_type",
            "neighborhood_context",
            "life_context",
            "money_mindset",
            "promo_attitude",
            "loyalty_app_habit",
            "store_relationship",
            "jobs_to_be_done",
            "shopping_routine",
            "favorite_food_story",
            "quirks",
            "what_makes_them_engage",
            "what_they_ignore",
            "voice",
        ],
        "properties": {
            "full_name": {"type": "string", "description": "Russian first name + surname"},
            "age": {"type": "integer", "minimum": 16, "maximum": 90},
            "occupation": text,
            "income_band": text,
            "household": text,
            "city_type": text,
            "neighborhood_context": text,
            "life_context": text,
            "money_mindset": text,
            "promo_attitude": text,
            "loyalty_app_habit": text,
            "store_relationship": text,
            "jobs_to_be_done": {
                "type": "array",
                "items": text,
                "minItems": 2,
                "maxItems": 4,
            },
            "shopping_routine": text,
            "favorite_food_story": text,
            "quirks": {
                "type": "array",
                "items": text,
                "minItems": 2,
                "maxItems": 4,
            },
            "what_makes_them_engage": text,
            "what_they_ignore": text,
            "voice": {
                "type": "string",
                "minLength": 1,
                "description": "one first-person paragraph in the shopper's own voice",
            },
        },
    }
