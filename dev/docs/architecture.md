# Архитектура

## Общая схема

```
┌──────────────┐  HTTP/JSON  ┌──────────────────────────┐  SQL   ┌────────────┐
│  frontend    │ ──────────▶ │  backend (FastAPI)       │ ─────▶ │ PostgreSQL │
│  React, web  │ ◀────────── │  монолит по features     │ ◀───── │            │
└──────────────┘             │  llm/ synthetic/ eval/   │        └────────────┘
                             │  simulation/             │
                             └──────────┬───────────────┘
                                        │ Anthropic API (только текст, есть fallback)
                                        ▼
```

Один backend-процесс, одна база. Нет очередей, нет воркеров, нет кэшей: обработка чека синхронная внутри запроса, этого достаточно для демо и честно для тестов.

## Backend: feature-модули и слои

Код разложен по features, а не по типам файлов. Каждый feature — папка `app/features/<name>/` с пятью файлами:

| Файл | Отвечает за | Знает про |
|---|---|---|
| `router.py` | HTTP: путь, метод, статус, DTO in/out | `service.py` своего feature, `dto.py`, `core/db.Conn` |
| `dto.py` | pydantic-модели запросов и ответов API, зеркало `openapi.yaml` | pydantic, `models.py` свой |
| `models.py` | pydantic-модели строк таблиц и доменных объектов feature | только pydantic |
| `service.py` | бизнес-логика, оркестрация, вызов соседей | `database.py` и `models.py` свои, `service.py` и `models.py` соседей, `game_rules`, `llm` |
| `database.py` | SQL к своим таблицам | psycopg, `models.py` свой |

Стрелки идут только вниз: `router → service → database`. Между features — только `service → service`. Ни один feature не ходит в чужие таблицы напрямую: таблица принадлежит одному feature (см. `data-model.md`, колонка «владелец»).

Данные между слоями — только pydantic-модели из `models.py`: `database.py` читает строки через `class_row(Model)`, service принимает и возвращает модели, router превращает модель в DTO через `model_validate`. `dict`, `tuple`, `dataclass`, `TypedDict` как контейнеры данных запрещены.

Чистые вычисления (формулы без базы) — в отдельных модулях внутри feature: `challenges/economics.py`, `antifraud/scoring.py`, `league/scoring.py`, `domovoy/progression.py`. Это делает unit-тесты тривиальными.

### Список features

| Feature | Таблицы-владелец | Что делает |
|---|---|---|
| `health` | — | `GET /health` |
| `users` | `users`, `stores` | демо-список пользователей, профиль, псевдоним |
| `receipts` | `receipts`, `receipt_items` | приём чека, дедупликация 30-мин окна, **оркестратор `process_receipt`** |
| `user_features` | `user_features` | frequency, recency, avg basket, promo sensitivity, category affinity, cadence, favourite store |
| `savings` | — (читает `receipts`) | фактическая экономия за неделю/месяц, по категориям, дельта к прошлому периоду |
| `domovoy` | `domovoy_states` | XP, уровень, настроение, streak, предметы |
| `challenges` | `challenges`, `reward_ledger` | candidate engine, economics engine, выбор hero/side, прогресс, награда, rationale |
| `league` | `leagues`, `league_members` | формирование лиг, score, ранг, зоны |
| `referrals` | `referrals` | код/ссылка, статусы, qualifying purchases, награда |
| `antifraud` | `fraud_checks` | скоринг чека и реферала, решение approve/hold/block, причины |
| `achievements` | `achievements` | ачивки по событиям |
| `pm` | `simulation_runs`, `eval_runs` | PM-карточка пользователя, список фрод-проверок, результаты симуляции и eval |

Вне `features/`, потому что это не HTTP-функциональность:

- `app/llm/` — клиент Anthropic, промпты, детерминированные fallback-шаблоны. Единственная точка вызова LLM.
- `app/synthetic/` — генератор синтетических пользователей и чеков, CLI `uv run python -m app.synthetic --users 300 --weeks 10`.
- `app/eval/` — оценка relevance челленджей на 30–50 профилях, пишет `eval_runs`.
- `app/simulation/` — control vs treatment на 1–10k пользователей, пишет `simulation_runs`.
- `app/game_rules.py` — все константы. Единственное место чисел.
- `app/core/` — config, db, errors, logging.

## Главный поток: обработка чека

Точка входа — `receipts.service.process_receipt(conn, receipt_input)`. Её зовут и `POST /receipts`, и демо-кнопка `POST /users/{id}/receipts/simulate` (она сначала генерирует правдоподобный чек из features пользователя, потом зовёт ту же функцию). Демо-кнопка работает в два шага: `GET /users/{id}/receipts/simulate/draft` собирает черновик корзины (`receipts/draft.py`), пользователь правит позиции на экране и подтверждает их в том же `POST .../simulate` полем `items`. Порядок фиксирован:

```
1. receipts      insert receipt + items; counted=false, если в том же магазине был чек < 30 мин назад
2. antifraud     score_receipt → fraud_checks; block → counted=false, дальше идём, но без наград
3. user_features recompute(user_id)
4. domovoy       on_receipt: +XP за валидную покупку, пересчёт уровня и настроения
5. challenges    on_receipt: прогресс активных; выполнен → reward_ledger, +XP, streak
6. league        on_receipt: пересчёт score участника и ранга
7. referrals     on_receipt: если пользователь приглашённый — проверка qualifying purchase, antifraud.score_referral, награда
8. achievements  on_receipt
9. return ReceiptProcessingResult (дельты: xp, level, mood, savings, challenge progress, league rank до/после, referral status, fraud decision)
```

Всё в одной транзакции: упало в шаге 6 — чек не записан. Это осознанно: демо должно быть либо целиком, либо никак.

## Формирование челленджей

`challenges.service.refresh_weekly(conn, user_id)` — зовётся демо-ручкой `POST /users/{id}/challenges/refresh` и при первом заходе на Home, если активных нет.

```
user_features → candidate_engine (что допустимо: frequency, category)
             → economics (target относительно baseline, expected incremental margin, max reward)
             → personalization (ранжирование: 1 hero + до 2 side)
             → llm.domovoy_copy (title, body, explanation — только текст)
             → insert challenges
```

LLM получает готовые числа и features, возвращает текст. Если ключа нет или вызов упал — шаблон из `llm/templates.py`. Числа в тексте LLM подставляются из данных, а не генерируются.

## Frontend

`src/features/<name>/` на каждый экран: `home`, `challenge`, `league`, `referral`, `pm`. Данные только через TanStack Query. Типы — из `shared/api/schema.d.ts`, сгенерированного из контракта. Оболочка «телефона» в `app/` центрирует контент шириной 390px на десктопе. Текущий пользователь демо — в URL `?user=<id>` и контексте.

## Контракт

`dev/contracts/openapi.yaml` пишется до кода. Backend проверяется на соответствие (`make contract-check`), frontend генерирует типы (`make contract-types`). Изменение API без правки контракта — дефект.

## Время и деньги

«Сейчас» существует только в `app/core/clock.py`: `now()`, `today()`, `week_start()`, `week_end()` в `game_rules.TIMEZONE`. Ruff запрещает `datetime.now()` и naive datetime в остальном коде, тесты замораживают время фикстурой `freeze_time`, демо — переменной `DEMO_NOW`. Деньги внутри — `Decimal`, наружу в DTO — `float`; баллы и XP — `int`.

## Чего в архитектуре нет намеренно

- Auth: демо переключает пользователя по `user_id`. В контракте это обычный path-параметр.
- Фоновые задачи: недельный сброс лиг и генерация челленджей — ручки, которые дергает демо или cron позже.
- Кэш: все чтения — из Postgres, объём данных на демо — тысячи строк.
- Микросервисы, брокеры, ORM.
