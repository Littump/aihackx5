from datetime import UTC, datetime

NOW = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)

REWARDS_FIELDS = {
    "points_balance",
    "xp",
    "level",
    "xp_to_next_level",
    "rules",
    "history",
}
REWARD_EVENT_FIELDS = {"id", "kind", "title", "detail", "xp_delta", "points_delta", "created_at"}
REWARD_RULE_FIELDS = {"code", "title", "xp", "points_min", "points_max"}
