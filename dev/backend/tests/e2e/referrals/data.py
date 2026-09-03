from datetime import UTC, datetime, timedelta

NOW = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
REFERRER_CREATED_AT = NOW - timedelta(days=90)

REFERRAL_RESPONSE_FIELDS = {
    "code",
    "link",
    "rules",
    "referrer_reward_points",
    "referee_reward_points_new",
    "referee_reward_points_dormant",
    "invitees",
    "paid_this_month",
    "paid_limit_month",
}
REFERRAL_INVITEE_FIELDS = {
    "label",
    "referee_kind",
    "status",
    "purchases_done",
    "purchases_required",
    "reward_points",
    "created_at",
}
REDEEM_RESPONSE_FIELDS = {"referee_user_id", "referrer_user_id", "referee_kind", "status"}
