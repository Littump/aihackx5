# E14 — ML rework: LLM-планировщик челленджей

Переработка ML-части: hand-rolled рекоммендер (`candidate` + `personalization`) заменяется на дешёвую
LLM в роли time-series / insight-аналитика, которая **планирует** следующий челлендж строгой схемой
(structured output через Anthropic tool-use) поверх фиксированного каталога SKU. Деньги по-прежнему считает
статический Economics Engine; LLM задаёт только ординальный `promo_level`. Rule-based остаётся **fallback**.

Дизайн и обоснование — `docs/ml-rework/ml-solution-architecture.md`, карта изменений —
`docs/ml-rework/product-and-architecture-modifications.md`. Все числа — `simulation assumptions`.

Границы зон: `app/features/*`, миграции, контракт — Роман (`BE-`/`FE-`); `app/llm/`, `app/eval/`,
`app/simulation/`, `app/synthetic/` — Татьяна (`AI-`).

---

## BE-024 Миграция 003: каталог, план, расширение челленджей (владелец: R)
**Файлы:** `dev/backend/migrations/003_ml_planner.sql`, `tests/e2e/test_migration_*`.
**Описание:**
- `sku_catalog` (владелец `catalog`): `sku_id TEXT PK, name TEXT, category TEXT CHECK IN game_rules.CATEGORIES,
  brand TEXT NULL, regular_price NUMERIC(12,2), typical_promo_depth NUMERIC(4,3), is_challenge_eligible BOOLEAN,
  popularity_rank INTEGER`, индекс `(category, popularity_rank)`.
- `receipt_items.sku_id TEXT NULL FK sku_catalog ON DELETE SET NULL` (обратно совместимо: `product_name`+`category` остаются).
- `challenges`: `+ sku_refs JSONB NOT NULL DEFAULT '[]'`, `+ promo_level TEXT CHECK IN ('none','low','medium','high')`,
  `+ needs_promo BOOLEAN NOT NULL DEFAULT false`, `+ reward_kind TEXT NOT NULL DEFAULT 'promo' CHECK IN ('promo','ladder')`,
  `+ plan_step INTEGER NOT NULL DEFAULT 0` (индекс шага в плане), `+ plan_group_id TEXT NULL` (связывает шаги одного плана),
  `+ unlocks_next BOOLEAN NOT NULL DEFAULT false`, `+ activates_on DATE NULL` (неделя активации отложенного шага),
  `+ plan_source TEXT NOT NULL DEFAULT 'rules' CHECK IN ('llm','rules')`. Активен всегда только `plan_step=0` текущей недели.
- `challenges.type` CHECK расширить: `frequency, category, basket, streak, winback`.
- `llm_plans` (владелец `challenges`): `id, user_id FK, raw_output JSONB` (весь план с `steps[]`), `is_valid BOOLEAN,
  repair_count INTEGER, plan_source TEXT, created_at` — аудит для PM view (полный многошаговый план).
**AC:** миграция применяется и откатывается; `test_migrations` видит новые таблицы/колонки; старые e2e зелёные (дефолты не ломают BE-011/012).

## BE-025 Константы планировщика в `game_rules.py` (владелец: R)
**Файлы:** `dev/backend/app/game_rules.py`, зеркало `dev/docs/domain-rules.md`, `tests/unit/test_game_rules.py`.
**Описание:**
- `PROMO_LEVEL_SHARE = {"none":0.0,"low":0.4,"medium":0.7,"high":1.0}` — доля от `max_reward_rub`.
- `CHURN_RISK_CADENCE_FACTOR = 1.8` (порог `recency_days > factor × cadence_days`).
- `CHALLENGE_LIBRARY = ("frequency","category","basket","streak","winback")`.
- `PLANNER_REPAIR_MAX = 2`, `PLANNER_SKU_HINT_MAX = 12`, `PLANNER_TIMEOUT_S = 8`.
- `MAX_PLAN_STEPS = 2` — максимум последовательных шагов в одном решении LLM (структура рассчитана на N, cap = 2).
- `PLANNER_PREV_PLANS_MAX = 3` — сколько прошлых планов подаём в `previous_plans`.
- `REWARD_KINDS = ("promo","ladder")`; `CHALLENGE_LADDER_XP = {"low":10,"medium":20,"high":30}` — **бонус-XP поверх** `XP_CHALLENGE`(+50) при `reward_kind=ladder`, начисляется в ту же шкалу уровней §8 (не отдельная валюта; assumptions).
- Reward ladder: `LADDER_NEWBIE_BOOST`, `LADDER_DECAY_PER_LEVEL`, `LADDER_COUPON_MAX_RUB` (значения — assumptions).
**AC:** новый раздел §17 в `domain-rules.md` совпадает с `game_rules.py` (тест соответствия, как в BE-003); `PROMO_LEVEL_SHARE['high'] == 1.0` = текущий cap, т.е. `high` не пробивает маржу; `MAX_PLAN_STEPS == 2` и присутствует в §17; `CHALLENGE_LADDER_XP` документирован как бонус-XP в шкалу §8, не отдельный счёт.

## BE-026 Feature `catalog` (владелец: R)
**Файлы:** `dev/backend/app/features/catalog/{router,dto,models,service,database}.py`, тесты.
**Описание:** чтение `sku_catalog`; `get_hints(category|None, limit) -> list[SkuHint]` для планировщика (топ по `popularity_rank`, только `is_challenge_eligible`); `GET /catalog?category=` для отладки/демо.
**AC:** возвращает только eligible SKU; alcohol/tobacco отфильтрованы; пустая категория → топ по популярности; e2e на ручку.

## BE-027 Insight Builder (владелец: R)
**Файлы:** `dev/backend/app/features/challenges/insight.py`, `models.py` (`PlannerInput`, `CategoryTimeseries`, `ChurnRisk`, `PreviousPlan`), `tests/unit/challenges/test_insight.py`.
**Описание:** детерминированно собирает `PlannerInput` из `user_features` + чеков: агрегаты, `category_timeseries`
(cadence_days, days_overdue, share, visits по 3–5 топ-категориям), `churn_risk` (`none|elevated|high` по §17),
`catalog_hint` из BE-026, `previous_plans` — последние `PLANNER_PREV_PLANS_MAX` hero-плана из `challenges`/`llm_plans`
(`week`, `challenge_type`, `reward_kind`, `promo_level`, `status` `completed|expired|active`, `used`). Сырые чеки по
умолчанию не включаются (флаг `include_receipts`). Никакого LLM, никакой арифметики в LLM.
**AC:** `churn_risk` считается по порогу `CHURN_RISK_CADENCE_FACTOR`; для пустой истории — безопасные дефолты (как §3 sentinel), `previous_plans=[]`; `previous_plans` не длиннее `PLANNER_PREV_PLANS_MAX` и упорядочен свежими вперёд; JSON сериализуется < ~1.5 КБ на дефолте; unit на каждое поле.

## BE-028 `promo_level` → бюджет в `economics.py` (владелец: R)
**Файлы:** `dev/backend/app/features/challenges/economics.py`, `tests/unit/challenges/test_economics.py`.
**Описание:** `reward_points_for_level(economics, promo_level) -> int` = `max_reward_points(max_reward_rub × PROMO_LEVEL_SHARE[level])`. Формула маржи §6 не меняется. `none`/`needs_promo=false` → 0 баллов (только XP). При `reward_kind='ladder'` Economics возвращает 0 рублей/баллов — награду отдаёт Reward Ladder (BE-032).
**AC:** пример PO (600 ₽, 2→3): `high` → 30 баллов (= текущий результат), `medium` → 20, `low` → 10, `none` → 0; ни один уровень не превышает `40% × margin`; reward ≤ 150; `reward_kind='ladder'` → 0 денег.

## BE-029 Plan Validator + fallback (владелец: R)
**Файлы:** `dev/backend/app/features/challenges/plan_validator.py`, `tests/unit/challenges/test_plan_validator.py`.
**Описание:** валидирует `ChallengePlan` = `steps[]` (`1..MAX_PLAN_STEPS`) + `insight_used` + `rationale`. Общие правила на **каждый** шаг: `challenge_type ∈ CHALLENGE_LIBRARY`; `category ∈ CATEGORIES` и не в `CHALLENGE_EXCLUDED_CATEGORIES`; каждый `sku_id ∈ sku_catalog` и eligible; `target` в коридоре §5/§14; `promo_level`↔`needs_promo` согласованы; `reward_kind ∈ REWARD_KINDS` (при `ladder` → `needs_promo=false`). Правила плана: `1 ≤ len(steps) ≤ MAX_PLAN_STEPS`; `unlocks_next=true` только у не-последнего шага, у последнего `false`; `rationale` содержит число из инсайта (§14 п.4). При провале — repair (до `PLANNER_REPAIR_MAX`), затем fallback на `candidate.build` + `personalization.rank` (одношаговый план). Возвращает `(list[ChallengeDraft], plan_source)` — по одному drafту на шаг, активен только `steps[0]`.
**AC:** невалидный SKU → repair→fallback (`plan_source='rules'`, один шаг); target вне коридора → repair; `reward_kind='ladder'` с `needs_promo=true` → нормализуется; `unlocks_next=true` у последнего шага → отклоняется/repair; `len(steps) > MAX_PLAN_STEPS` → отклоняется; валидный план → `ChallengeDraft`-ы эквивалентны по полям существующему; unit на каждое правило.

## BE-030 Библиотека челленджей: basket / streak / winback (владелец: R)
**Файлы:** `dev/backend/app/features/challenges/{service,candidate,models}.py`, тесты.
**Описание:** предикаты прогресса `_matches_receipt` для новых типов: `basket` (в чеке ≥ K из `sku_refs`/категорий — **самоценная связка**), `streak` (не прервать серию недель — уже есть в domovoy, связать), `winback` (первый counted-чек после просрочки кадэнса). Правила target для новых типов в §5-подобном виде. Поддержать **многошаговый план (`steps[]`)**: активен только `steps[0]`; при его закрытии, если `unlocks_next=true`, создаётся **отложенный** `steps[1]` с `activates_on` = следующая неделя (один активный набор на неделю, §7). Rule-based `candidate` учит новые типы как fallback-кандидатов там, где это тривиально (иначе fallback = frequency/category).
**AC:** basket-челлендж двигается только при попадании SKU/категорий; winback закрывается первым визитом; закрытие шага с `unlocks_next=true` создаёт ровно один отложенный шаг на след. неделю; в один момент активен ровно один hero; возврат откатывает как в BE-012; unit на каждый предикат.

## BE-031 `refresh_weekly` через planner (владелец: R)
**Файлы:** `dev/backend/app/features/challenges/service.py`, `database.py`, тесты.
**Описание:** `refresh_weekly`: `insight.build` (вкл. `previous_plans`) → `llm.planner.plan` (AI-008) → `plan_validator` (BE-029) → для **`steps[0]`** маршрутизация по `reward_kind`: `promo` → economics `promo_level` (BE-028), `ladder` → reward ladder бонус-XP (BE-032) → copy → insert как активный hero; `steps[1]` (если есть) пишется отложенным (`plan_step=1`, `activates_on`=след. неделя, не активен). Пишет `llm_plans` (весь план), `plan_source`, `reward_kind`, `plan_group_id`. Без ключа/при ошибке — детерминированный fallback (`plan_source='rules'`, `reward_kind='promo'`, один шаг), как сейчас `copy_source='template'`.
**AC:** ровно один активный hero после refresh (даже при 2 шагах); с моком плана — `plan_source='llm'`, `reward_kind='promo'` влияет на `reward_points`, `reward_kind='ladder'` → 0 денег + бонус-XP; `steps[1]` создан отложенным и не активен; без ключа — `plan_source='rules'`, поведение = текущему BE-011; повторный refresh не плодит активные.

## BE-032 Reward Ladder (владелец: R)
**Файлы:** `dev/backend/app/features/domovoy/ladder.py` (чистая функция) + запись через `domovoy.service`, тесты.
**Описание:** награда за опыт по шкале XP/level (та же шкала уровней §8, L1..L10) + `tenure_weeks`: ценность выше для новичков, затухает по уровню (`LADDER_*`). Форма — XP/предмет/купон (₽-потолок `LADDER_COUPON_MAX_RUB`). Величину считает код, вне LLM и вне Economics. Начисляется на повышении уровня. **Плюс `grant_challenge_xp(promo_level) -> int` по `CHALLENGE_LADDER_XP`**: когда шаг закрыт с `reward_kind='ladder'`, начисляем **бонус-XP поверх** `XP_CHALLENGE`(+50) в ту же шкалу §8 (не отдельная валюта; омниканальная лестница, без промо-денег).
**AC:** новичок (L1) получает купон > опытного (L8); монотонное затухание; купон ≤ потолка; `grant_challenge_xp('high')==30` и суммируется с `XP_CHALLENGE` в общий XP §8; закрытие ladder-шага двигает уровень §8 и приближает след. подарок; детерминированно; unit.

## BE-033 Контракт: план в API + PM (владелец: R)
**Файлы:** `dev/contracts/openapi.yaml`, `challenges/dto.py`, `pm/dto.py`, `make contract-types`, тесты.
**Описание:** `ChallengeDetail` += `sku_refs`, `promo_level`, `reward_kind`, `plan_step`, `unlocks_next`, `plan_source`; PM-схема += `ChallengePlanAudit` (`insight_used`, `reward_kind`, `steps` весь план, `plan_source`, `is_valid`, `repair_count`). Порядок: yaml → backend → типы (decision #4).
**AC:** `contract-check` зелёный; фронт-типы обновлены; поля (`reward_kind`, `plan_step`, `unlocks_next`) отдаются ручкой challenges, весь `steps[]`-план — ручкой pm.

---

## AI-008 LLM Challenge Planner (владелец: T)
**Файлы:** `dev/backend/app/llm/planner.py`, `planner_tool.py`, `prompts.py`, `tests/unit/llm/test_planner.py`.
**Описание:** объявляет tool `emit_challenge_plan` с `input_schema` (схема ниже), вызывает Anthropic с
`tool_choice={"type":"tool","name":"emit_challenge_plan"}` (schema-constrained эквивалент — у Anthropic нет strict-флага),
парсит в `ChallengePlan`. Промпт получает `PlannerInput` (BE-027) как JSON; роль — «аналитик, выбери один следующий
челлендж, деньги не назначай». Тайм-аут `PLANNER_TIMEOUT_S`, одна попытка + repair-hook для BE-029, затем сигнал fallback.
Промпт получает `previous_plans` (BE-027) и вправе спланировать до `MAX_PLAN_STEPS` шагов (`steps[]`), думая на несколько недель вперёд. Тесты без сети: клиент мокается.

Сигнатура и модели (стык с challenges):
```python
# app/llm/planner.py
class ChallengeStep(BaseModel):
    challenge_type: Literal["frequency","category","basket","streak","winback"]
    target: int
    category: str | None
    sku_refs: list[str]            # 0..3 sku_id
    reward_kind: Literal["promo","ladder"]     # promo = деньги (Economics); ladder = бонус-XP (Reward Ladder §8)
    promo_level: Literal["none","low","medium","high"]
    needs_promo: bool
    deadline_days: int
    unlocks_next: bool             # True = закрытие шага открывает следующий шаг на след. неделе

class ChallengePlan(BaseModel):
    steps: list[ChallengeStep]     # 1..MAX_PLAN_STEPS (2); активен только steps[0]
    insight_used: list[str]
    rationale: str

async def plan(*, planner_input: PlannerInput) -> ChallengePlan | None: ...  # None → fallback
```

`emit_challenge_plan` `input_schema` (план = массив `steps` из плоских шагов; enum'ы, каждое поле с `description`; `maxItems: 2` = `MAX_PLAN_STEPS`):
```jsonc
{
  "type": "object",
  "additionalProperties": false,
  "required": ["steps","insight_used","rationale"],
  "properties": {
    "steps": {
      "type": "array",
      "minItems": 1,
      "maxItems": 2,
      "description": "1..MAX_PLAN_STEPS последовательных шагов; активен всегда только steps[0]",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["challenge_type","target","category","sku_refs","reward_kind","promo_level","needs_promo","deadline_days","unlocks_next"],
        "properties": {
          "challenge_type": {"enum": ["frequency","category","basket","streak","winback"], "description": "тип из библиотеки"},
          "target": {"type": "integer", "minimum": 1, "description": "цель за неделю; код валидирует коридор относительно baseline"},
          "category": {"type": ["string","null"], "enum": ["dairy","bakery","fruits_veg","meat_fish","grocery","snacks","drinks","alcohol","household","beauty","ready_food","other", null], "description": "макрокатегория или null"},
          "sku_refs": {"type": "array", "items": {"type": "string"}, "maxItems": 3, "description": "sku_id ИЗ каталога, будут проверены на существование"},
          "reward_kind": {"enum": ["promo","ladder"], "description": "promo = скидка/баллы (деньги считает код); ladder = бонус-XP в шкалу опыта (§8)"},
          "promo_level": {"enum": ["none","low","medium","high"], "description": "ординал агрессивности промо; рубли считает код, НЕ ты"},
          "needs_promo": {"type": "boolean", "description": "false = шаг самоценен, промо не тратим"},
          "deadline_days": {"type": "integer", "minimum": 1, "maximum": 14, "description": "код клампит к границам недели"},
          "unlocks_next": {"type": "boolean", "description": "true = выполнение шага открывает следующий шаг; у последнего шага false"}
        }
      }
    },
    "insight_used": {"type": "array", "items": {"type": "string"}, "description": "ключи признаков инсайта, которые реально использованы"},
    "rationale": {"type": "string", "maxLength": 200, "description": "объяснение со ссылкой на число из инсайта"}
  }
}
```
**AC:** без ключа → `plan` возвращает `None` (→ fallback); с моком tool-use → валидный `ChallengePlan` c `steps[]` (1..2) и `reward_kind`, деньги в ответе отсутствуют; невалидный ответ → `None`; промпт не просит рубли/баллы, но просит выбрать `reward_kind` и (опц.) второй шаг в `steps[]`, опираясь на `previous_plans`.

## AI-009 Каталог SKU в синтетике + LLM-персоны (владелец: T)
**Файлы:** `dev/backend/app/synthetic/catalog.py`, `profiles.py`, тесты.
**Описание:** `catalog.py` генерирует 200–500 SKU (по 15–40 на 12 категорий) с ценами/промо-глубиной/популярностью,
пишет в `sku_catalog` через `catalog.database`; чеки в генераторе ссылаются на `sku_id`. Персоны поверх числовых
сегментов («студент за снеками», «ЗОЖ», «вечерний после спорта») — текст от LLM, числовые параметры от кода, укоренены в истории.
**AC:** каталог детерминирован при `--seed`; alcohol помечен `is_challenge_eligible=false`; чеки ссылаются на существующие SKU; распределения сегментов не изменились относительно AI-001 (± 20 %).

## AI-010 Eval: продолжение истории (counterfactual, без судьи) (владелец: T)
**Файлы:** `dev/backend/app/eval/{continuation,metrics}.py`, тесты.
**Описание:** ядро оценки без LLM-as-judge (§9): полная история профиля (LLM-as-user) → **обрезка в точке T** →
инсайт по «прошлому» → подстановка оффера ветки → LLM-as-user **дописывает хвост** с офером в контексте →
**детерминированный** подсчёт incremental visits/purchases/revenue/margin и `net_effect = incremental margin − reward cost − 1.5 ₽ инфра/мес` (формула net из демо-материалов §5.1) по формулам §6/§7. **Главная бизнес-метрика (демо §6):** доля пользователей с **≥ N покупками за 4 недели** (гипотеза ≥ 8), Test vs Control, целевой **+2 п.п.**. relevance (§14) остаётся sanity-check плана. Пишет в `eval_runs.details`.
**AC:** при uplift=0 хвосты веток совпадают и net_effect ≤ 0; деньги/визиты считает код, не судья; фиксированный
`--seed` и точка T воспроизводят хвост; отчёт содержит incremental revenue/margin, **долю ≥N покупок за 4 недели (Test vs Control)** и relevance hit rate; `net_effect` вычитает 1.5 ₽ инфры; unit на подсчёт по хвосту.

## AI-011 Simulation: 3 ветки из одной точки T (владелец: T)
**Файлы:** `dev/backend/app/simulation/{model,report}.py`, тесты.
**Описание:** ветки `control_x5` (baseline-оффер X5), `treatment_llm` (планировщик), `treatment_rules` (текущий rule-based) — все продолжают хвост из **одной точки T и одного seed персоны** (честный counterfactual, §9 ветки G.3). Бюджет — простой **per-user cap** = `max_reward_rub`, **без knapsack/онлайн-аллокатора**. PM-отчёт: суммарные промо-расходы vs суммарный incremental margin. Параметры из `SIMULATION_DEFAULTS`.
**AC:** при uplift 0 net_effect ≤ 0 и доли равны; при дефолтах `treatment_llm` net_effect > 0 и доля пользователей с ≥N покупками за 4 недели выше, чем в `control_x5`; ни один per-user reward не превышает `max_reward_rub`; все параметры помечены `assumptions=true`; 5000×8 недель < 60 с.

## AI-012 Промпт-тюнинг планировщика (владелец: T)
**Файлы:** `app/llm/prompts.py`, `dev/docs/eval-report.md`.
**Описание:** прогнать AI-010 с реальным ключом на 50 профилях: valid-plan rate высокий, fallback rate < 20 %, число из инсайта в `rationale` в 100 % валидных планов, net_effect/incremental margin `treatment_llm` vs `control_x5` измерен на продолжении истории; зафиксировать финальный промпт и few-shot.
**AC:** отчёт приложен в `dev/docs/eval-report.md`; fallback rate < 20 %; нет финансовых полей в ответах LLM; net_effect `treatment_llm` ≥ `control_x5` на выборке (или зафиксировано, почему нет).

---

## FE-007 PM view: план LLM (владелец: R)
**Файлы:** `dev/frontend/src/features/pm/*`, тесты.
**Описание:** в карточке PM показать `ChallengePlanAudit`: `steps[]` (тип/`promo_level`/`sku_refs`/`reward_kind`/`unlocks_next` по шагам, с пометкой активного `steps[0]`), `insight_used`, `plan_source` (llm/rules), `is_valid`/`repair_count`, и что деньги посчитал Economics, а не LLM.
**AC:** видно `plan_source` и что при fallback это честно помечено; многошаговый план отображается как последовательность с активным `steps[0]`; поля из BE-033.

---

## Связь с существующими задачами

- **BE-010/011/012 (rule-based)** остаются `done` и работают как **fallback** — не удаляем.
- **AI-004 (LLM copy)** дополняется: LLM теперь и планирует (AI-008), и рендерит текст; интерфейс `render_challenge` не ломаем.
- **AI-005 (relevance eval)** расширяется в AI-010; **AI-006 (simulation)** — в AI-011; **AI-007 (промпт-тюнинг текста)** — соседний с AI-012 (тюнинг плана).
- **BE-022/FE-006 (PM view)** дополняются BE-033/FE-007.
