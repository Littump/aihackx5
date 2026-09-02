from .types import (
    BIGINT,
    DATE,
    INTEGER,
    JSONB,
    TEXT,
    TIMESTAMPTZ,
    Check,
    Column,
    ForeignKey,
    Index,
    numeric,
)

COLUMNS: dict[str, dict[str, Column]] = {
    "leagues": {
        "id": Column(BIGINT),
        "store_id": Column(BIGINT),
        "division": Column(INTEGER),
        "week_start": Column(DATE),
        "status": Column(TEXT),
    },
    "league_members": {
        "league_id": Column(BIGINT),
        "user_id": Column(BIGINT),
        "score": Column(INTEGER),
        "joined_at": Column(TIMESTAMPTZ),
    },
    "referrals": {
        "id": Column(BIGINT),
        "referrer_user_id": Column(BIGINT),
        "referee_user_id": Column(BIGINT),
        "referee_kind": Column(TEXT),
        "status": Column(TEXT),
        "first_purchase_at": Column(TIMESTAMPTZ, nullable=True),
        "second_purchase_at": Column(TIMESTAMPTZ, nullable=True),
        "fraud_score": numeric(4, 3, nullable=True),
        "fraud_reasons": Column(JSONB),
        "referrer_reward_points": Column(INTEGER),
        "referee_reward_points": Column(INTEGER),
        "created_at": Column(TIMESTAMPTZ),
        "decided_at": Column(TIMESTAMPTZ, nullable=True),
    },
    "fraud_checks": {
        "id": Column(BIGINT),
        "subject_type": Column(TEXT),
        "subject_id": Column(BIGINT),
        "user_id": Column(BIGINT),
        "score": numeric(4, 3),
        "signals": Column(JSONB),
        "decision": Column(TEXT),
        "created_at": Column(TIMESTAMPTZ),
    },
    "achievements": {
        "id": Column(BIGINT),
        "user_id": Column(BIGINT),
        "code": Column(TEXT),
        "unlocked_at": Column(TIMESTAMPTZ),
    },
    "mechanic_decisions": {
        "id": Column(BIGINT),
        "user_id": Column(BIGINT),
        "mechanic": Column(TEXT),
        "reasons": Column(JSONB),
        "created_at": Column(TIMESTAMPTZ),
    },
    "simulation_runs": {
        "id": Column(BIGINT),
        "created_at": Column(TIMESTAMPTZ),
        "params": Column(JSONB),
        "results": Column(JSONB),
    },
    "eval_runs": {
        "id": Column(BIGINT),
        "created_at": Column(TIMESTAMPTZ),
        "profiles": Column(INTEGER),
        "hit_rate": numeric(4, 3),
        "invalid_rate": numeric(4, 3),
        "fallback_rate": numeric(4, 3),
        "economics_pass_rate": numeric(4, 3),
        "details": Column(JSONB),
    },
}

TABLES: tuple[str, ...] = tuple(COLUMNS)

PRIMARY_KEYS: dict[str, tuple[str, ...]] = {
    "leagues": ("id",),
    "league_members": ("league_id", "user_id"),
    "referrals": ("id",),
    "fraud_checks": ("id",),
    "achievements": ("id",),
    "mechanic_decisions": ("id",),
    "simulation_runs": ("id",),
    "eval_runs": ("id",),
}

UNIQUES: dict[str, set[tuple[str, ...]]] = {
    "league_members": {("user_id", "league_id")},
    "referrals": {("referee_user_id",)},
    "achievements": {("user_id", "code")},
}

FOREIGN_KEYS: dict[str, set[ForeignKey]] = {
    "leagues": {ForeignKey("store_id", "stores", "id", "RESTRICT")},
    "league_members": {
        ForeignKey("league_id", "leagues", "id", "CASCADE"),
        ForeignKey("user_id", "users", "id", "CASCADE"),
    },
    "referrals": {
        ForeignKey("referrer_user_id", "users", "id", "CASCADE"),
        ForeignKey("referee_user_id", "users", "id", "CASCADE"),
    },
    "fraud_checks": {ForeignKey("user_id", "users", "id", "CASCADE")},
    "achievements": {ForeignKey("user_id", "users", "id", "CASCADE")},
    "mechanic_decisions": {ForeignKey("user_id", "users", "id", "CASCADE")},
}

INDEXES: dict[str, set[Index]] = {
    "leagues": {
        Index("leagues_week_start_status_idx", "(week_start, status)"),
        Index(
            "leagues_open_store_division_week_uidx",
            "(store_id, division, week_start)",
            unique=True,
            where="(status = 'open'::text)",
        ),
    },
    "league_members": {Index("league_members_league_id_score_idx", "(league_id, score DESC)")},
    "referrals": {
        Index("referrals_referrer_user_id_created_at_idx", "(referrer_user_id, created_at)")
    },
    "fraud_checks": {
        Index("fraud_checks_subject_type_subject_id_idx", "(subject_type, subject_id)"),
        Index("fraud_checks_user_id_created_at_idx", "(user_id, created_at DESC)"),
        Index("fraud_checks_decision_idx", "(decision)"),
    },
}

CHECK_VALUES: list[Check] = [
    Check("leagues", "status", ("open", "closed")),
    Check("referrals", "referee_kind", ("new", "dormant", "active")),
    Check(
        "referrals",
        "status",
        ("pending", "first_purchase", "qualified", "on_review", "rewarded", "blocked"),
    ),
    Check("fraud_checks", "subject_type", ("receipt", "referral")),
    Check("fraud_checks", "decision", ("approve", "hold", "block")),
    Check("mechanic_decisions", "mechanic", ("challenge", "league", "referral")),
]
