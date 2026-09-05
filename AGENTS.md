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

### Модели для eval (vLLM на GPU-кластере)
- Кластер `root@inference-node.local`, HGX H100. Два OpenAI-совместимых сервера vLLM подняты бок о бок на GPU 3-6 (TP4, FP8, offline, ctx 32k):
  - Cheap/fast: **Qwen3-VL 27B FP8** — порт `8016`, модель `qwen38-27b-fp8` (для structured JSON слать `chat_template_kwargs.enable_thinking=false`; tool-calling включён). Сервер стартует с `--structured-outputs-config '{"backend":"xgrammar","disable_any_whitespace":true}'` — иначе xgrammar разрешает любой whitespace и Qwen под strict guided JSON зацикливается на пробелах перед enum, сжигая весь лимит токенов (флаг читается только при запуске, per-request не работает; рецепт `/opt/relaunch-qwen.sh` на кластере).
  - Larger: **DeepSeek-V4-Flash** (160B MoE, MLA, kv fp8) — порт `8017`, модель `deepseek-v4-flash`.
- Локально `sshpass` нет → запускать через `nix-shell -p sshpass`. Пароль — в `<pass-file>`.
- Поднять туннель (локальный `18016` → кластерный `8016`, при необходимости `18017` → `8017`) и проверить, что vLLM отвечает:

```bash
nix-shell -p sshpass --run 'sshpass -f <pass-file> ssh -o StrictHostKeyChecking=no -o ExitOnForwardFailure=yes -fN -L 18016:localhost:8016 -L 18017:localhost:8017 root@inference-node.local'
curl -s http://localhost:18016/v1/models   # Qwen
curl -s http://localhost:18017/v1/models   # DeepSeek-V4-Flash
```

- Туннель через SSH может оборваться посреди долгого прогона (оба порта идут через один ssh) — тогда все вызовы после обрыва падают в `fallback_null` и eval получается битым. Держать самовосстанавливающийся туннель в цикле, отдельно от PTY:

```bash
cat > /tmp/tunnel_loop.sh <<'SH'
#!/usr/bin/env bash
while true; do
  nix-shell -p sshpass --run 'sshpass -f <pass-file> ssh -o StrictHostKeyChecking=no -o ExitOnForwardFailure=yes -o ServerAliveInterval=5 -o ServerAliveCountMax=3 -o TCPKeepAlive=yes -o ConnectTimeout=15 -N -L 18016:localhost:8016 -L 18017:localhost:8017 root@inference-node.local'
  sleep 3
done
SH
setsid bash /tmp/tunnel_loop.sh >/tmp/tunnel_loop.log 2>&1 </dev/null & disown
```

- После прогона обязательно гасить туннель: убить цикл и ssh — `pkill -f tunnel_loop.sh`, затем `pgrep -af '1801[67]:localhost'` и `kill <PID>`.

### Перезапуск eval
Из `dev/backend`. Планировщик (награды) и actor (симуляция покупателя) — строго разные модели.
Planner — дешёвый Qwen (`--planner-base-url`/`--planner-model` или `ML_PLANNER_BASE_URL`/`ML_PLANNER_MODEL`);
actor — сильный DeepSeek (`--actor-base-url`/`--actor-model` или `ML_ACTOR_BASE_URL`/`ML_ACTOR_MODEL`).
Дефолты — в `app/ml/config.py` (planner→:8016, actor→:8017):

```bash
cd dev/backend
uv run python -m app.ml.cli run-eval \
  --seed 7 --profiles 50 --horizon 12 --cut 6 --concurrency 3 \
  --planner-base-url http://localhost:18016/v1 \
  --actor-base-url http://localhost:18017/v1 \
  --out-md ../../docs/ml-rework/eval-report.md \
  --out-json build/eval_report.json \
  --trace-out build/eval_traces.jsonl
```

- `--profiles` — размер выборки (AI-012 требует 50); `--seed`, `--horizon`, `--cut` детерминируют историю и точку T, поэтому прогон воспроизводим.
- `--concurrency` (дефолт `config.EVAL_MAX_CONCURRENCY=3`) — сколько профилей считать параллельно. Выше 3 перегружает vLLM (особенно 160B DeepSeek): растёт латентность, вызовы упираются в таймаут и уходят в `fallback_null`. Живой прогон 50 профилей при `--concurrency 3` занимает ~55-60 мин.
- Таймаут одного LLM-вызова — `config.LLM_TIMEOUT_S=180`: DeepSeek на 700 токенов измеренно отвечает ~67 с, при 60 с даже здоровые вызовы таймаутились. Актёр ретраит вызов `config.ACTOR_RETRY_MAX=2` раза (планировщик — 3), после чего честно пишет `fallback_null` (не подменяет решение молча).
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
Актёр (синтетический покупатель) намеренно «пиковый» и малолояльный: играет роль от первого лица, по умолчанию продолжает покупать как обычно (`buy_as_usual`/`ignore`) и включается (`use_offer`) только если оффер проходит его личную планку. Выход строгий: `thinking` → `promo_decision` → `extra_visits` → `completed_challenge` → `rationale` (см. `docs/ml-rework/actor-and-tracing.md`).

```bash
uv run python -m app.ml.cli run-eval --seed 7 --profiles 50 --horizon 12 --cut 6 \
  --trace-out build/eval_traces.jsonl   # + обычные --out-md/--out-json
uv run python -m app.ml.cli export-traces --in build/eval_traces.jsonl --to json --out build/langfuse_generations.json
LANGFUSE_HOST=http://localhost:3000 LANGFUSE_PUBLIC_KEY=pk LANGFUSE_SECRET_KEY=sk \
  uv run python -m app.ml.cli export-traces --in build/eval_traces.jsonl --to langfuse
```

- `--trace-out` пишет JSONL: строка 1 — шапка прогона, далее по профилю (снапшот, `planner_calls`, ветки с решением актёра, сырым ответом LLM и распарсенным JSON — для проверки, что LLM не читерит). `build/` в `.gitignore`.
- `export-traces --to langfuse` заливает по одному trace на профиль и по generation на LLM-вызов; по умолчанию `run-eval --trace-out` делает это сам. Локальный стек — `make langfuse-up` (`deploy/langfuse/`).

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
