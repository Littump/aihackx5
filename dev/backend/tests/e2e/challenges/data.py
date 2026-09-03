from datetime import UTC, datetime

from psycopg.types.json import Jsonb

NOW = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)

CHALLENGE_FIELDS = {
    "id",
    "type",
    "category",
    "status",
    "is_hero",
    "baseline",
    "target",
    "progress",
    "period_start",
    "period_end",
    "reward_xp",
    "reward_points",
    "title",
    "body",
}
CHALLENGE_DETAIL_FIELDS = CHALLENGE_FIELDS | {
    "explanation",
    "rationale_features",
    "economics",
    "copy_source",
}
CHALLENGE_ECONOMICS_FIELDS = {
    "avg_basket",
    "expected_incremental_purchases",
    "expected_incremental_margin",
    "max_reward_rub",
    "contribution_margin",
    "reward_share_max",
}

MULTI_CATEGORY_AFFINITY = Jsonb(
    {
        "dairy": {"share": 0.30, "visits": 6, "cadence_days": 5.0},
        "bakery": {"share": 0.20, "visits": 5, "cadence_days": 6.0},
        "snacks": {"share": 0.15, "visits": 4, "cadence_days": 8.0},
    }
)
