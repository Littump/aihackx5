# E5 — Challenges

## BE-010 candidate + economics
**Файлы:** `app/features/challenges/candidate.py`, `economics.py`, `tests/unit/challenges/`.
**Описание:** `candidate.build(features) -> list[ChallengeDraft]` по §4–5 (frequency при headroom, category при affinity, fallback для пустой истории). `economics.evaluate(draft, features) -> ChallengeEconomics` и `max_reward_points(...)` по §6. `ChallengeDraft` — pydantic-модель в `models.py`: type, category, baseline, target, priority, rationale_features (вложенная модель `RationaleFeatures`).
**AC:**
- пример PRD: baseline 2, target 3, basket 600 → margin 90, max 36, reward 30;
- baseline 1.5, target 3, basket 555 → revenue 832.5, margin 124.875, max 49.95, reward 40 (без промежуточных округлений, floor до кратного 10 только в конце);
- маленькая корзина (basket 150, 2→3) → margin 22.5 → max 9 → reward 0 (только XP);
- reward никогда > 150;
- target для baseline 2 = 3, для 5 = 6, для 6 — кандидата frequency нет;
- category-кандидат только при share ≥ 0.10 и visits ≥ 3, `alcohol` исключён.

## BE-011 генерация и ручки
**Файлы:** `app/features/challenges/{router,dto,service,database}.py`, `personalization.py`, `app/llm/domovoy_copy.py` (заглушка-шаблон, сигнатура из `team.md`), тесты.
**Описание:** `personalization.rank(drafts) -> hero, side` по §7. `service.refresh_weekly(conn, user_id)`: закрыть активные как `expired`, собрать кандидатов, экономику, ранжировать, получить copy через `llm.domovoy_copy.render_challenge`, вставить. `GET /users/{id}/challenges`, `GET .../{challenge_id}`, `POST .../refresh`. Период — с понедельника текущей недели по воскресенье.
**AC:**
- у пользователя всегда ровно один hero после refresh; side ≤ 2, разных типов/категорий;
- `explanation` содержит хотя бы одно число из `rationale_features` (шаблон гарантирует);
- повторный refresh не плодит активные;
- чужой `challenge_id` → 404; поля по контракту, `copy_source=template` без ключа.

## AI-004 LLM copy (владелец: T)
**Файлы:** `app/llm/client.py`, `domovoy_copy.py`, `prompts.py`, `templates.py`, `tests/unit/llm/`.
**Описание:** реализация сигнатур из `team.md` §2. Перед кодом — скилл `claude-api`. Промпт получает draft + features + economics как JSON и обязан вернуть JSON `{title, body, explanation}`; числа из входа в тексте обязательны, финансовых параметров в ответе нет. Таймаут 8 с, одна попытка, затем шаблон. Тесты без сети: клиент мокается, проверяется парсинг, fallback, наличие чисел.
**AC:** без ключа — `source=template`; с моком ответа — `source=llm`, числа baseline/target в тексте; при невалидном JSON — шаблон; explanation ссылается на конкретную feature (категория или частота).

**Исправлено 2026-09-04 (было найдено при FE-D04):** заглушка `domovoy_copy.py` подставляла английские ключи как есть — «Больше bakery», «За month ты сэкономил…». Добавлены `CATEGORY_LABELS`/`PERIOD_LABELS` (те же русские названия, что в `dev/frontend/src/features/home/categoryLabels.ts`, для консистентности между PM view и продуктовыми экранами), тексты переформулированы через кавычки-ёлочки и именительный падеж категории, чтобы не требовать склонения. Актуально и после LLM-планировщика (E14-ml-planner) — при подключении настоящего `render_challenge`/`render_insight` тот же словарь пригодится и там, fallback-путь никуда не денется.

## BE-012 прогресс и награда
**Файлы:** `app/features/challenges/service.py` (`on_receipt`, `record_reward`, `on_receipt_returned`), `database.py`, тесты.
**Описание:** `on_receipt(conn, user_id, receipt) -> list[ChallengeProgressDelta]`: для активных — frequency +1 за counted-чек, category +1 если категория в позициях; при `progress ≥ target` → `completed`, запись в `reward_ledger` (`kind=challenge`, `xp_delta=reward_xp`, `points_delta=reward_points`), `domovoy.add_xp`, обновление streak. `record_reward` — единственная точка записи в ledger. `on_receipt_returned` откатывает прогресс и, если челлендж был закрыт этим чеком, — статус и ledger (отрицательной записью).
**AC:**
- 2 чека при target 3 → progress 2, status active; третий → completed, ledger +50 XP +30 баллов;
- чек `counted=false` не двигает прогресс;
- category-челлендж по `dairy` не двигается чеком без dairy;
- возврат закрывшего чека → status active, progress −1, ledger −30 баллов, XP не отнимаем.

## Связь с E14 (ML rework)

Задачи выше остаются в силе и после переработки. `candidate.py` + `personalization.py` (BE-010/011) не удаляются —
они становятся **fallback**-стратегией, когда LLM-план невалиден или нет ключа. Новый путь выбора челленджа —
LLM-планировщик: см. эпик [E14-ml-planner.md](E14-ml-planner.md) (BE-027 Insight Builder, AI-008 planner, BE-029 validator,
BE-030 новые типы, BE-031 новый `refresh_weekly`). `AI-004` (LLM copy) дополняется планированием, интерфейс
`render_challenge` не ломается. Дизайн — `docs/ml-rework/ml-solution-architecture.md`.
