from datetime import UTC, datetime

NOW = datetime(2026, 9, 15, 10, 0, tzinfo=UTC)

HOME_FIELDS = {
    "user",
    "domovoy",
    "savings",
    "points_balance",
    "insight",
    "hero_challenge",
    "league",
    "referral",
    "recommended_mechanic",
}
USER_SUMMARY_FIELDS = {"id", "pseudonym", "segment", "level"}
DOMOVOY_FIELDS = {"xp", "level", "xp_to_next_level", "mood", "mood_reason", "streak_weeks", "items"}
REFERRAL_FIELDS = {"code", "invited_count", "rewarded_count"}
RECOMMENDED_MECHANIC_FIELDS = {"mechanic", "reason"}
