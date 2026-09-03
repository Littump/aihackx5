from datetime import UTC, datetime

from psycopg.types.json import Jsonb

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)

PM_USER_RESPONSE_FIELDS = {
    "user",
    "features",
    "recommended_mechanic",
    "hero_challenge",
    "rewards_total_points",
    "rewards_total_xp",
    "expected_incremental_margin_month",
    "fraud_checks",
    "ledger",
}
USER_FEATURES_FIELDS = {
    "computed_at",
    "window_weeks",
    "frequency_per_week",
    "recency_days",
    "avg_basket",
    "promo_sensitivity",
    "cadence_days",
    "category_affinity",
    "realized_savings_30d",
    "favourite_store_id",
    "cross_chain_share",
}
FRAUD_CHECK_FIELDS = {
    "id",
    "subject_type",
    "subject_id",
    "user_id",
    "score",
    "decision",
    "signals",
    "created_at",
}
LEDGER_ENTRY_FIELDS = {"kind", "xp_delta", "points_delta", "ref_type", "ref_id", "created_at"}
HERO_CHALLENGE_FIELDS = {
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
    "explanation",
    "rationale_features",
    "economics",
    "copy_source",
}

SIMULATION_RUN_FIELDS = {"id", "created_at", "params", "results"}
SIMULATION_RESULTS_FIELDS = {
    "purchases_per_user_control",
    "purchases_per_user_treatment",
    "share_above_n_control",
    "share_above_n_treatment",
    "frequency_uplift",
    "incremental_revenue",
    "incremental_margin",
    "reward_cost",
    "net_effect",
    "referral_conversion",
    "fraud_precision",
    "fraud_recall",
}
EVAL_RUN_FIELDS = {
    "id",
    "created_at",
    "profiles",
    "hit_rate",
    "invalid_rate",
    "fallback_rate",
    "economics_pass_rate",
    "details",
}

HERO_ECONOMICS = Jsonb(
    {
        "avg_basket": 600.0,
        "expected_incremental_purchases": 1.0,
        "expected_incremental_margin": 90.0,
        "max_reward_rub": 36.0,
        "contribution_margin": 0.15,
        "reward_share_max": 0.4,
    }
)
