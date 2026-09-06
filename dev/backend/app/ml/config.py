import os

from app import game_rules

LLM_QWEN_BASE_URL_DEFAULT = "http://localhost:8016/v1"
LLM_QWEN_MODEL_DEFAULT = "qwen38-27b-fp8"

# Persona node: config holds a localhost placeholder; real host lives in local .env / CLI flags.
LLM_PERSONA_BASE_URL_DEFAULT = "http://localhost:8080/v1"
LLM_PERSONA_MODEL_DEFAULT = "MiniMaxAI/MiniMax-M3-MXFP8"
PERSONA_BASE_URL_DEFAULT = LLM_PERSONA_BASE_URL_DEFAULT
PERSONA_MODEL_DEFAULT = LLM_PERSONA_MODEL_DEFAULT

# Planner (rewards) = cheap Qwen; actor (shopper actions) = MiniMax persona node.
PLANNER_BASE_URL_DEFAULT = LLM_QWEN_BASE_URL_DEFAULT
PLANNER_MODEL_DEFAULT = LLM_QWEN_MODEL_DEFAULT
ACTOR_BASE_URL_DEFAULT = LLM_PERSONA_BASE_URL_DEFAULT
ACTOR_MODEL_DEFAULT = LLM_PERSONA_MODEL_DEFAULT

LANGFUSE_HOST_DEFAULT = "http://localhost:3000"
LANGFUSE_PUBLIC_KEY_DEFAULT = "pk-lf-domovoy-local"
LANGFUSE_SECRET_KEY_DEFAULT = "sk-lf-domovoy-local"

LLM_TIMEOUT_S = 180.0
ACTOR_RETRY_MAX = 2
ACTOR_RETRY_BACKOFF_S = 0.75
ACTOR_MAX_TOKENS = 4000
JUDGE_MAX_TOKENS = 1500
JUDGE_META_MAX_TOKENS = 6000
JUDGE_MIN_EVIDENCE_PROFILES = 2
EVAL_MAX_CONCURRENCY = 3

# Actor node capacity throttle (estimated from the SGLang /metrics of the actor endpoint).
ACTOR_MAX_CONCURRENCY = 3
NODE_OCCUPANCY_CEILING = 0.30
NODE_PRECHECK_MAX_OCCUPANCY = 0.50
NODE_RUNNING_CAPACITY = 32
CAPACITY_POLL_INTERVAL_S = 3.0
CAPACITY_WAIT_TIMEOUT_S = 600.0
CAPACITY_METRICS_TIMEOUT_S = 5.0

PERSONA_TIMEOUT_S = 600.0
PERSONA_TEMPERATURE = 1.0
PERSONA_TOP_P = 0.95
PERSONA_MAX_TOKENS = 12000
PERSONA_ENABLE_THINKING = True
PERSONA_MAX_CONCURRENCY = 2
PERSONA_RETRY_MAX = 2
PERSONA_RETRY_BACKOFF_S = 1.0

CATEGORIES: tuple[str, ...] = game_rules.CATEGORIES
EXCLUDED_CATEGORIES: frozenset[str] = game_rules.CHALLENGE_EXCLUDED_CATEGORIES

# Planner v2: five canonical challenge mechanics (no `streak` — that is an XP/league rail).
CHALLENGE_LIBRARY: tuple[str, ...] = (
    "frequency",
    "category",
    "basket",
    "replenishment",
    "collection",
)

LIFECYCLE_KEYWORDS: tuple[str, ...] = ("rising", "steady", "cooling", "dormant")
MODIFIER_KEYWORDS: tuple[str, ...] = (
    "formerly_active",
    "has_headroom",
    "at_ceiling",
    "large_basket",
    "small_basket",
    "broad",
    "day_to_day",
)
POSTURES: tuple[str, ...] = ("promo_immune", "value_selective", "deal_driven")
GOAL_TARGETS: tuple[str, ...] = ("visit_frequency", "basket_value")
GOAL_PROXIES: tuple[str, ...] = (
    "lapsed_category_rebuy",
    "add_category",
    "high_margin_category",
    "none",
)
GOAL_DIRECTIONS: tuple[str, ...] = ("increase", "recover", "sustain")
XP_LEVELS: tuple[str, ...] = ("low", "medium", "high")
POINTS_LEVELS: tuple[str, ...] = ("none", "low", "medium", "high")
INSIGHT_KINDS: tuple[str, ...] = (
    "lapsed_category",
    "momentum_ride",
    "visit_headroom",
    "churn_drift",
    "dormant_gap",
    "basket_depth",
    "high_margin_push",
    "streak_continuity",
    "reward_posture",
    "staple_avoid",
)
ACTION_INSIGHT_KINDS: frozenset[str] = frozenset(
    {
        "lapsed_category",
        "momentum_ride",
        "visit_headroom",
        "churn_drift",
        "dormant_gap",
        "basket_depth",
        "high_margin_push",
    }
)

# Reward mix: XP is always on and off-budget; X5 points are budget-gated (Part 2.5).
POINTS_LEVEL_SHARE: dict[str, float] = {"none": 0.0, "low": 0.4, "medium": 0.7, "high": 1.0}
XP_LEVEL_MULTIPLIER: dict[str, float] = {"low": 1.0, "medium": 1.5, "high": 2.0}
POSTURE_MAX_POINTS_LEVEL: dict[str, str] = {
    "promo_immune": "none",
    "value_selective": "medium",
    "deal_driven": "high",
}
POSTURE_PROMO_CUTS: tuple[float, float] = (0.35, 0.62)
PROMO_IMMUNE_CHURN_POINTS_LEVEL = "low"

# Derived-signal windows and bars (Part 1b / Part 2.1); mirrored by rules and the prompt.
DERIVED_WINDOW_DAYS = 28
VISIT_CEILING = 3.0
FREQUENCY_MECHANIC_MIN_PER_WEEK = 2.0
BASKET_REFERENCE = 600.0
MOMENTUM_RISING = 1.15
MOMENTUM_FORMERLY_ACTIVE = 0.7
OVERDUE_COOLING_MIN = 1.2
OVERDUE_DORMANT = 2.6
CADENCE_REGULARITY_STEADY = 0.6
HEADROOM_HAS_ROOM = 0.3
HEADROOM_AT_CEILING = 0.15
HEADROOM_ACTIVE_RECENCY_DAYS = 21
BASKET_LARGE_INDEX = 1.2
BASKET_SMALL_INDEX = 0.7
CATEGORY_BROAD_MIN = 3
CATEGORY_MIN_SHARE = 0.10
CATEGORY_MIN_VISITS = 3
STAPLE_SHARE_MIN = 0.35
STAPLE_MIN_VISITS = 2
TOP_CATEGORY_OVERDUE_MIN = 2.0
AMBIGUOUS_BOUNDARY_BAND = 0.15

CHURN_RISK_CADENCE_FACTOR = 1.8
CHURN_RISK_HIGH_FACTOR = 2.6

MAX_CHALLENGES = 3
CHALLENGE_DEADLINE_DAYS = 7
MAX_INSIGHTS = 4
MIN_INSIGHTS = 2
PLANNER_REPAIR_MAX = 2
PLANNER_PREV_PLANS_MAX = 3
PLANNER_TIMESERIES_TOP_K = 5

# High-margin mandate (A/B toggle): when on, a plan must include one high-margin challenge.
CATEGORY_CONTRIBUTION_MARGIN: dict[str, float] = dict(game_rules.CATEGORY_CONTRIBUTION_MARGIN)
HIGH_MARGIN_MIN_MARGIN = game_rules.HIGH_MARGIN_MIN_MARGIN
HIGH_MARGIN_CATEGORIES: tuple[str, ...] = tuple(
    category
    for category in CATEGORIES
    if category not in EXCLUDED_CATEGORIES
    and CATEGORY_CONTRIBUTION_MARGIN.get(category, 0.0) >= HIGH_MARGIN_MIN_MARGIN
)


def _env_flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


HIGH_MARGIN_MANDATE_ENABLED = _env_flag("ML_HIGH_MARGIN_MANDATE_ENABLED", True)

CATALOG_MIN_PER_CATEGORY = 18
CATALOG_MAX_PER_CATEGORY = 34

INFRA_COST_PER_USER_MONTH_RUB = 1.5
BUSINESS_METRIC_PURCHASES = 8
BUSINESS_METRIC_WINDOW_WEEKS = 4
RELEVANCE_HIT_THRESHOLD = 0.70

CONTRIBUTION_MARGIN = game_rules.CONTRIBUTION_MARGIN
REWARD_SHARE_MAX = game_rules.REWARD_SHARE_MAX
REWARD_POINTS_MIN = game_rules.REWARD_POINTS_MIN
REWARD_POINTS_MAX_WEEKLY = game_rules.REWARD_POINTS_MAX_WEEKLY
REWARD_POINTS_ROUNDING_STEP = game_rules.REWARD_POINTS_ROUNDING_STEP
XP_CHALLENGE = game_rules.XP_CHALLENGE


def high_margin_categories() -> frozenset[str]:
    return frozenset(HIGH_MARGIN_CATEGORIES)


def is_high_margin(category: str | None) -> bool:
    if category is None:
        return False
    return category in HIGH_MARGIN_CATEGORIES


def points_ceiling(posture: str, churn_risk: str) -> str:
    if posture == "promo_immune" and churn_risk in ("elevated", "high"):
        return PROMO_IMMUNE_CHURN_POINTS_LEVEL
    return POSTURE_MAX_POINTS_LEVEL[posture]
