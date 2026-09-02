# Модель данных

PostgreSQL 16. Все таблицы создаются SQL-миграциями в `dev/backend/migrations/`. Каждая таблица принадлежит одному feature — только его `database.py` пишет в неё. Время — `TIMESTAMPTZ`, деньги — `NUMERIC(12,2)`, баллы и XP — `INTEGER`, перечисления — `TEXT` + `CHECK`. Если колонка не помечена NULL, она NOT NULL; ON DELETE указан у каждого FK.

## Служебные

### `schema_migrations` (владелец: `scripts/migrate.py`)
| колонка | тип | |
|---|---|---|
| version | TEXT PK | имя файла миграции |
| applied_at | TIMESTAMPTZ NOT NULL DEFAULT now() | |

## Пользователи и магазины

### `stores` (владелец: `users`)
| колонка | тип | |
|---|---|---|
| id | BIGSERIAL PK | |
| name | TEXT NOT NULL | «Пятёрочка, Ленина 12» — синтетика |
| chain | TEXT NOT NULL CHECK IN ('pyaterochka','perekrestok') | |
| district | TEXT NOT NULL | для агрегатов «дом vs район» |
| city | TEXT NOT NULL | |

### `users` (владелец: `users`)
| колонка | тип | |
|---|---|---|
| id | BIGSERIAL PK | |
| pseudonym | TEXT NOT NULL UNIQUE | имя Домового, единственное, что видят другие |
| segment | TEXT NOT NULL CHECK IN ('regular_mid','light','heavy','dormant') | |
| favourite_store_id | BIGINT NULL FK stores ON DELETE SET NULL | пересчитывается в user_features, здесь — кэш для лиги |
| referral_code | TEXT NOT NULL UNIQUE | |
| referred_by_user_id | BIGINT NULL FK users ON DELETE SET NULL | |
| device_fingerprint | TEXT NULL | синтетический, для антифрода |
| social_propensity | NUMERIC(4,3) NOT NULL DEFAULT 0 | синтетический признак 0..1 |
| created_at | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| индексы | | `(favourite_store_id)`, `(referred_by_user_id)`, `(device_fingerprint)` |

## Чеки

### `receipts` (владелец: `receipts`)
| колонка | тип | |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT NOT NULL FK users ON DELETE CASCADE | |
| store_id | BIGINT NOT NULL FK stores ON DELETE RESTRICT | |
| purchased_at | TIMESTAMPTZ NOT NULL | |
| regular_total | NUMERIC(12,2) NOT NULL | сумма по регулярным ценам |
| paid_total | NUMERIC(12,2) NOT NULL | фактически оплачено |
| discount_total | NUMERIC(12,2) NOT NULL | regular − paid до баллов |
| points_earned | INTEGER NOT NULL DEFAULT 0 | |
| points_spent | INTEGER NOT NULL DEFAULT 0 | |
| counted | BOOLEAN NOT NULL DEFAULT true | false: дубль в 30-мин окне, превышен дневной лимит или блок антифрода |
| is_returned | BOOLEAN NOT NULL DEFAULT false | |
| returned_at | TIMESTAMPTZ NULL | |
| source | TEXT NOT NULL CHECK IN ('synthetic','simulated','api') | |
| pos_id | TEXT NULL | синтетический кассовый узел, для антифрода |
| created_at | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| индексы | | `(user_id, purchased_at DESC)`, `(store_id, purchased_at)` |

### `receipt_items` (владелец: `receipts`)
| колонка | тип | |
|---|---|---|
| id | BIGSERIAL PK | |
| receipt_id | BIGINT NOT NULL FK receipts ON DELETE CASCADE | |
| product_name | TEXT NOT NULL | |
| category | TEXT NOT NULL | из фиксированного списка 12 макрокатегорий в `game_rules.CATEGORIES` |
| qty | NUMERIC(8,3) NOT NULL | |
| regular_price | NUMERIC(12,2) NOT NULL | за единицу |
| paid_price | NUMERIC(12,2) NOT NULL | за единицу |
| is_promo | BOOLEAN NOT NULL DEFAULT false | |
| индексы | | `(receipt_id)`, `(category)` |

## Признаки и состояние

### `user_features` (владелец: `user_features`)
Одна строка на пользователя, полностью пересчитывается после каждого чека.
| колонка | тип | |
|---|---|---|
| user_id | BIGINT PK FK users ON DELETE CASCADE | |
| computed_at | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| window_weeks | INTEGER NOT NULL | по скольким неделям считали (8–12) |
| frequency_per_week | NUMERIC(6,3) NOT NULL DEFAULT 0 | counted-чеки / недели |
| recency_days | INTEGER NULL | дней с последнего чека; NULL — нет чеков |
| avg_basket | NUMERIC(12,2) NOT NULL DEFAULT 0 | |
| promo_sensitivity | NUMERIC(4,3) NOT NULL DEFAULT 0 | доля promo-позиций по сумме |
| cadence_days | NUMERIC(6,2) NULL | средний интервал между чеками; NULL — нет чеков |
| category_affinity | JSONB NOT NULL DEFAULT '{}' | `{"dairy": {"share": 0.21, "visits": 6, "cadence_days": 5.8}, ...}` |
| weekday_pattern | JSONB NOT NULL DEFAULT '[]' | `[0.1, 0.25, ...]` доли по дням недели |
| realized_savings_30d | NUMERIC(12,2) NOT NULL DEFAULT 0 | |
| favourite_store_id | BIGINT NULL FK stores ON DELETE SET NULL | NULL — нет чеков |
| cross_chain_share | NUMERIC(4,3) NOT NULL DEFAULT 0 | доля чеков не в основной сети |

### `domovoy_states` (владелец: `domovoy`)
| колонка | тип | |
|---|---|---|
| user_id | BIGINT PK FK users ON DELETE CASCADE | |
| xp | INTEGER NOT NULL DEFAULT 0 | |
| level | INTEGER NOT NULL DEFAULT 1 | производное от xp, хранится для простоты запросов |
| mood | TEXT NOT NULL CHECK IN ('cheerful','cozy','healthy','bored','sleepy') | |
| mood_reason | TEXT NOT NULL DEFAULT '' | короткая причина для UI |
| streak_weeks | INTEGER NOT NULL DEFAULT 0 | |
| streak_freeze_available | BOOLEAN NOT NULL DEFAULT true | одна заморозка в месяц |
| items | JSONB NOT NULL DEFAULT '[]' | коды косметики |
| last_fed_at | TIMESTAMPTZ NULL | последний counted-чек |
| updated_at | TIMESTAMPTZ NOT NULL DEFAULT now() | |

## Челленджи и награды

### `challenges` (владелец: `challenges`)
| колонка | тип | |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT NOT NULL FK users ON DELETE CASCADE | |
| type | TEXT NOT NULL CHECK IN ('frequency','category') | MVP-типы из PRD |
| category | TEXT NULL | для `category` |
| status | TEXT NOT NULL CHECK IN ('active','completed','failed','expired') | |
| is_hero | BOOLEAN NOT NULL | 1 hero + до 2 side |
| baseline | NUMERIC(8,3) NOT NULL | покупок/нед или покупок категории за окно |
| target | NUMERIC(8,3) NOT NULL | |
| progress | NUMERIC(8,3) NOT NULL DEFAULT 0 | |
| period_start | TIMESTAMPTZ NOT NULL | |
| period_end | TIMESTAMPTZ NOT NULL | deadline |
| reward_xp | INTEGER NOT NULL | |
| reward_points | INTEGER NOT NULL | 0, если economics не разрешил денежную награду |
| economics | JSONB NOT NULL | `{"avg_basket":600,"expected_incremental_margin":90,"max_reward":36,"contribution_margin":0.15}` |
| rationale_features | JSONB NOT NULL | какие features легли в основу, для «Почему это мне?» и PM view |
| copy_title | TEXT NOT NULL | |
| copy_body | TEXT NOT NULL | |
| copy_explanation | TEXT NOT NULL | |
| copy_source | TEXT NOT NULL CHECK IN ('llm','template') | |
| created_at | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| completed_at | TIMESTAMPTZ NULL | |
| индексы | | `(user_id, status)`, `(user_id, period_end)` |

### `reward_ledger` (владелец: `challenges`)
Журнал всех начислений — единственный источник для экономики и PM view.
| колонка | тип | |
|---|---|---|
| id | BIGSERIAL PK | |
| user_id | BIGINT NOT NULL FK users ON DELETE CASCADE | |
| kind | TEXT NOT NULL CHECK IN ('receipt_xp','challenge','streak','league','referral','achievement') | |
| xp_delta | INTEGER NOT NULL DEFAULT 0 | |
| points_delta | INTEGER NOT NULL DEFAULT 0 | |
| ref_type | TEXT NULL | 'challenge','receipt','referral','league_week' |
| ref_id | BIGINT NULL | |
| created_at | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| индексы | | `(user_id, created_at DESC)`, `(kind)` |

## Лига

### `leagues` (владелец: `league`)
| колонка | тип | |
|---|---|---|
| id | BIGSERIAL PK | |
| store_id | BIGINT NOT NULL FK stores ON DELETE RESTRICT | «дом» |
| division | INTEGER NOT NULL CHECK 1..5 | 1 бронза … 5 алмаз |
| week_start | DATE NOT NULL | понедельник |
| status | TEXT NOT NULL DEFAULT 'open' CHECK IN ('open','closed') | open — набирает до 30, при 30 закрывается и открывается новая (шардирование) |
| индексы | | частичный `UNIQUE (store_id, division, week_start) WHERE status = 'open'` — не более одной открытой лиги на тройку, closed-шардов может быть несколько; `(week_start, status)` |

### `league_members` (владелец: `league`)
| колонка | тип | |
|---|---|---|
| league_id | BIGINT NOT NULL FK leagues ON DELETE CASCADE | |
| user_id | BIGINT NOT NULL FK users ON DELETE CASCADE | |
| score | INTEGER NOT NULL DEFAULT 0 | |
| joined_at | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| PK | | `(league_id, user_id)`; `UNIQUE (user_id, league_id)` + индекс `(league_id, score DESC)` |

Ранг и зоны считаются запросом по `score DESC`, не хранятся.

## Рефералы и антифрод

### `referrals` (владелец: `referrals`)
| колонка | тип | |
|---|---|---|
| id | BIGSERIAL PK | |
| referrer_user_id | BIGINT NOT NULL FK users ON DELETE CASCADE | |
| referee_user_id | BIGINT NOT NULL UNIQUE FK users ON DELETE CASCADE | |
| referee_kind | TEXT NOT NULL CHECK IN ('new','dormant','active') | определяет размер награды |
| status | TEXT NOT NULL DEFAULT 'pending' CHECK IN ('pending','first_purchase','qualified','on_review','rewarded','blocked') | |
| first_purchase_at, second_purchase_at | TIMESTAMPTZ NULL | NULL — покупки ещё не было |
| fraud_score | NUMERIC(4,3) NULL | NULL — проверка ещё не проводилась |
| fraud_reasons | JSONB NOT NULL DEFAULT '[]' | |
| referrer_reward_points, referee_reward_points | INTEGER NOT NULL DEFAULT 0 | |
| created_at | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| decided_at | TIMESTAMPTZ NULL | NULL — решения ещё нет |
| индексы | | `(referrer_user_id, created_at)` |

### `fraud_checks` (владелец: `antifraud`)
| колонка | тип | |
|---|---|---|
| id | BIGSERIAL PK | |
| subject_type | TEXT NOT NULL CHECK IN ('receipt','referral') | |
| subject_id | BIGINT NOT NULL | |
| user_id | BIGINT NOT NULL FK users ON DELETE CASCADE | |
| score | NUMERIC(4,3) NOT NULL | 0..1 |
| signals | JSONB NOT NULL | `[{"code":"burst_same_store","weight":0.25,"strong":true,"detail":"4 чека за 12 минут"}]` |
| decision | TEXT NOT NULL CHECK IN ('approve','hold','block') | |
| created_at | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| индексы | | `(subject_type, subject_id)`, `(user_id, created_at DESC)`, `(decision)` |

## Прочее

### `achievements` (владелец: `achievements`)
`id`, `user_id` FK users ON DELETE CASCADE, `code` TEXT, `unlocked_at` TIMESTAMPTZ NOT NULL DEFAULT now(); `UNIQUE (user_id, code)`.

### `mechanic_decisions` (владелец: `pm`)
Какую механику показали как hero-блок и почему. `id`, `user_id` FK users ON DELETE CASCADE, `mechanic` CHECK IN ('challenge','league','referral'), `reasons` JSONB, `created_at` TIMESTAMPTZ NOT NULL DEFAULT now().

### `simulation_runs` (владелец: `pm`, пишет `app/simulation`)
`id`, `created_at` TIMESTAMPTZ NOT NULL DEFAULT now(), `params` JSONB (users, weeks, uplift, margin, reward share, sponsor share — всё с пометкой assumption), `results` JSONB (purchases per user, share ≥ N, uplift, incremental revenue/margin, reward cost, net, referral conversion, fraud precision/recall).

### `eval_runs` (владелец: `pm`, пишет `app/eval`)
`id`, `created_at` TIMESTAMPTZ NOT NULL DEFAULT now(), `profiles` INTEGER, `hit_rate` NUMERIC(4,3), `invalid_rate` NUMERIC(4,3), `fallback_rate` NUMERIC(4,3), `economics_pass_rate` NUMERIC(4,3), `details` JSONB (по профилям: challenge, вердикт, причина).
