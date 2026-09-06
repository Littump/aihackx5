# aihackx5 — «Домовой»

Персональный игровой слой поверх X5 Клуба. Хакатон, MVP за несколько дней. Продукт описан в `docs/product-analysis/mechanics/PRD.md` — это источник истины по функциональности. Всё, что ниже, — как мы это строим.

## Стек

- Backend: Python 3.12, FastAPI, монолит, raw SQL через psycopg 3 (без ORM), PostgreSQL 16, SQL-миграции.
- Frontend: TypeScript, React, Vite, mobile-first веб (один экран шириной до 430px), TanStack Query, react-router, Tailwind.
- LLM: Anthropic SDK, только для текста и объяснений. LLM не назначает награды и не считает деньги.
- Тесты: pytest (unit + e2e через реальный Postgres), Vitest.
- Качество: ruff, mypy, ESLint, Prettier, pre-commit. Коммит без зелёных хуков невозможен.

## Где что лежит

| Путь | Что там |
|---|---|
| `docs/product-analysis/mechanics/PRD.md` | Что делаем. Читать первым |
| `dev/docs/README.md` | Индекс технической документации |
| `dev/docs/architecture.md` | Слои, папки, поток данных, границы модулей |
| `dev/docs/domain-rules.md` | Все числа и формулы: XP, savings, economics, лига, антифрод, рефералы |
| `dev/docs/data-model.md` | Таблицы и колонки |
| `dev/contracts/openapi.yaml` | Контракт API. Меняется до кода, а не после |
| `dev/docs/dev-pipeline.md` | Как берём задачу и доводим до done |
| `dev/docs/backlog/` | Эпики и задачи с acceptance criteria |
| `dev/docs/team.md` | Кто что делает |
| `dev/docs/decisions.md` | Почему архитектура такая; не переспаривать без новой информации |
| `dev/docs/deploy.md` | Деплой на Yandex Cloud VM и CD |
| `.claude/rules/` | Правила для кода: backend, frontend, testing, style |
| `.claude/skills/` | Рецепты: run-task, add-endpoint, add-model, add-logic, add-screen, update-api-contract |
| `.claude/agents/` | Субагенты: backend-dev, frontend-dev, qa-tester, reviewer |
| `dev/backend/app/ml/` | LLM-планировщик челленджей + контрфактический eval (E14 AI-008..012); промпты в `app/ml/prompts/` |
| `docs/ml-rework/` | Дизайн ML-переработки и последний eval-отчёт (`eval-report.md`) |

## Обязательный порядок перед любой задачей

1. Прочитать `dev/docs/backlog/README.md` и файл эпика задачи — там acceptance criteria.
2. Прочитать `dev/docs/architecture.md` и `.claude/rules/code-style.md`.
3. Прочитать профильные правила: `.claude/rules/backend.md` или `.claude/rules/frontend.md`, всегда `.claude/rules/testing.md`.
4. Если задача про числа и формулы — `dev/docs/domain-rules.md`. Если про API — `dev/contracts/openapi.yaml`.
5. Если задача укладывается в скилл (`add-endpoint`, `add-model`, `add-logic`, `add-screen`, `update-api-contract`) — работать по скиллу, а не по памяти.

Полный цикл одной задачи — скилл `run-task`: разработчик → тестировщик → ревьюер → статус в backlog.

## Жёсткие правила (нарушение = задача не принята)

- Слои backend: `router.py` → `service.py` → `database.py`. Router не знает про SQL, database не знает про HTTP, service не знает ни того, ни другого. DTO только в `dto.py`.
- SQL пишется руками в `database.py` и нигде больше. ORM, query builder и SQL-строки в сервисах запрещены.
- Между слоями ходят только pydantic-модели из `models.py`: `database.py` возвращает модели через `class_row`, `service.py` принимает и отдаёт модели, `router.py` превращает их в DTO. Никаких `dict`, `tuple`, `dataclass`, `TypedDict`.
- Докстринги и комментарии не длиннее одной строки. Многострочные докстринги, блочные комментарии и два комментария подряд запрещены — это проверяет хук `scripts/check_comments.py`.
- Каждая ручка имеет e2e-тест через реальный Postgres. Каждая функция сервиса с логикой имеет unit-тест.
- Каждое изменение API начинается с `dev/contracts/openapi.yaml`, затем backend, затем `make contract-types` для фронта.
- Числа игровых правил живут только в `dev/backend/app/game_rules.py` и зеркалятся в `dev/docs/domain-rules.md`. Магические константы в сервисах запрещены.
- Время только через `app/core/clock.py`; `datetime.now()` и naive datetime не проходят ruff. Деньги: `Decimal` в моделях, `float` в DTO.
- LLM-вызовы только через `app/llm/`, всегда с детерминированным fallback, чтобы тесты и демо работали без ключа.
- Никаких ФИО, адресов и абсолютных чужих трат в ответах API рейтинга.

## Команды

```bash
make setup          # uv sync, npm install, pre-commit install
make up             # Postgres в docker (порт 5433)
make migrate        # применить SQL-миграции
make test-db-reset  # пересоздать domovoy_test (после правки уже применённой миграции)
make dev-be         # uvicorn с reload на :8000
make dev-fe         # vite на :5173
make test-be        # pytest unit + e2e
make test-fe        # vitest
make check          # ruff + mypy + eslint + prettier --check + check_comments
make format         # автоформат всего
make contract-types # openapi.yaml -> src/shared/api/schema.d.ts
make contract-check # сравнить openapi.yaml с тем, что отдаёт backend
```

## ML eval — контролируемый прогон планировщика

Модуль `dev/backend/app/ml/` — самодостаточный LLM-планировщик челленджей (E14 AI-008..012): синтетический каталог/профили/история, планировщик на qwen через tool-use с валидатором и rule-fallback, экономика наград и контрфактический eval из одной точки T. Промпты — в `app/ml/prompts/*.md`, схемы — pydantic v2 в `app/ml/schemas.py`, метрики — `app/ml/eval.py`. Отчёт последнего прогона — `docs/ml-rework/eval-report.md`.

### Инференс-узел и модели для eval
Конфигурация GPU-узла — доступ, раскладка GPU, запуск vLLM-серверов planner/actor, и строгие правила (что агент может делать на узле и как менять параметры) — вынесена в gitignored-скилл `.codex/skills/inference-node/SKILL.md`. Он не в git, потому что содержит адрес узла и путь к паролю. Дефолтные модели: planner — `qwen38-27b-fp8` (наш Qwen-узел; DeepSeek снят, planner занимает все 4 GPU узла), actor — `MiniMaxAI/MiniMax-M3-MXFP8` на **продовом** узле (эндпоинт `…:8080/v1`). Модели прописаны в `app/ml/config.py` как localhost-плейсхолдеры; реальные base-url узлов — только в локальном `.env` и в скилле (в git адрес узла не коммитим). Actor-узел общий и продовый: наши вызовы троттлятся (потолок ≤30% занятости узла по `/metrics`, предстарт-гейт <50%), Qwen на нашем узле гоняем без ограничений. Во всех вызовах — strict `json_schema` structured output; «thinking» реализовано как обязательное первое поле схемы (модель рассуждает внутри структурированного ответа), а нативный `enable_thinking` в chat-template для guided-JSON вызовов (planner/actor/judge) ВЫКЛЮЧЕН: у Qwen под xgrammar нативный think уходит в неограниченную фазу рассуждения, сжигает весь лимит токенов и возвращает пустой ответ (llm-plan share падает в 0). Генерация персон (`persona`) идёт на MiniMax и native-thinking допускает (`config.PERSONA_ENABLE_THINKING`). Любые изменения на узле — только по правилам из скилла.

### Перезапуск eval
Из `dev/backend`. `--seed 7` — зафиксированный дефолт прогона (воспроизводимость); менять только осознанно. Планировщик (награды) и actor (покупатель) — строго разные модели.
Planner — Qwen на нашем узле (`--planner-base-url`/`--planner-model` или `ML_PLANNER_BASE_URL`/`ML_PLANNER_MODEL`);
actor — MiniMax на продовом узле `…:8080/v1` (`--actor-base-url`/`--actor-model` или `ML_ACTOR_BASE_URL`/`ML_ACTOR_MODEL`).
Base-url узлов берутся из локального `.env` (реальный адрес — в скилле); `config.py` держит localhost-плейсхолдеры и в git не попадает. CLI не читает `.env` сам — подгружаем через `set -a; source ../../.env; set +a`. Actor автоматически троттлится по `/metrics` продового узла (потолок `--actor-occupancy-ceiling` 0.30, предстарт-гейт `--precheck-max-occupancy` 0.50; выключить — `--no-capacity-gate`):

```bash
cd dev/backend
set -a; source ../../.env; set +a   # реальные base-url planner/actor из локального .env (адрес — в скилле)
uv run python -m app.ml.cli gen-personas --seed 7 --count 50 --out build/personas_seed7.json  # разово; персоны с продового узла
uv run python -m app.ml.cli run-eval \
  --seed 7 --profiles 50 --horizon 12 --cut 6 --concurrency 3 \
  --personas build/personas_seed7.json \
  --out-md ../../docs/ml-rework/eval-report.md \
  --out-json build/eval_report.json \
  --trace-out build/eval_traces.jsonl
```

- `--profiles` — размер выборки (AI-012 требует 50); `--seed`, `--horizon`, `--cut` детерминируют историю и точку T, поэтому прогон воспроизводим.
- `--concurrency` (дефолт `config.EVAL_MAX_CONCURRENCY=3`) — сколько профилей считать параллельно. Actor вдобавок ограничен собственным семафором (`--actor-concurrency`, дефолт 3) и capacity-гейтом, поэтому на общий продовый узел уходит не больше разрешённой доли. Живой прогон 50 профилей — порядка часа, троттлинг может растянуть его при занятом узле.
- Таймаут одного LLM-вызова — `config.LLM_TIMEOUT_S=180`. Actor с thinking отвечает дольше и крупнее (`config.ACTOR_MAX_TOKENS=4000`), поэтому запас по таймауту нужен. Актёр ретраит вызов `config.ACTOR_RETRY_MAX=2` раза (планировщик — 3), после чего честно пишет `fallback_null` (не подменяет решение молча).
- `gen-catalog` / `gen-profiles` — отдельно выгрузить синтетические данные (флаг `--out`).

### Null-инвариант (без сети)
При нулевом uplift ветки обязаны совпадать (AC AI-010/011). Гоняется без сети:

```bash
uv run python -m app.ml.cli run-eval --seed 7 --profiles 50 --null --no-llm \
  --out-md build/eval_null.md --out-json build/eval_null.json
```

Ожидаемо: incremental visits = 0, `net_effect` ≤ 0, uplift `0.0 pp`, строка «Null test PASS». `--no-llm` использует rule-fallback вместо planner и null-ответ вместо actor.

### Локальный Langfuse (self-hosted) и авто-заливка
Поднять локальный стек Langfuse (web+worker+postgres+clickhouse+redis+minio) одной командой; org/project/ключи создаются автоматически через `LANGFUSE_INIT_*`, minio вынесен с занятого порта 9090 на 9190/9191:

```bash
make langfuse-up      # UI: http://localhost:3000, вход admin@domovoy.local / domovoy-admin
make langfuse-logs    # хвост логов web+worker
make langfuse-down    # погасить стек (данные сохраняются в volume)
```

Фиксированные локальные ключи проекта: public `pk-lf-domovoy-local`, secret `sk-lf-domovoy-local`, host `http://localhost:3000` (дефолты в `app/ml/config.py`; переопределяются `LANGFUSE_HOST`/`LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`).

`run-eval` c `--trace-out` заливает трейсы в Langfuse автоматически по окончании прогона — отдельный `export-traces` не нужен. Заливка best-effort: если Langfuse недоступен, прогон не падает, а печатает `langfuse push skipped: ...`. Выключить — `--no-langfuse`.

```bash
uv run python -m app.ml.cli run-eval --seed 7 --profiles 50 --horizon 12 --cut 6 \
  --trace-out build/eval_traces.jsonl            # трейсы уедут в Langfuse сами
```

Существующий JSONL можно залить вручную (ключи берутся из дефолтов/env):

```bash
uv run python -m app.ml.cli export-traces --in build/eval_traces.jsonl --to langfuse
```

### Трейсы прогона и инспекция в Langfuse
Актёр (синтетический покупатель) намеренно «пиковый» и малолояльный: играет роль от первого лица, по умолчанию продолжает покупать как обычно (`buy_as_usual`/`ignore`) и включается (`use_offer`) только если оффер проходит его личную планку. Выход строгий: `thinking` → `promo_decision` → `extra_visits` → `completed_challenge` → `rationale` (см. `docs/ml-rework/actor-and-tracing.md`). Диалог идёт многонедельным чатом (`user_sim.run_weekly_chat`): личность покупателя — в кэшируемом system-сообщении (KV-cache), далее по одному ходу на неделю от точки T до горизонта; челлендж активен одну неделю (7 дней), инкремент считается только за активную неделю, невовлечённый хвост проматывается по baseline. Понедельная прогрессия и числовые метрики уходят в Langfuse для графиков по T.

```bash
uv run python -m app.ml.cli run-eval --seed 7 --profiles 50 --horizon 12 --cut 6 \
  --trace-out build/eval_traces.jsonl   # + обычные --out-md/--out-json
uv run python -m app.ml.cli export-traces --in build/eval_traces.jsonl --to json --out build/langfuse_generations.json
LANGFUSE_HOST=http://localhost:3000 LANGFUSE_PUBLIC_KEY=pk LANGFUSE_SECRET_KEY=sk \
  uv run python -m app.ml.cli export-traces --in build/eval_traces.jsonl --to langfuse
```

- `--trace-out` пишет JSONL: строка 1 — шапка прогона, далее по профилю (снапшот, `planner_calls`, ветки с решением актёра, сырым ответом LLM и распарсенным JSON — для проверки, что LLM не читерит). `build/` в `.gitignore`.
- `export-traces --to langfuse` заливает по одному trace на профиль и по generation на LLM-вызов; по умолчанию `run-eval --trace-out` делает это сам. Локальный стек — `make langfuse-up` (`deploy/langfuse/`).

### Как прогонять eval (полный цикл: run → view → judge)
Один прогон делает всё: считает метрики, пишет трейсы и сам заливает их в Langfuse. Для быстрой проверки хватает нескольких профилей; для отчёта AI-012 — 50. Planner (награды) и actor (покупатель) — строго разные модели; реальные base-url берутся из локального `.env` (`set -a; source ../../.env; set +a`), либо передаются флагами `--planner-base-url`/`--actor-base-url` (адрес узла — в скилле, в git не коммитим).

```bash
cd dev/backend
# 1) быстрый прогон на нескольких пользователях (проверить трейсы/стратегию)
uv run python -m app.ml.cli run-eval --seed 21 --profiles 4 --horizon 12 --cut 6 --concurrency 3 \
  --out-md build/eval_small.md --out-json build/eval_small.json --trace-out build/eval_small.jsonl
# 2) авто-оценка тех же трейсов LLM-судьёй (скоры уедут в Langfuse на те же traces)
uv run python -m app.ml.cli judge-traces --in build/eval_small.jsonl --to langfuse
```

- Разные seed дают разные сегменты покупателей — для наглядной проверки стратегии брать seed с разнообразием (например `--seed 21` → regular_mid/dormant/light), а не выборку из одного сегмента.
- `judge-traces` привязывает скоры к тем же trace_id, что и `run-eval` (детерминированный fingerprint прогона), поэтому судью гонять по тому же `--trace-out` JSONL, что залил прогон. Пересоздавать прогон не нужно.

### Human eval: как читать один трейс
Открыть `http://localhost:3000`, вход `admin@domovoy.local` / `domovoy-admin`, проект **Domovoy ML Eval** (`domovoy-ml`) → Tracing → Traces. Один трейс = один покупатель (имя `profile P000x (segment)`), и всё для ручной оценки видно уже на корне трейса (`profile_story` в `langfuse_export.py`):

- Input → `shopper`: кто это (`who_they_are`, `persona_label`, `deal_attitude`, `churn_risk`, `promo_sensitivity`, `favorite_categories`) — портрет и мотивация синтетического покупателя.
- Input → `planner_strategy`: что и почему выбрал планировщик — `mechanic`, `target`, `category`, `reward_kind`/`reward_level`, `rationale` (обязана ссылаться на реальное число), `insight_used`, и `offer_shown_to_user`.
- Output → `branch_decisions`: реакция покупателя по трём веткам (`control_x5` массовое промо, `treatment_llm`, `treatment_rules`) — `shopper_verdict`, `shopper_thinking`, `shopper_rationale`, `extra_visits`, `completed_challenge`, `net_effect_rub`.
- Output → `how_to_judge`: 7 вопросов-рубрика (`JUDGE_QUESTIONS`) — по ним человек оценивает трейс без чтения кода.

Вложенные observations (`planner:*`, `actor:*`) держат сырой промпт+ответ LLM рядом с распарсенным JSON — открывать, если надо убедиться, что LLM не читерит и рассуждение настоящее.

### LLM-as-judge: авто-оценка тех же трейсов
`judge-traces` (модуль `app/ml/judge.py`, MiniMax на продовом узле — та же actor-модель, но строго отдельная от планировщика Qwen, поэтому награды планировщика не оцениваются собой) читает `profile_story` и ставит по каждому профилю оценку. Судья — строгий (grounding по G-Eval): промпт `prompts/judge_system.md` задаёт фиксированную траекторию оценки (сначала поле `analysis` проходит нумерованные шаги: портрет покупателя → оффер и честность цифры → инкрементальность → механика → награда → разбор решения актёра по веткам → флаг сговорчивости, и только потом баллы), с якорями рубрики 1–5 и требованием подтверждать высокий балл конкретным числом/полем. Инференс судьи — та же capped-инфраструктура, что у актёра/персон: precheck-гейт и `CapacityLimiter` по `/metrics` узла (флаги `--no-capacity-gate`, `--occupancy-ceiling`, `--precheck-max-occupancy`, `--node-concurrency`, `--judge-metrics-url`). Судья интегрирован прямо в Langfuse рядом с трейсами: на каждый трейс он и вешает Scores (панель Scores), и добавляет `evaluator`-observation `judge:verdict` (полный `analysis` + все баллы + вердикт), поэтому вердикт судьи виден бок о бок с историей покупателя и рубрикой `how_to_judge` — человек и LLM оценивают из одного трейса. Плохие прогоны помечены визуально: трейсу проставляются теги `judge:bad`/`judge:mixed`/`judge:good` (плюс `judge:too_cooperative`/`judge:too_resistant`, если актёр вне характера), а сам `judge:verdict` получает level ERROR (bad) / WARNING (mixed) — по тегам и уровню список Traces фильтруется и подсвечивает провальные.

- 5 числовых дименшенов 1–5 (нормируются в 0–1): `judge_strategy_fit`, `judge_mechanic_choice`, `judge_reward_fit`, `judge_rationale_honesty`, `judge_persona_consistency` (последний оценивает, реально ли действия актёра соответствуют его характеру во всех ветках).
- 2 категориальных: `judge_verdict` ∈ {good, mixed, bad} и `judge_actor_cooperation` ∈ {too_cooperative, consistent, too_resistant} — явная проверка, не слишком ли покупатель сговорчив (взял/выполнил оффер, который скептик его профиля проигнорировал бы). Текст-обоснование судьи лежит в `comment` каждого скора.
- Кросс-трейсовые предложения: после поштучной оценки судья делает мета-проход (`prompts/judge_meta_system.md`, `JUDGE_META_MAX_TOKENS`) и выдаёт структурированные `proposals` — системные проблемы планировщика/актёра, каждая доказана минимум на 2 разных профилях (`JUDGE_MIN_EVIDENCE_PROFILES`). Валидатор выкидывает предложения, чьи `evidence` ссылаются на <2 реальных `profile_id`, поэтому в отчёт попадают только паттерны, реально встреченные в нескольких трейсах. Предложения уезжают отдельным трейсом `judge run summary (seed=N)` (по одному `evaluator`-observation на предложение, severity → level, теги `judge:summary`/`judge:high`/…); выключить — `--no-proposals`.
- `--to json --out build/judge_verdicts.json --proposals-out build/judge_proposals.json` — те же вердикты и предложения в файлы (без сети), для оффлайн-инспекции.

```bash
uv run python -m app.ml.cli judge-traces --in build/eval_small.jsonl --to langfuse   # скоры в Langfuse
uv run python -m app.ml.cli judge-traces --in build/eval_small.jsonl --to json        # вердикты в файл
```

Так и человек (по `how_to_judge` на корне), и LLM-судья (по Scores) оценивают прогон из одного трейса.

### Переиспользуемые отчёты
- `--out-md` — человекочитаемый отчёт (таблица веток: `net_effect`, incr.margin, reward cost, incr.visits, доля ≥8 покупок за 4 недели, completion, relevance hit, доля llm-планов, uplift). Это артефакт для PM — коммить в `docs/ml-rework/eval-report.md`.
- `--out-json` — те же метрики машинно (`EvalReport`) для дальнейшей обработки; `build/` в `.gitignore`, JSON не коммитим.
- Шапка отчёта самодокументирована (planner model / actor model / seed / profiles / horizon / cut / null_test) — по ней прогон повторяется один в один.
- Прогонять один раз на фиксированном `--seed`; новый прогон перезаписывает `--out-md`, поэтому обновлять метрики только вместе с кодом и в одном коммите.

### Проверки перед коммитом ML
```bash
cd dev/backend
uv run pytest tests/unit/ml -q
uv run mypy app/ml tests/unit/ml
uv run ruff check app/ml tests/unit/ml && uv run ruff format --check app/ml tests/unit/ml
```

## Язык

Документация, комментарии в backlog, сообщения коммитов — русский. Код, идентификаторы, названия таблиц и полей API — английский.
