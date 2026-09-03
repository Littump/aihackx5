# PRD — «Домовой»

## 1. Цель продукта

**Домовой** — персональный игровой слой внутри X5, который автоматически использует историю покупок пользователя, чтобы:

- показывать реальную выгоду от X5 Клуба;
- давать релевантную причину выбрать X5 для следующей покупки;
- связывать отдельные покупки в постоянный progress loop;
- повышать frequency без постоянного увеличения промо-бюджета.

Пользователь ничего не загружает вручную: покупки с картой X5 автоматически попадают в историю.

### Основной сегмент

Пользователи X5 Клуба со средней частотой покупок — ориентировочно **3–7 покупок в месяц**.

Почему этот сегмент:

- уже есть история чеков для персонализации;
- привычка покупать в X5 уже сформирована;
- при этом остаётся headroom для дополнительной покупки;
- такой пользователь ближе всего к переходу через целевой порог `N покупок за период`.

### Core flow

**покупка → чек попадает в профиль → анализ привычек → обновление Домового и статистики → персональная цель → следующая покупка → обновление прогресса, рейтинга и награды**

---

## 2. Customer Jobs

### Job 1 — быстро получить релевантную выгоду

Когда мне снова нужно купить продукты, я хочу быстро понять, есть ли сейчас в X5 что-то полезное именно для меня, чтобы не тратить время на просмотр множества акций.

**Гипотеза решения:** показывать один главный персональный next action на основе истории покупок.

### Job 2 — понимать пользу программы лояльности

Когда я регулярно пользуюсь X5 Клубом, я хочу понимать, какую реальную пользу уже получил, чтобы видеть смысл продолжать пользоваться программой.

**Гипотеза решения:** показывать фактическую экономию и накопленный прогресс через Домового.

### Job 3 — иметь дополнительную причину выбрать X5

Когда мне снова нужны продукты, я хочу получить релевантную дополнительную причину выбрать X5, а не альтернативу.

**Гипотеза решения:** персональные цели немного выше привычного baseline пользователя + игровой progress.

---

## 3. Игровые механики

В MVP используем три механики.

### 3.1. Личный прогресс + цифровой аватар

Домовой отражает накопленный прогресс пользователя:

- level / XP;
- состояние / настроение;
- streak;
- фактическая экономия;
- выполненные челленджи;
- achievements.

Новая покупка автоматически влияет на состояние Домового.

### 3.2. Лига домов

Анонимный рейтинг пользователей по игровому score.

Показываем:

- 20–30 пользователей в одной лиге;
- псевдонимы / Домовых;
- score;
- место пользователя;
- зону повышения;
- изменение позиции после новой покупки.

Не показываем:

- ФИО;
- адрес пользователя;
- абсолютные суммы трат;
- состав чужих покупок.

Score должен учитывать прогресс и выполнение целей, а не просто абсолютный размер трат.

### 3.3. Referral — «Позови соседа»

Пользователь получает referral link / QR.

Награда начисляется не за регистрацию, а после qualifying behavior приглашённого.

Минимальная логика:

1. пользователь приходит по referral;
2. совершает первую qualifying purchase;
3. совершает вторую покупку;
4. referral проходит antifraud check;
5. начисляется reward.

---

## 4. Основной интерфейс

### Screen 1 — Home / Домовой

Показываем:

- Домового;
- level / XP;
- состояние;
- экономию за месяц;
- один персональный insight;
- **1 hero challenge**;
- progress;
- `Почему это мне?`;
- переход в Лигу;
- переход в Referral.

Пример:

**Домовой · уровень 7**

В сентябре вы сэкономили **1 240 ₽**

**Цель недели**

Обычно у вас 2 покупки в неделю.  
Сделайте 3 до воскресенья.

**2 / 3**

+50 XP + 30 баллов

---

### Screen 2 — Challenge

Показываем:

- название;
- условие;
- baseline;
- target;
- progress;
- deadline;
- reward;
- `Почему это мне?`;
- историю выполненных целей.

---

### Screen 3 — Лига домов

Показываем:

- текущий дивизион;
- список пользователей;
- score;
- место пользователя;
- зоны повышения / понижения;
- изменение позиции после новой покупки.

---

### Screen 4 — Referral

Показываем:

- QR / referral link;
- условия;
- reward;
- progress приглашённых;
- статус `ожидает / выполнен / на проверке`;
- лимиты.

Статистику пользователя можно встроить в Home / Profile, чтобы не создавать отдельный пятый consumer-screen.

---

## 5. Автоматическая обработка покупки

Новый чек приходит автоматически после покупки с картой X5.

Система:

1. добавляет чек в историю;
2. пересчитывает user features;
3. обновляет savings;
4. обновляет progress активного challenge;
5. начисляет XP;
6. обновляет состояние Домового;
7. обновляет league score / rank;
8. при выполнении цели рассчитывает reward;
9. запускает antifraud check при необходимости.

Для demo используем техническую кнопку **`Simulate new purchase`**.

---

## 6. Персональные челленджи

На Home — **1 hero challenge**.

На отдельном экране можно показывать ещё максимум 2 side challenges.

### MVP-типы

#### Frequency

Обычно 2 покупки в неделю → цель 3.

#### Category

Пользователь регулярно покупает молочные продукты → цель по этой категории.

Каждая цель содержит:

`type / baseline / target / progress / deadline / reward / rationale`

> **E14 (ML rework, принято).** Базовый MVP — `Frequency` и `Category`. Принятая переработка расширяет
> библиотеку типов до `basket / streak / replenishment / collection` и добавляет форму награды
> `reward_kind` (`promo` / `ladder` / `none`) и многошаговый план `steps[]` (cap 2, пользователю виден
> только `steps[0]`). Дизайн — `docs/ml-rework/ml-solution-architecture.md`, задачи — эпик E14.

---

## 7. Как формируется предложение

### Pipeline

**чеки → user features → candidate challenges / offers → personalization → economics engine → LLM → пользователь**

> **E14 (ML rework, принято).** Целевой pipeline: **чеки → user features → Insight Builder → LLM Challenge
> Planner (structured output) → детерминированный validator → Economics / Reward Ladder → пользователь**.
> `candidate` + `personalization` ниже сохраняются как **fallback** (без ключа LLM или при невалидном
> плане, `plan_source=rules`), а не удаляются. Деньги/XP по-прежнему считает код (decision #7/#15).

### 7.1. User Features — обычный код

Из чеков считаем:

- frequency;
- recency;
- average basket;
- promo sensitivity;
- category affinity;
- purchase cadence;
- realized savings;
- favourite store;
- challenge history.

### 7.2. Candidate Engine — обычный код

Определяет, что пользователю вообще допустимо предложить.

Например:

- есть headroom по frequency → `Frequency challenge`;
- сильная affinity к категории → `Category challenge`;
- есть подходящее активное промо → персональный offer.

### 7.3. Personalization

AI/recommender ранжирует допустимые варианты и выбирает:

- 1 hero option;
- до 2 side options.

> **E14 (ML rework, принято).** Целевой выбор челленджа делает LLM Challenge Planner (§7.5); rule-based
> ранжирование остаётся **fallback**-веткой и baseline для eval.

### 7.4. Economics / Reward Engine — обычный код

Проверяет, окупается ли механика.

Для каждого challenge engine:

- определяет target относительно baseline;
- оценивает expected incremental effect;
- определяет, допустим ли денежный reward;
- рассчитывает максимальный бюджет reward.

Пример:

`baseline = 2 покупки / неделю`

`target = 3`

`average basket = 600 ₽`

`expected incremental margin = 90 ₽`

Если правило:

`reward ≤ 40% expected incremental margin`

то максимальная стоимость reward:

`36 ₽`

Система может выдать, например, **30 баллов**.

Это не обязательный reward, а максимальный допустимый бюджет.

Если X5 уже имеет готовое промо, система не создаёт новую скидку, а выбирает релевантный offer из доступного пула.

В production expected incremental effect должен учитывать вероятность, что пользователь совершил бы действие и без challenge.

### 7.5. LLM

LLM отвечает за:

- текст от лица Домового;
- explanation;
- tone of voice;
- персональный insight.

Например:

> Домовой заметил, что вы покупаете молочные продукты примерно раз в 6 дней. Поэтому на этой неделе он выбрал цель именно по этой категории.

LLM **не назначает скидку, reward или финансовые параметры**.

> **E14 (ML rework, принято).** В целевой архитектуре LLM выходит из роли «только текст» и становится
> **планировщиком челленджа**: выбирает тип, target, ссылки на SKU (`sku_refs`), **форму** награды
> `reward_kind` (`promo` / `ladder` / `none`) и её **ординальную стадию** `reward_level`
> (`none` / `low` / `medium` / `high`), а также до `MAX_PLAN_STEPS=2` шагов плана. Граница «LLM не считает
> деньги» сохраняется: **конкретную сумму в рублях и число XP считает только код** — Economics Engine по
> марже (§7.4) и Reward Ladder по грейду пользователя. Ответ LLM детерминированно валидируется (SKU/target/
> тип), при провале — repair и fallback на rule-based. Полный дизайн — `docs/ml-rework/ml-solution-architecture.md`,
> граница уточнена в decision #7/#15.

---

## 8. Что считается экономией

Фактическая экономия рассчитывается только из данных чеков.

Упрощённо:

`Savings = regular price − paid price + cashback received + points spent`

Пользователь видит:

- savings за неделю / месяц;
- изменение к предыдущему периоду;
- основные категории экономии.

LLM не рассчитывает и не придумывает savings.

---

## 9. Правила начисления

| Действие | Игровая награда | Денежная награда |
|---|---:|---:|
| Валидная покупка | +10 XP | — |
| Выполнен weekly challenge | +50 XP | рассчитывает Economics Engine |
| Streak / achievement | XP / предмет | обычно — |
| Повышение в Лиге | XP / предмет | ограниченный reward при необходимости |
| Successful referral | +100 XP | фиксированный reward после antifraud |

Лимиты reward задаются конфигурацией и проверяются Economics Engine.

---

## 10. «Почему это мне?»

Для каждой персональной рекомендации пользователь может открыть explanation.

Пример:

> За последние 8 недель вы покупали молочные продукты 6 раз, обычно каждые 5–7 дней. Поэтому эта цель связана именно с этой категорией.

Explanation должен ссылаться на реальные рассчитанные user features.

---

## 11. Antifraud

Используем простой explainable precision-first scoring.

### Receipt fraud signals

- слишком много чеков за короткий период;
- несколько чеков в одном магазине с маленьким интервалом;
- резкий аномальный скачок frequency;
- возврат покупки, закрывшей challenge;
- нетипичное повторяющееся поведение чеков.

### Referral fraud signals

- один device / fingerprint у пригласившего и приглашённого;
- слишком много referrals за короткий период;
- одинаковые минимальные покупки у всех приглашённых;
- связанные аккаунты;
- подозрительная скорость регистрации и покупки.

### Fraud score

`0–1`

Пример правил:

- `<0.5` → approve;
- `0.5–0.8` → hold / delayed reward;
- `≥0.8 + минимум 2 сильных сигнала` → block / manual review.

**Precision важнее Recall:** блокируем только при сильных и объяснимых сигналах, чтобы не наказывать честных пользователей.

---

## 12. Business / PM View

PM X5 должен видеть:

- user features;
- выбранную механику;
- выбранный challenge / offer;
- rationale;
- baseline;
- target;
- reward;
- expected incremental effect;
- expected margin;
- fraud score + причины;
- result.

PM view нужен для demo и объяснимости решения.

---

## 13. Synthetic Data

### Для разработки

100–500 пользователей.

### Для финальной simulation

5–10 тыс. пользователей.

История на пользователя: **8–12 недель**.

### Минимальные данные

`user_id`

`receipt_id`

`timestamp`

`store`

`products`

`categories`

`regular_price`

`paid_price`

`discount`

`points_earned`

`points_spent`

Пользователи должны отличаться по:

- frequency;
- average basket;
- категориям;
- promo sensitivity;
- shopping cadence;
- social propensity;
- fraud patterns.

---

## 14. AI Evaluation

Персональные челленджи проверяем минимум на **30–50 synthetic profiles**.

### Основная метрика

`Challenge relevance hit rate ≥ 70%`

Challenge считается релевантным, если:

- связан с историей покупок пользователя;
- target реалистичен относительно baseline;
- условия можно проверить по чекам;
- explanation соответствует данным пользователя.

Дополнительно:

- invalid challenge rate;
- fallback rate;
- доля challenges, прошедших economics validator.

---

## 15. Simulation

На 1–10 тыс. synthetic users моделируем:

- control;
- treatment.

### Показываем

- purchases per user;
- долю пользователей с `≥ N покупками`;
- frequency uplift;
- incremental revenue;
- incremental margin;
- reward cost;
- net effect;
- referral conversion;
- fraud precision / recall.

Все параметры uplift, margin и reward явно маркируются как **simulation assumptions**, а не реальные показатели X5.

---

## 16. План пилота

### Гипотеза

Персональный игровой слой «Домовой» увеличивает долю пользователей с `≥ N покупками за период` относительно контроля без снижения incremental margin на участника.

### Группы

**Control:** текущий пользовательский опыт.

**Test A:** Домовой + персональные challenges + progress.

**Test B:** полный игровой слой — Домовой + challenges + Лига + Referral.

Это позволяет отдельно измерить эффект core-механики и social layer.

### Primary metric

- доля пользователей с `≥ N покупками за 4 недели`;

или

- purchases per user.

### Secondary metrics

- challenge activation rate;
- challenge completion rate;
- WAU;
- league engagement;
- referral conversion;
- savings visibility / interaction.

### Guardrails

- incremental margin − rewards ≥ 0;
- reward cost не превышает expected effect;
- fraud payouts;
- opt-outs / complaints;
- жалобы на рейтинг / privacy.

---

## 17. Demo Flow

1. Открываем Домового.
2. Показываем savings, XP и hero challenge.
3. Нажимаем `Почему это мне?`.
4. Показываем данные, на которых основана рекомендация.
5. Симулируем новую покупку.
6. Домовой автоматически «съедает» чек.
7. Обновляются savings, XP, state и challenge progress.
8. Пользователь выполняет challenge.
9. Меняется его позиция в Лиге.
10. Показываем Referral и расчёт reward.
11. Показываем antifraud example.
12. Открываем PM view.
13. Показываем simulation на 5–10 тыс. пользователей:
    - relevance hit rate;
    - frequency control vs treatment;
    - reward cost;
    - incremental margin;
    - antifraud precision.

---

## 18. MVP / порядок разработки

Все блоки ниже входят в финальный scope хакатона, но реализуются последовательно.

### Phase 1 — Core

- synthetic receipts;
- user features;
- Home / Домовой;
- savings;
- personalized challenge;
- `Почему это мне?`;
- receipt event → обновление progress;
- Economics Engine;
- LLM copy.

### Phase 2 — Social + Risk

- Лига домов;
- Referral;
- reward calculation;
- antifraud;
- achievements.

### Phase 3 — Evaluation

- PM view;
- 30–50 profile relevance eval;
- simulation 1–10k users;
- pilot metrics.

---

## 19. Definition of Done

- [ ] выбран и зафиксирован сегмент;
- [ ] есть synthetic history 8–12 недель;
- [ ] рассчитываются user features;
- [ ] разные профили получают разные challenges;
- [ ] challenge relevance ≥70% на 30–50 профилях;
- [ ] работает Home / Домовой;
- [ ] считается фактическая savings;
- [ ] новый receipt event обновляет progress / XP / state;
- [ ] работает Economics Engine;
- [ ] reward не превышает expected incremental effect;
- [ ] работает `Почему это мне?`;
- [ ] реализована Лига;
- [ ] место пользователя меняется после действий;
- [ ] реализован Referral;
- [ ] считается referral reward;
- [ ] реализован receipt/referral antifraud;
- [ ] fraud threshold объясним;
- [ ] precision используется как приоритетная antifraud metric;
- [ ] есть PM view;
- [ ] есть simulation 1–10k users;
- [ ] есть pilot plan с primary и guardrail metrics.
