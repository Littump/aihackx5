# Влияние на текущую архитектуру и продукт (record asides)

> Статус: **proposal**. Здесь зафиксировано, что именно в уже принятой архитектуре и продукте
> придётся тронуть, если принимаем LLM-планировщик из
> [ml-solution-architecture.md](ml-solution-architecture.md). Это карта изменений, а не сами изменения —
> код не трогаем, решения `dev/docs/decisions.md` не переспариваем без отдельного согласования.

## 1. Что НЕ меняется (важно для доверия жюри)

- Слои `router → service → database`, pydantic между слоями, raw SQL в `database.py`.
- Экономика денег: формула маржи и cap `40% × incremental_margin` (`economics.py`, `domain-rules.md` §6).
- Принцип «LLM не считает деньги», детерминированные награды (decision #7), объяснимость чисел (decision #6).
- Антифрод precision-first (decision #9), приватность рейтинга (без ФИО/адресов).
- Все числа — в `game_rules.py`, зеркалятся в `domain-rules.md` (тест-инвариант).

## 2. Ключевой сдвиг роли LLM (нужно обновить decisions.md)

| Было | Стало |
|---|---|
| LLM — **только текст** (PRD §7.5, CLAUDE.md: «LLM не назначает награды и не считает деньги») | LLM **планирует ход**: тип челленджа, target, SKU-ссылки, `promo_level` (ординал), `needs_promo` |
| Выбор челленджа — `candidate.build` + `personalization.rank` | Выбор челленджа — LLM Planner; rule-based становится **fallback** |
| Награда — только промо-деньги | LLM выбирает **форму** награды `reward_kind` (`promo` или `ladder` — очки лестницы); величину считает код |
| Челлендж — один шаг | План — последовательность **`steps[]`** (cap `MAX_PLAN_STEPS=2`): самоценная связка сейчас (`steps[0]`) открывает награду на след. неделе (`steps[1]`); активен всегда только один шаг |
| Планировщик без памяти | Планировщик видит `previous_plans` (1–3 прошлых хода со статусом/использованием) и меняет стратегию, если прошлый челлендж не сработал |
| Деньги — Economics Engine | Деньги — Economics Engine (**без изменений**), но вход теперь `promo_level`, а не тип из правил |

Формулировку decision #7 стоит уточнить: «LLM выбирает **уровень** промо и состав челленджа, но **сумму
в рублях/баллах считает только Economics Engine**». Это не отменяет принцип, а уточняет границу.
Рекомендуется добавить новое решение (например #14) «LLM-планировщик + детерминированный валидатор + fallback».

## 3. Изменения по коду (feature-модули)

| Модуль | Изменение |
|---|---|
| `app/features/catalog/` (**новый**) | владелец `sku_catalog`; чтение каталога, подсказки SKU для планировщика |
| `app/features/challenges/candidate.py` | остаётся как **fallback**-стратегия (не удалять) |
| `app/features/challenges/personalization.py` | остаётся как fallback-ранжирование |
| `app/features/challenges/planner.py` (**новый**) | сбор `PlannerInput` (Insight Builder), вызов LLM, приём `ChallengePlan` |
| `app/features/challenges/plan_validator.py` (**новый**) | детерминированная проверка SKU/target/типа/rationale, repair, выбор fallback |
| `app/features/challenges/economics.py` | добавить маппинг `promo_level → доля от max_reward_rub` (новая функция, формула прежняя) |
| `app/features/challenges/service.py` | `refresh_weekly`: сначала planner→validator, при провале — текущий candidate/personalization |
| `app/features/challenges/models.py` | новые модели `ChallengePlan` (`steps[]` из `ChallengeStep`), `PlannerInput` (с `previous_plans`), `PreviousPlan`, `ChurnRisk`, `PromoLevel`, `RewardKind` |
| `app/llm/` | новый `planner_tool.py` (объявление tool `emit_challenge_plan` + `input_schema`), клиент с tool-use forcing и fallback; `domovoy_copy.py` остаётся для текста |
| `app/features/rewards_ladder/` (**новый**, или подмодуль `domovoy`) | награды за опыт по XP/level + tenure, new-user буст, decay; **плюс XP за челленджи с `reward_kind=ladder`** (омниканальная лестница) |
| `app/synthetic/` | добавить генерацию SKU-каталога (`catalog.py`) и LLM-персон поверх числовых профилей |
| `app/eval/` | **история-продолжение (counterfactual)**: обрезаем историю в точке T, продолжаем хвост LLM-пользователем, считаем incremental revenue/margin кодом; **без LLM-as-judge**; relevance §14 — sanity-check |
| `app/simulation/` | ветки `treatment_llm` vs `treatment_rules` vs `control_x5` из одной точки T/seed; бюджет — простой per-user cap (**без knapsack**) |
| `app/features/pm/` | PM view показывает `ChallengePlan` (`steps[]` что выбрала LLM, какие `insight_used`, fallback/valid) |

## 4. Изменения модели данных (миграции)

| Таблица | Изменение |
|---|---|
| `sku_catalog` (**новая**, владелец `catalog`) | `sku_id, name, category, brand, regular_price, typical_promo_depth, is_challenge_eligible, popularity_rank` |
| `receipt_items` | опционально добавить `sku_id` FK на `sku_catalog` (сейчас только `product_name`+`category`) |
| `challenges` | добавить `sku_refs JSONB`, `promo_level`, `needs_promo`, `reward_kind ('promo'|'ladder')`, `plan_step INTEGER`, `plan_group_id`, `unlocks_next BOOLEAN`, `activates_on DATE NULL`, `plan_source ('llm'|'rules')` |
| `llm_plans` (**новая**, владелец `challenges` или `pm`) | аудит: сырой ответ LLM, валидность, repair-count, для объяснимости PM |
| `challenge_types` | расширить enum: `basket`, `streak`, `winback` (сейчас только `frequency`,`category`) |

## 5. Новые константы в `game_rules.py` (+ зеркало в `domain-rules.md`)

- `PROMO_LEVEL_SHARE = {none:0.0, low:0.4, medium:0.7, high:1.0}` (доля от `max_reward_rub`).
- `MAX_PLAN_STEPS = 2`, `PLANNER_PREV_PLANS_MAX = 3` (обобщённая многошаговость + память планировщика).
- `CHURN_RISK_CADENCE_FACTOR = 1.8` (порог `recency_days > factor × cadence_days`).
- `CHALLENGE_LIBRARY = [frequency, category, basket, streak, winback]`.
- `CHALLENGE_LADDER_XP = {low:10, medium:20, high:30}` — бонус-XP поверх `XP_CHALLENGE` в шкалу уровней §8 (не отдельная валюта).
- `PLANNER_REPAIR_MAX = 2`, `PLANNER_SKU_HINT_MAX`, `PLANNER_TIMEOUT_S = 8`.
- Reward ladder: буст-коэффициент для новичков и функция затухания по tenure/level.

## 6. Контракт API (`dev/contracts/openapi.yaml`)

- `ChallengeDetail` (в `dto.py`) получает `sku_refs`, `promo_level`, `plan_source`.
- PM-ручка отдаёт `ChallengePlan` + `insight_used` + `plan_source` (llm/rules).
- Порядок неизменен: сначала `openapi.yaml`, затем backend, затем `make contract-types` (decision #4).

## 7. Влияние на backlog (dev/docs/backlog)

Синхронизировано в новый эпик **[E14 — ML rework](../../dev/docs/backlog/E14-ml-planner.md)** и в доску
`dev/docs/backlog/README.md`. Соответствие компонентов этого документа и задач E14:

| Компонент (этот док) | Задачи E14 |
|---|---|
| Каталог SKU (§3) | BE-024 (миграция), BE-026 (feature `catalog`), AI-009 (генерация в синтетике) |
| Insight Builder (§4) | BE-027 |
| LLM Planner + схема (§5) | AI-008 (`emit_challenge_plan`, tool-use), BE-029 (validator + fallback) |
| Библиотека челленджей (§6) | BE-030 (basket/streak/winback) |
| Economics / promo_level (§7) | BE-025 (константы), BE-028 (`promo_level` → бюджет), BE-031 (`refresh_weekly`) |
| Reward Ladder (§8) | BE-032 |
| Reward Ladder ↔ челленджи (§8) | BE-032 (XP за `reward_kind=ladder`) |
| Синтетическая eval (§9) | AI-010 (история-продолжение, без судьи), AI-011 (3 ветки из точки T + per-user cap), AI-012 (промпт-тюнинг) |
| Контракт + PM view (§6, §11) | BE-033, FE-007 |

`E1-synthetic` (AI-001), `E5-challenges` (BE-010/011/012, AI-004) и `E11-eval-simulation` (AI-005/006/007)
остаются базой: rule-based становится fallback, а не удаляется (см. «Связь с E14» в этих эпиках).

## 8. Порядок безопасного внедрения (не ломая demo/тесты)

1. Каталог SKU + Insight Builder (детерминированные, тестируемые без LLM).
2. `planner` + `plan_validator` с **дефолтным fallback** = текущий rule-based → зелёные тесты без ключа.
3. Подключить LLM tool-use за фиче-флагом; без ключа `plan_source=rules` (как сейчас `copy_source=template`).
4. Reward ladder как отдельный детерминированный модуль.
5. Синтетический eval: сперва на числовых профилях (без LLM-юзера), затем добавить LLM-as-user и X5-baseline.
6. A/B в симуляции: `llm` vs `rules` vs `control_x5` → цифры для PM view и защиты.

## 9. Открытые вопросы для продукт-овнера

- Даём ли LLM в инсайт **сырые последние 10 чеков** или только производные признаки? (дефолт — признаки).
- `promo_level → доля` — фиксируем таблицей (0/40/70/100 %) или калибруем симуляцией?
- Reward ladder: конкретные пороги «новичок → буст», форма затухания, потолок купона; сколько XP даёт
  `reward_kind=ladder`-челлендж относительно уровня.
- `reward_kind`: даём ли LLM свободу выбирать `ladder` vs `promo`, или это жёсткое правило по сегменту/churn.
- `steps[]` (многошаговый план): фиксируем ли `MAX_PLAN_STEPS=2` на хакатоне или сразу открываем 3 шага в неделю подряд.
- Каталог SKU: скрейпим реальные товары X5 или берём синтетический правдоподобный набор для хакатона?
- Горизонт истории для eval-продолжения (12 недель?) и точка обрезки T (середина?) — фиксируем или свипаем.


## 10. Проверка продуктовых инвариантов (по `docs/demo/`)

Сверено с `docs/demo/ПРОДУКТОВЫЕ МАТЕРИАЛЫ.docx` и `PROJECT_DESCRIPTION_INTERMEDIATE_FINAL.md`, чтобы rework
не ломал уже показанные жюри обещания:

| Инвариант из демо-материалов | Где закреплён | Как соблюдён в rework |
|---|---|---|
| Один hero next action на главном экране (не набор равнозначных CTA) | демо §8; `domain-rules.md` §7 | Активен ровно `steps[0]`; `steps[1]` — отложенный, активируется на след. неделе (§5, §7, §10 arch) |
| LLM «получает готовые факты и числа, не назначает скидки и rewards» | демо §4 | LLM выбирает только `reward_kind` и ординальный `promo_level`; рубли/XP считает код (Economics/Ladder) |
| Net = incremental margin − reward cost − 1.5 ₽ инфры/мес | демо §5.1 | Формула net в eval §9 G.4 и AI-010 включает 1.5 ₽ инфры |
| Reward cost ≤ 40 % incremental margin | демо §5.1; `domain-rules.md` §6 | `REWARD_SHARE_MAX=0.40`, `PROMO_LEVEL_SHARE['high']=1.0` = текущий cap, не пробивает маржу |
| Недельный потолок награды 150 баллов | `domain-rules.md` §6 | Применяется **пошагово** (каждый шаг — своя неделя, §7 arch) |
| Главная бизнес-метрика: доля с ≥N покупками за 4 недели, Test vs Control, +2 п.п. | демо §6 | Восстановлена в eval §9 G.4 и AC AI-010/AI-011 |
| XP/уровни L1..L10, награды детерминированы (decision #7) | `domain-rules.md` §8 | `reward_kind=ladder` = бонус-XP поверх `XP_CHALLENGE` в ту же шкалу §8, не параллельная валюта |
| Сегмент regular_mid 3–7 покупок/мес, baseline 6/мес | демо §1, §5 | Инсайт и eval используют тот же сегмент/baseline; формула §7 `frequency` считает headroom к 6 |
| Rule-based recommender как baseline, ML — целевая персонализация | демо §4 | `candidate`+`personalization` сохранены как fallback и как ablation-ветка `treatment_rules` |

Вывод: rework **уточняет** роль LLM (планировщик вместо только-текста) и добавляет многошаговость + память,
но денежные guardrail'ы, hero-инвариант, XP-лестница и бизнес-метрика остаются как в демо-материалах.
