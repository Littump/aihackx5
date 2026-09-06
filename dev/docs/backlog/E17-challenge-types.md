# E17 — Единый словарь типов челленджей и интеграция планировщика

Закрываем разрыв между тремя разъехавшимися наборами типов челленджей: продуктовые
доки (`PRODUCT.md` — 7 «типов», `mechanics.md` — 5), ML-песочница (`app/ml/` — 6:
`frequency, category, basket, streak, replenishment, collection`) и production-backend
(`app/features/challenges` + `domain-rules.md` — только `frequency, category`).
Сейчас реально доведены до чеко-проверяемого выполнения лишь два типа; `basket`,
`replenishment`, `collection` в `app/ml/` существуют как ярлык в промпте актёра без
тип-специфичной семантики (`baseline_for_step` даёт 0 всем, кроме `frequency`; eval в
`app/ml/eval.py` считает эффект как `extra_visits × avg_basket` независимо от типа).
Планировщик из `docs/ml-rework/` был собран в `app/ml/` как самодостаточный eval и в
production challenges не интегрирован (миграции `003_ml_planner.sql` нет, feature
`catalog`, `planner.py`, `plan_validator.py` в `app/features` отсутствуют).

Этот эпик сводит всё к одному канону и даёт каждому оставшемуся типу настоящее
правило прогресса по чеку в backend и честную completion-семантику в eval.

## Продуктовое решение (принято)

- Канонические типы челленджа — ровно **5**: `frequency`, `category`, `basket`,
  `replenishment`, `collection`. Каждый — персональная недельная цель, измеримая по чекам,
  выше личного baseline.
- `streak` **не тип челленджа**, а XP/лига-механика (личная серия, `domain-rules.md`
  §8/§9: `XP_STREAK_4W`, `LEAGUE_SCORE_STREAK_*`, ачивка `streak_4`). Убираем `streak` из
  `CHALLENGE_LIBRARY` и из типов в ML.
- `neighbors` («Соседи») **не персональный челлендж**, а командная цель лиги. В список
  типов челленджа не входит.
- Денежные guardrail (cap `40% × incremental_margin`, недельный потолок 150 баллов,
  «LLM не считает деньги») — без изменений; расширяем только словарь типов и их прогресс.

Порядок выполнения — по `deps`. Границы зон: `app/features/*`, миграции, контракт,
`game_rules.py` — Роман (`BE-`); `app/ml/*` и eval — Татьяна (`AI-`); продуктовые доки — Анна (`DOC-`).

---

## DOC-003 Канонизировать типы челленджей в доках (владелец: A)
**Файлы:** `docs/product-analysis/mechanics/PRD.md`, `dev/docs/domain-rules.md` (§4/§5),
`docs/product-analysis/PRODUCT.md`, `docs/product-analysis/mechanics/mechanics.md`.
**Описание:** одна таблица канонических 5 типов — для каждого: что просит у пользователя
(user ask), правило прогресса по чеку, формула target, источник финансирования (сеть/поставщик).
Явно зафиксировать, что `streak` — XP/лига-механика, а `neighbors` — цель лиги, и убрать их из
списков типов в `PRODUCT.md`/`mechanics.md`. PRD становится источником истины по типам.
**AC:** PRD и `domain-rules.md` перечисляют ровно 5 типов и совпадают между собой; `streak`/`neighbors`
помечены как отдельные механики со ссылкой на свои разделы; в `PRODUCT.md`/`mechanics.md` не осталось
типов вне канона; таблица ссылается на `game_rules.CHALLENGE_LIBRARY`.

## BE-034 Библиотека типов и правила target/predicate в `game_rules.py` (владелец: R)
**Файлы:** `dev/backend/app/game_rules.py`, зеркало `dev/docs/domain-rules.md` §4/§5,
`dev/backend/tests/unit/test_game_rules.py`.
**Описание:** `CHALLENGE_LIBRARY = ("frequency","category","basket","replenishment","collection")`
(без `streak`). Пороги и формулы для новых типов как именованные константы (без магии в сервисах):
`basket` — целевая сумма чека от `avg_basket` (например `BASKET_TARGET_UPLIFT`); `replenishment` —
условие просроченной категории через `cadence_days`/`days_overdue`; `collection` — минимальное число
различных SKU/подкатегорий (`COLLECTION_MIN_DISTINCT`). Формулы target новых типов — в §5 domain-rules.
**AC:** тест соответствия `domain-rules.md ↔ game_rules.py` (как BE-003) зелёный; `streak` отсутствует
в `CHALLENGE_LIBRARY`; все новые пороги задокументированы и покрыты unit.

## BE-035 Миграция: расширить `challenges.type` + `sku_refs` (владелец: R)
**Файлы:** `dev/backend/migrations/005_challenge_types.sql`, `dev/backend/tests/e2e/test_migration_*`.
**Описание:** `challenges.type` CHECK → `frequency, category, basket, replenishment, collection`;
`+ sku_refs JSONB NOT NULL DEFAULT '[]'` (для `collection`/SKU-целей). `streak` в CHECK не добавляется.
Обратная совместимость: существующие `frequency`/`category` и их прогресс не ломаются.
**AC:** миграция применяется и откатывается; `test_migrations` видит новый CHECK и колонку; старые e2e
(BE-011/BE-012) зелёные на дефолтах.

## BE-036 Прогресс и выполнение новых типов (владелец: R)
**Файлы:** `dev/backend/app/features/challenges/{service,database,models}.py`,
`dev/backend/tests/unit/challenges/*`, `dev/backend/tests/e2e/*`.
**Описание:** чеко-проверяемое выполнение для каждого нового типа: `basket` — сумма `paid_total`
counted-чеков в периоде ≥ target (в руб), а не число визитов; `replenishment` — `+1` за counted-чек,
содержащий просроченную целевую категорию; `collection` — число различных SKU/подкатегорий из целевого
набора ≥ target. Возврат чека откатывает прогресс и награду, как в BE-012.
**AC:** unit на предикат каждого типа; e2e: чек двигает прогресс своего типа и не двигает чужой;
возврат откатывает; `basket` считает рубли, а не визиты.

## BE-037 Candidate и economics для новых типов (владелец: R)
**Файлы:** `dev/backend/app/features/challenges/{candidate,economics,personalization}.py`, тесты.
**Описание:** `candidate.build` генерирует кандидатов `basket`/`replenishment`/`collection` по условиям §4;
priority для них; `economics` считает max reward от инкремента для каждого типа (target/ожидаемый эффект),
без магических констант. hero/side не дублируют тип и категорию.
**AC:** кандидаты новых типов появляются на подходящих профилях и не появляются на неподходящих (unit);
экономика каждого типа в пределах cap 40%; hero/side разнотипны; e2e на генерацию набора.

## AI-013 Свести `app/ml` к канону + честная completion-семантика в eval (владелец: T)
**Файлы:** `dev/backend/app/ml/{config,schemas,rules,eval,user_sim}.py`,
`dev/backend/tests/unit/ml/*`, `docs/ml-rework/eval-report.md`.
**Описание:** привести `CHALLENGE_LIBRARY`/`ChallengeType` к канону из 5 типов (убрать `streak`).
Дать eval тип-специфичное выполнение вместо «всё = extra_visits»: `basket` — рост суммы чека,
`replenishment` — визит в просроченную целевую категорию, `collection` — разнообразие SKU; чтобы
метрики мерили механику, а не только визиты. Перегенерировать отчёт на фиксированном `--seed` в том же коммите.
**AC:** `uv run pytest tests/unit/ml -q` зелёный; `ChallengeType` == 5 канонических; `streak` отсутствует;
трейсы показывают тип-специфичный расчёт выполнения; `eval-report.md` перегенерирован вместе с кодом;
null-инвариант (uplift 0 → ветки совпадают) сохранён.

## BE-038 Интеграция планировщика в production challenges (владелец: R, поддержка T)
**Файлы:** `dev/backend/app/features/challenges/{planner,plan_validator}.py` (новые, тонкая обёртка над
логикой `app/ml`), `service.py` (refresh), тесты; при необходимости общий модуль словаря типов.
**Описание:** план планировщика (тип из канона, target, `sku_refs`, ординальный `reward_level`) проходит
детерминированный валидатор и ложится в `challenges` как hero/side; текущий rule-based (candidate +
personalization) остаётся **fallback**. Без ключа/при ошибке — детерминированный fallback, чтобы тесты и
демо работали. Деньги по-прежнему считает `economics` (LLM не назначает суммы).
**AC:** e2e: refresh с планировщиком создаёт валидный челлендж канонического типа с прогрессом по BE-036;
без ключа — fallback на rule-based (тот же тип-контракт); невалидный тип/target чинится валидатором или
уходит в fallback; денежные guardrail не изменены.

---

## Связь с существующими задачами

- Замещает разъехавшуюся часть **E14**: канон типов теперь 5 (без `streak`), а BE-030
  «basket/streak/replenishment/collection» переосмыслен здесь без `streak`.
- **BE-010/011/012 (rule-based)** остаются `done` и работают как **fallback** — не удаляем.
- **AI-008..012** реализованы в `app/ml/` (не `app/llm`/`app/eval`); AI-013 приводит их словарь к канону.
- Продуктовые инварианты (hero-один-на-неделю, cap 40%, потолок 150 баллов) — без изменений.
