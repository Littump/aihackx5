CREATE TABLE stores (
    id        BIGSERIAL PRIMARY KEY,
    name      TEXT NOT NULL,
    chain     TEXT NOT NULL CHECK (chain IN ('pyaterochka', 'perekrestok')),
    district  TEXT NOT NULL,
    city      TEXT NOT NULL
);

CREATE TABLE users (
    id                    BIGSERIAL PRIMARY KEY,
    pseudonym             TEXT NOT NULL UNIQUE,
    segment               TEXT NOT NULL
        CHECK (segment IN ('regular_mid', 'light', 'heavy', 'dormant')),
    favourite_store_id    BIGINT REFERENCES stores (id) ON DELETE SET NULL,
    referral_code         TEXT NOT NULL UNIQUE,
    referred_by_user_id   BIGINT REFERENCES users (id) ON DELETE SET NULL,
    device_fingerprint    TEXT,
    social_propensity     NUMERIC(4, 3) NOT NULL DEFAULT 0,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX users_favourite_store_id_idx ON users (favourite_store_id);
CREATE INDEX users_referred_by_user_id_idx ON users (referred_by_user_id);
CREATE INDEX users_device_fingerprint_idx ON users (device_fingerprint);

CREATE TABLE receipts (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    store_id        BIGINT NOT NULL REFERENCES stores (id) ON DELETE RESTRICT,
    purchased_at    TIMESTAMPTZ NOT NULL,
    regular_total   NUMERIC(12, 2) NOT NULL,
    paid_total      NUMERIC(12, 2) NOT NULL,
    discount_total  NUMERIC(12, 2) NOT NULL,
    points_earned   INTEGER NOT NULL DEFAULT 0,
    points_spent    INTEGER NOT NULL DEFAULT 0,
    counted         BOOLEAN NOT NULL DEFAULT true,
    is_returned     BOOLEAN NOT NULL DEFAULT false,
    returned_at     TIMESTAMPTZ,
    source          TEXT NOT NULL CHECK (source IN ('synthetic', 'simulated', 'api')),
    pos_id          TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX receipts_user_id_purchased_at_idx ON receipts (user_id, purchased_at DESC);
CREATE INDEX receipts_store_id_purchased_at_idx ON receipts (store_id, purchased_at);

CREATE TABLE receipt_items (
    id             BIGSERIAL PRIMARY KEY,
    receipt_id     BIGINT NOT NULL REFERENCES receipts (id) ON DELETE CASCADE,
    product_name   TEXT NOT NULL,
    category       TEXT NOT NULL,
    qty            NUMERIC(8, 3) NOT NULL,
    regular_price  NUMERIC(12, 2) NOT NULL,
    paid_price     NUMERIC(12, 2) NOT NULL,
    is_promo       BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX receipt_items_receipt_id_idx ON receipt_items (receipt_id);
CREATE INDEX receipt_items_category_idx ON receipt_items (category);

CREATE TABLE user_features (
    user_id               BIGINT PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
    computed_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    window_weeks          INTEGER NOT NULL,
    frequency_per_week    NUMERIC(6, 3) NOT NULL DEFAULT 0,
    recency_days          INTEGER,
    avg_basket            NUMERIC(12, 2) NOT NULL DEFAULT 0,
    promo_sensitivity     NUMERIC(4, 3) NOT NULL DEFAULT 0,
    cadence_days          NUMERIC(6, 2),
    category_affinity     JSONB NOT NULL DEFAULT '{}',
    weekday_pattern       JSONB NOT NULL DEFAULT '[]',
    realized_savings_30d  NUMERIC(12, 2) NOT NULL DEFAULT 0,
    favourite_store_id    BIGINT REFERENCES stores (id) ON DELETE SET NULL,
    cross_chain_share     NUMERIC(4, 3) NOT NULL DEFAULT 0
);

CREATE TABLE domovoy_states (
    user_id                  BIGINT PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
    xp                       INTEGER NOT NULL DEFAULT 0,
    level                    INTEGER NOT NULL DEFAULT 1,
    mood                     TEXT NOT NULL
        CHECK (mood IN ('cheerful', 'cozy', 'healthy', 'bored', 'sleepy')),
    mood_reason              TEXT NOT NULL DEFAULT '',
    streak_weeks             INTEGER NOT NULL DEFAULT 0,
    streak_freeze_available  BOOLEAN NOT NULL DEFAULT true,
    items                    JSONB NOT NULL DEFAULT '[]',
    last_fed_at              TIMESTAMPTZ,
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE challenges (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    type                TEXT NOT NULL CHECK (type IN ('frequency', 'category')),
    category            TEXT,
    status              TEXT NOT NULL
        CHECK (status IN ('active', 'completed', 'failed', 'expired')),
    is_hero             BOOLEAN NOT NULL,
    baseline            NUMERIC(8, 3) NOT NULL,
    target              NUMERIC(8, 3) NOT NULL,
    progress            NUMERIC(8, 3) NOT NULL DEFAULT 0,
    period_start        TIMESTAMPTZ NOT NULL,
    period_end          TIMESTAMPTZ NOT NULL,
    reward_xp           INTEGER NOT NULL,
    reward_points       INTEGER NOT NULL,
    economics           JSONB NOT NULL,
    rationale_features  JSONB NOT NULL,
    copy_title          TEXT NOT NULL,
    copy_body           TEXT NOT NULL,
    copy_explanation    TEXT NOT NULL,
    copy_source         TEXT NOT NULL CHECK (copy_source IN ('llm', 'template')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at        TIMESTAMPTZ
);

CREATE INDEX challenges_user_id_status_idx ON challenges (user_id, status);
CREATE INDEX challenges_user_id_period_end_idx ON challenges (user_id, period_end);

CREATE TABLE reward_ledger (
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    kind          TEXT NOT NULL CHECK (
        kind IN ('receipt_xp', 'challenge', 'streak', 'league', 'referral', 'achievement')
    ),
    xp_delta      INTEGER NOT NULL DEFAULT 0,
    points_delta  INTEGER NOT NULL DEFAULT 0,
    ref_type      TEXT,
    ref_id        BIGINT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX reward_ledger_user_id_created_at_idx ON reward_ledger (user_id, created_at DESC);
CREATE INDEX reward_ledger_kind_idx ON reward_ledger (kind);
