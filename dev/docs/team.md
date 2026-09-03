# Команда и зоны ответственности

| Кто | GitHub | Зона |
|---|---|---|
| Роман | Littump | Backend core: receipts, user_features, savings, domovoy, challenges (candidate/economics/personalization), league, referrals, antifraud, pm. Frontend целиком. Инфраструктура, контракт, миграции. |
| Татьяна | tatiana-stlv | Данные и ИИ: `app/synthetic/` (генератор пользователей и чеков с профилями и фрод-паттернами), `app/llm/` (тексты Домового, explanation, insight, промпты и fallback), `app/eval/` (relevance hit rate на 30–50 профилях), `app/simulation/` (control vs treatment, отчёт для PM view). |
| Анна | anna-kaz | Продуктовые документы, приоритеты, демо-сценарий, презентация. |

Префиксы задач: `BE-` и `FE-` — Роман, `AI-` — Татьяна, `INF-` — Роман, `DOC-` — Анна.

## Как стыкуемся

Зоны не пересекаются по файлам. Стык — через три фиксированных интерфейса. Их менять можно только вместе.

### 1. Синтетика → база
`app/synthetic` пишет напрямую в таблицы `stores`, `users`, `receipts`, `receipt_items` по `data-model.md` через функции `database.py` соответствующих features (`users.database.insert_user`, `receipts.database.insert_receipt`). Никаких своих таблиц. Профили пользователей: `regular_mid` (основной, 3–7 покупок/мес), `light`, `heavy`, `dormant`; 3 % с фрод-паттернами из `domain-rules.md` §11. Параметры CLI: `--users`, `--weeks`, `--seed`, `--fraud-share`.

### 2. LLM-модуль → challenges
```python
# app/llm/domovoy_copy.py
class ChallengeCopy(BaseModel):
    title: str
    body: str
    explanation: str
    source: Literal["llm", "template"]

async def render_challenge(*, challenge: ChallengeDraft, features: UserFeatures) -> ChallengeCopy: ...
async def render_insight(*, features: UserFeatures, savings: SavingsSummary) -> str: ...
```
`ChallengeDraft` и `UserFeatures` — pydantic-модели из `challenges/models.py` и `user_features/models.py`, `SavingsSummary` — из `savings/models.py`. Модуль не ходит в базу и не считает числа: все числа приходят в аргументах и должны попасть в текст как есть. Без ключа или при ошибке — шаблон, `source="template"`. Пока модуль не готов, в core лежит заглушка с шаблоном, чтобы ничего не блокировать.

### 3. Eval и Simulation → pm
`app/eval` и `app/simulation` — CLI: `uv run python -m app.eval --profiles 50`, `uv run python -m app.simulation --users 5000 --weeks 8`. Читают базу через `service.py` features, пишут одну строку в `eval_runs` / `simulation_runs` через `pm.database`. Формат `results` JSONB — в `data-model.md`. PM view читает последнюю строку.

## Правило вежливости

Нужно поменять что-то в чужой зоне — пишешь в чат и делаешь отдельным коммитом с ID задачи. Нашёл баг в чужом — заводишь задачу в backlog, не чинишь молча.

### 4. LLM-планировщик → challenges (E14, proposal)

После ML-rework LLM не только рендерит текст, но и **планирует** челлендж. Стык — ещё один фиксированный интерфейс:
```python
# app/llm/planner.py  (зона Татьяны)
async def plan(*, planner_input: PlannerInput) -> ChallengePlan | None: ...  # None → детерминированный fallback
```
`PlannerInput` собирает `challenges/insight.py`, `ChallengePlan` валидирует `challenges/plan_validator.py`
(зона Романа). LLM не возвращает рубли/баллы — только `promo_level`; деньги считает `economics.py`. Новая feature
`catalog` (`sku_catalog`) — зона Романа; генерация каталога в `app/synthetic/catalog.py` — зона Татьяны.
Полный дизайн и границы — `docs/ml-rework/`.
