# Доменные правила: числа и формулы

Единственное место, где живут числа, кроме `dev/backend/app/game_rules.py`. Оба файла обязаны совпадать; расхождение — дефект. Все значения — допущения хакатона, в коде и UI они помечаются как `simulation assumptions`, а не показатели X5.

## 0. Время

Таймзона всех правил — `TIMEZONE = "Europe/Moscow"`. Неделя челленджа и лиги — с понедельника 00:00 по воскресенье 23:59:59 по ней. Все расчёты берут «сейчас» из `app.core.clock`; на демо время фиксируется `DEMO_NOW`.

## 1. Учёт покупок

| Правило | Значение | Константа |
|---|---|---|
| Окно дедупликации: чеки в одном магазине ближе этого интервала — один чек, второй `counted=false` | 30 минут | `RECEIPT_DEDUP_WINDOW_MIN = 30` |
| Максимум учтённых чеков в день | 3 | `RECEIPTS_PER_DAY_MAX = 3` |
| Окно features | 8–12 недель, по умолчанию 10 | `FEATURES_WINDOW_WEEKS = 10` |
| Возврат чека | откатывает прогресс челленджа и награду, если чек его закрыл | — |

Категории (12 макро): `dairy, bakery, fruits_veg, meat_fish, grocery, snacks, drinks, alcohol, household, beauty, ready_food, other`. Алкоголь и табак в челленджи не попадают: `CHALLENGE_EXCLUDED_CATEGORIES = {"alcohol"}`.

## 2. Savings (фактическая экономия)

По чеку: `savings = (regular_total − paid_total) + points_earned + points_spent`. Баллы считаем 1 балл = 1 ₽. Возвращённые чеки исключаются.

Период: неделя (последние 7 дней) и месяц (календарный текущий). Дельта — к предыдущему периоду той же длины. Топ-3 категории по вкладу `(regular_price − paid_price) × qty`.

LLM не участвует. Это чистый агрегат по данным чеков, без участия LLM.

## 3. User features

| Feature | Формула |
|---|---|
| `frequency_per_week` | counted-чеки за окно / недель в окне |
| `recency_days` | дней с последнего counted-чека |
| `avg_basket` | среднее `paid_total` |
| `promo_sensitivity` | сумма promo-позиций / сумма всех позиций (по regular_price × qty) |
| `cadence_days` | среднее между соседними чеками |
| `category_affinity[c].share` | доля категории в сумме корзин |
| `category_affinity[c].visits` | число чеков с категорией |
| `category_affinity[c].cadence_days` | средний интервал между чеками с категорией |
| `favourite_store_id` | магазин с максимумом чеков, при равенстве — последний |
| `cross_chain_share` | доля чеков в сети, отличной от сети любимого магазина |
| `realized_savings_30d` | savings за последние `REALIZED_SAVINGS_WINDOW_DAYS = 30` дней (не окно features): `(regular_total − paid_total) + points_earned + points_spent`, 0 если чеков нет |
| `weekday_pattern` | доля counted-чеков по дню недели покупки (0 — понедельник) за окно, `[0]×7` если чеков нет |

Нет истории (0 чеков в окне): `frequency_per_week=0`, `recency_days = USER_FEATURES_RECENCY_NO_HISTORY_DAYS = 999` (сентинел, не null), `avg_basket=0`, `promo_sensitivity=0`, `cadence_days=null`, `category_affinity={}`, `favourite_store_id=null`, `cross_chain_share=0`.

Baseline для frequency-челленджа = `round(frequency_per_week, 1)`, минимум 1.

## 4. Candidate engine (что допустимо предложить)

| Кандидат | Условие |
|---|---|
| `frequency` | `frequency_per_week ≤ FREQUENCY_HEADROOM_MAX = 6` и `recency_days ≤ 21` |
| `category` | категория с `share ≥ 0.10` и `visits ≥ 3` за окно, не из исключённых |

Если кандидатов нет (новый пользователь без истории) — `frequency` с baseline 1, target 2, без денежной награды.

## 5. Target

| Тип | Target |
|---|---|
| `frequency` | `max(ceil(baseline × 1.2), baseline + 1)`, потолок `baseline + 2` |
| `category` | покупок категории за неделю: `max(ceil(weekly_visits × 1.2), weekly_visits + 1)`, где `weekly_visits = visits / window_weeks` |

Пример PRD: baseline 2 → target 3.

## 6. Economics engine

```
expected_incremental_purchases = target − baseline
expected_incremental_revenue   = expected_incremental_purchases × avg_basket
expected_incremental_margin    = expected_incremental_revenue × CONTRIBUTION_MARGIN      # 0.15
max_reward_rub                 = expected_incremental_margin × REWARD_SHARE_MAX           # 0.40
reward_points                  = floor(max_reward_rub / 10) × 10
если reward_points < REWARD_POINTS_MIN (30) → денежной награды нет (0), остаётся XP
reward_points = min(reward_points, REWARD_POINTS_MAX_WEEKLY = 150)
```

Пример PRD: baseline 2, target 3, avg_basket 600 → margin 90 → max 36 → **30 баллов**. Пример из продуктового документа: baseline 1.5, target 3, чек 555 → 832 × 0.15 = 125 → 50 → **50 баллов**.

Deadweight в MVP не моделируем, но поле `economics.deadweight_note` пишет фразу для PM view. В production ожидаемый эффект умножается на `1 − P(выполнил бы без челленджа)`.

Стоимость балла для отчётов симуляции: `POINT_COST_RUB = 0.75` (сгорание 25 %), доля спонсорских наград `SPONSOR_SHARE = 0.5` — только в симуляции.

## 7. Personalization (hero + side)

Ранжирование кандидатов по `priority`:
- `frequency`: `priority = 1.0 + 0.5 × (1 − frequency_per_week / 6)` — чем больше headroom, тем выше;
- `category`: `priority = 0.8 + share` — сильная affinity поднимает.

Hero — максимум priority. Side — следующие до двух, не того же типа и категории. Один активный набор на неделю; `refresh` в середине недели закрывает старые как `expired`, если они не выполнены.

## 8. XP, уровни, настроение, streak

| Действие | XP |
|---|---|
| Валидный (counted) чек | +10 `XP_RECEIPT` |
| Выполнен weekly challenge | +50 `XP_CHALLENGE` |
| Streak каждые 4 недели | +100 `XP_STREAK_4W` + предмет |
| Повышение в лиге | +30 `XP_LEAGUE_PROMOTION` |
| Топ-3 недели лиги | +80 `XP_LEAGUE_TOP3` |
| Успешный реферал | +100 `XP_REFERRAL` |
| Ачивка | +25 `XP_ACHIEVEMENT` |

Уровень: `level = max n : xp ≥ 50 × (n − 1) × n`. Пороги: L1 0, L2 100, L3 300, L4 600, L5 1000, L6 1500, L7 2100, L8 2800, L9 3600, L10 4500.

`xp_to_next_level = порог(level + 1) − xp`; на L10 (максимум) — 0.

Настроение по последним 7 дням counted-чеков, первое сработавшее правило:

| Mood | Условие |
|---|---|
| `sleepy` | нет чеков 7+ дней |
| `healthy` | доля `fruits_veg + dairy` в сумме ≥ 0.30 |
| `cozy` | есть `bakery` и `drinks` (чай/кофе) хотя бы в двух чеках |
| `cheerful` | ≥ 5 разных категорий за неделю |
| `bored` | иначе |

Streak: число подряд идущих недель с выполненным hero-челленджем. Пропуск при доступной заморозке — streak сохраняется, заморозка сгорает; восстанавливается 1-го числа месяца.

## 9. Лига

- «Дом» = `favourite_store_id`. Лига = `(store_id, division, week_start)` до `LEAGUE_SIZE = 30` участников; `open` лига добирает, при 30 закрывается и открывается новая.
- Дивизионы 1..5: бронза, серебро, золото, платина, алмаз. Новичок — дивизион 1.
- Неделя: понедельник 00:00 — воскресенье 23:59. Сброс — ручка `POST /league/rollover` (в backlog).
- Зоны: повышение — топ `LEAGUE_PROMOTE_TOP = 7`, вылет — низ `LEAGUE_DEMOTE_BOTTOM = 5` (в дивизионе 1 не вылетают, в 5 не повышаются).

Score за неделю:
```
savings_rate = week_savings / week_regular_total            # 0..1, cap 0.5
score = 200 × savings_rate
      + 50 × completed_challenges_this_week
      + 10 × min(streak_weeks, 5)
      + 5  × min(counted_receipts_this_week, 7)
```
Пример: savings_rate 0.12, 1 челлендж, streak 3, 4 чека → 24 + 50 + 30 + 20 = **124**.

Абсолютные суммы трат в score не входят и наружу не отдаются. В ответе лиги другие участники — только `pseudonym`, `score`, `rank`, `level`.

## 10. Рефералы

| `referee_kind` | Кто это | Приглашённому | Пригласившему |
|---|---|---|---|
| `new` | нет чеков вообще | 200 баллов после 1-й покупки ≥ 500 ₽ | 150 баллов + 100 XP после 2-й покупки |
| `dormant` | 0 counted-чеков за 60 дней | 150 баллов после 1-й покупки ≥ 500 ₽ | 150 баллов + 100 XP после 2-й покупки |
| `active` | остальные | только предмет | только предмет и командный XP |

Qualifying: 1-я покупка `≥ REFERRAL_MIN_FIRST_PURCHASE = 500 ₽`; 2-я покупка не раньше `REFERRAL_SECOND_PURCHASE_MIN_DAYS = 7` дней после первой. Награда пригласившему — после 2-й покупки и `antifraud.decision == approve`; `hold` → статус `on_review`, повторная проверка через 14 дней или при следующей покупке; `block` → `blocked`.

Лимиты: `REFERRAL_PAID_PER_MONTH = 5`, `REFERRAL_PAID_PER_YEAR = 20`.

## 11. Антифрод

Скор = `min(1, Σ weight сработавших сигналов)`. Сигнал «сильный» — помечен `strong`.

### Чек
| Код | Условие | Вес | strong |
|---|---|---|---|
| `burst_same_store` | ≥ 4 чеков в одном магазине за 60 минут | 0.25 | да |
| `daily_volume` | ≥ 6 чеков за день | 0.35 | да |
| `same_pos_share` | один `pos_id` > 70 % чеков за 7 дней при ≥ 5 чеках | 0.30 | да |
| `frequency_spike` | чеков за 7 дней ≥ 4 × `frequency_per_week` при baseline ≥ 1 | 0.20 | нет |
| `return_after_reward` | возврат чека, закрывшего челлендж, в течение 3 дней | 0.25 | да |
| `basket_monotony` | ≥ 3 чека подряд с одинаковым набором категорий и суммой ± 5 % | 0.15 | нет |

### Реферал
| Код | Условие | Вес | strong |
|---|---|---|---|
| `shared_device` | одинаковый `device_fingerprint` | 0.40 | да |
| `instant_signup` | приглашённый создан < 10 минут после генерации ссылки | 0.15 | нет |
| `min_purchase_pattern` | все приглашённые сделали ровно 1 покупку в диапазоне 500–550 ₽ и больше ничего (при ≥ 3 приглашённых) | 0.30 | да |
| `invite_burst` | > 5 приглашений за час | 0.20 | нет |
| `referral_ring` | приглашённый пригласил пригласившего или его приглашённых | 0.30 | да |
| `same_store_zero_activity` | приглашённый после qualifying-покупок не имеет чеков 14 дней | 0.15 | нет |

### Решение
| Скор | Решение |
|---|---|
| `< 0.5` | `approve` |
| `0.5 – 0.8` | `hold`: награда откладывается, чек `counted` остаётся |
| `≥ 0.8` **и ≥ 2 strong** | `block`: выплаты нет, чек `counted=false`, в PM view с причинами |
| `≥ 0.8`, но < 2 strong | `hold` — precision важнее recall |

Каждая проверка сохраняется с полным списком сигналов и человеческим `detail`.

## 12. Ачивки (MVP)

| code | Условие |
|---|---|
| `first_receipt` | первый counted-чек |
| `first_challenge` | первый выполненный челлендж |
| `streak_4` | streak 4 недели |
| `saver_1000` | savings за месяц ≥ 1000 ₽ |
| `explorer` | чеки в обеих сетях за 30 дней |
| `neighbour` | первый успешный реферал |
| `league_top3` | топ-3 недели |

## 13. Симуляция (assumptions)

| Параметр | Значение по умолчанию |
|---|---|
| Пользователей | 5 000 (1 000 – 10 000) |
| Недель | 8 |
| Доля участия (treatment) | 0.30 |
| Uplift частоты у участников | +7 % (0 – 15 %) |
| Затухание uplift | −10 % относительное в месяц |
| Contribution margin | 0.15 |
| Стоимость балла | 0.75 ₽ |
| Доля спонсорских наград | 0.5 |
| Доля фрод-аккаунтов | 0.03 |
| Порог N для метрики «≥ N покупок за 4 недели» | 8 |

Выход: purchases per user, доля `≥ N`, uplift, incremental revenue, incremental margin, reward cost, net, referral conversion, fraud precision/recall при выбранных порогах.

## 14. Eval релевантности

Челлендж релевантен, если все четыре условия верны: (1) категория входит в топ-5 affinity или тип `frequency`; (2) `target` в пределах `baseline × 1.2 … baseline × 2` и `≤ baseline + 2`; (3) условия проверяемы по чекам (тип из библиотеки, поля заполнены); (4) `explanation` содержит хотя бы одно число из `rationale_features`. Hit rate = доля релевантных из 30–50 профилей, цель `≥ 0.70`. Дополнительно: invalid rate (не прошёл валидатор), fallback rate (copy_source = template), economics pass rate.
