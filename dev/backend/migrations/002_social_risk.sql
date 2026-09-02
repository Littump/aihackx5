CREATE TABLE leagues (
    id          BIGSERIAL PRIMARY KEY,
    store_id    BIGINT NOT NULL REFERENCES stores (id) ON DELETE RESTRICT,
    division    INTEGER NOT NULL CHECK (division BETWEEN 1 AND 5),
    week_start  DATE NOT NULL,
    status      TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed'))
);

CREATE UNIQUE INDEX leagues_open_store_division_week_uidx
    ON leagues (store_id, division, week_start)
    WHERE status = 'open';

CREATE INDEX leagues_week_start_status_idx ON leagues (week_start, status);

CREATE TABLE league_members (
    league_id  BIGINT NOT NULL REFERENCES leagues (id) ON DELETE CASCADE,
    user_id    BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    score      INTEGER NOT NULL DEFAULT 0,
    joined_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (league_id, user_id)
);

ALTER TABLE league_members
    ADD CONSTRAINT league_members_user_id_league_id_key
    UNIQUE (user_id, league_id);

CREATE INDEX league_members_league_id_score_idx ON league_members (league_id, score DESC);

CREATE TABLE referrals (
    id                     BIGSERIAL PRIMARY KEY,
    referrer_user_id       BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    referee_user_id        BIGINT NOT NULL UNIQUE REFERENCES users (id) ON DELETE CASCADE,
    referee_kind           TEXT NOT NULL CHECK (referee_kind IN ('new', 'dormant', 'active')),
    status                 TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN
            ('pending', 'first_purchase', 'qualified', 'on_review', 'rewarded', 'blocked')
        ),
    first_purchase_at      TIMESTAMPTZ,
    second_purchase_at     TIMESTAMPTZ,
    fraud_score            NUMERIC(4, 3),
    fraud_reasons          JSONB NOT NULL DEFAULT '[]',
    referrer_reward_points INTEGER NOT NULL DEFAULT 0,
    referee_reward_points  INTEGER NOT NULL DEFAULT 0,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    decided_at             TIMESTAMPTZ
);

CREATE INDEX referrals_referrer_user_id_created_at_idx ON referrals (referrer_user_id, created_at);

CREATE TABLE fraud_checks (
    id           BIGSERIAL PRIMARY KEY,
    subject_type TEXT NOT NULL CHECK (subject_type IN ('receipt', 'referral')),
    subject_id   BIGINT NOT NULL,
    user_id      BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    score        NUMERIC(4, 3) NOT NULL,
    signals      JSONB NOT NULL,
    decision     TEXT NOT NULL CHECK (decision IN ('approve', 'hold', 'block')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX fraud_checks_subject_type_subject_id_idx ON fraud_checks (subject_type, subject_id);
CREATE INDEX fraud_checks_user_id_created_at_idx ON fraud_checks (user_id, created_at DESC);
CREATE INDEX fraud_checks_decision_idx ON fraud_checks (decision);

CREATE TABLE achievements (
    id           BIGSERIAL PRIMARY KEY,
    user_id      BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    code         TEXT NOT NULL,
    unlocked_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, code)
);

CREATE TABLE mechanic_decisions (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    mechanic   TEXT NOT NULL CHECK (mechanic IN ('challenge', 'league', 'referral')),
    reasons    JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE simulation_runs (
    id         BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    params     JSONB NOT NULL,
    results    JSONB NOT NULL
);

CREATE TABLE eval_runs (
    id                   BIGSERIAL PRIMARY KEY,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    profiles             INTEGER NOT NULL,
    hit_rate             NUMERIC(4, 3) NOT NULL,
    invalid_rate         NUMERIC(4, 3) NOT NULL,
    fallback_rate        NUMERIC(4, 3) NOT NULL,
    economics_pass_rate  NUMERIC(4, 3) NOT NULL,
    details              JSONB NOT NULL
);
