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
| Прогресс челленджа за один зачтённый чек в периоде | +1 (frequency — за любой; category — если категория есть в позициях) | `CHALLENGE_PROGRESS_STEP = 1` |

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
| `frequency` | `frequency_per_week < FREQUENCY_HEADROOM_MAX = 6` (строго меньше — на самом пороге headroom уже нет) и `recency_days ≤ 21` |
| `category` | категория с `share ≥ 0.10` и `visits ≥ 3` за окно, не из исключённых |

Если кандидатов нет (новый пользователь без истории) — `frequency` с baseline 1, target 2, без денежной награды.

## 5. Target

| Тип | Target |
|---|---|
| `frequency` | `ceil(max(baseline × 1.2, baseline + 1))`, потолок `ceil(baseline + 2)` — `ceil` берётся от всего выражения, а не только от `× 1.2`, поэтому target всегда целое число, даже при дробном `baseline` |
| `category` | покупок категории за неделю: `ceil(max(weekly_visits × 1.2, weekly_visits + 1))`, потолок `ceil(weekly_visits + 2)`, где `weekly_visits = visits / window_weeks` |

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

Пример PRD: baseline 2, target 3, avg_basket 600 → margin 90 → max 36 → **30 баллов**. Второй пример: baseline 1.5, target 3, avg_basket 555 → revenue 832.5 → margin 124.875 → max 49.95 → **40 баллов** (округление вниз до кратного 10 без промежуточных округлений).

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
- Неделя: понедельник 00:00 — воскресенье 23:59. Сброс — ручка `POST /league/rollover`.
- Зоны: повышение — топ `LEAGUE_PROMOTE_TOP = 7`, вылет — низ `LEAGUE_DEMOTE_BOTTOM = 5` (в дивизионе 1 не вылетают, в 5 не повышаются).
- Rollover: XP за повышение (`XP_LEAGUE_PROMOTION`) и за топ-`LEAGUE_TOP3_RANK = 3` недели (`XP_LEAGUE_TOP3`) начисляются независимо, оба возможны одному участнику. Начисление ровно одно на лигу-неделю: закрытая лига повторно не обрабатывается.

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

Лимиты: `REFERRAL_PAID_PER_MONTH = 5`, `REFERRAL_PAID_PER_YEAR = 20`. `POST /referrals/redeem` возвращает `409 referral_limit_reached`, когда у пригласившего уже `REFERRAL_PAID_PER_YEAR` рефералов в статусе `rewarded` за текущий календарный год (годовой лимит, не месячный).

Известное ограничение MVP: реферал, упёршийся в месячный лимит `REFERRAL_PAID_PER_MONTH`, остаётся в `status='qualified'` без награды навсегда — retry на следующий месяц не реализован, это осознанное упрощение, а не баг.

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
| `0.5 – 0.8` | `hold`: чек `counted` остаётся как решил дедуп/лимит |
| `≥ 0.8` **и ≥ 2 strong** | `block`: чек `counted=false`, в PM view с причинами |
| `≥ 0.8`, но < 2 strong | `hold` — precision важнее recall |

Каждая проверка сохраняется с полным списком сигналов и человеческим `detail`.

### Эффект в пайплайне чека (BE-020)

`block` переводит `counted` в `false` (`counted_reason=fraud_block`), если чек ещё не стал `counted=false` по другой причине. Если дедуп/лимит уже сделали чек `counted=false` раньше — причина остаётся исходной (`dedup_window`/`daily_limit`), не перезаписывается на `fraud_block`. `hold` не влияет на чек-награды: XP и прогресс челленджа начисляются нормально, единственный эффект `hold` в MVP — запись в `fraud_checks` для PM view. Реферальные награды регулируются отдельным независимым фрод-чеком в `referrals.service` (`score_referral` на реферальные сигналы), не этим шагом.

## 12. Ачивки (MVP)

| code | Условие | Константа |
|---|---|---|
| `first_receipt` | первый counted-чек | — |
| `first_challenge` | первый выполненный челлендж | — |
| `streak_4` | streak_weeks ≥ 4 недель | `ACHIEVEMENT_STREAK_WEEKS = 4` |
| `saver_1000` | savings за месяц ≥ 1000 ₽ | `SAVER_1000_THRESHOLD_RUB = 1000` |
| `explorer` | counted-чеки в обеих сетях (pyaterochka и perekrestok) за 30 дней | `ACHIEVEMENT_EXPLORER_WINDOW_DAYS = 30` |
| `neighbour` | первый успешный реферал (`referral.status` стал `rewarded`) | — |
| `league_top3` | финальный ранг в закрывшейся лиге-неделе ≤ 3 (проверяется в `league.rollover`, не на каждом чеке) | `LEAGUE_TOP3_RANK = 3` |

Награда за каждую разблокированную ачивку — `XP_ACHIEVEMENT = 25`, без баллов. Повторное срабатывание не начисляет награду и не создаёт вторую строку: `UNIQUE (user_id, code)`.

`league_top3` намеренно не проверяется по живому рангу внутри `receipts.process_receipt`: соло-лига в начале недели тривиально даёт ранг 1, что обесценивало бы смысл «топ-3 недели». Ачивка разблокируется в `league.rollover.rollover_week` тем же условием (`rank ≤ LEAGUE_TOP3_RANK`), что уже определяет получателей `XP_LEAGUE_TOP3`.

`achievements_unlocked` в ответе `POST /receipts` содержит только коды, разблокированные для пользователя ЭТОГО чека. `neighbour` начисляется рефереру (другому пользователю) и в этот список не попадает, хотя запись в `achievements` и XP рефереру создаются немедленно.

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

## 15. Simulate demo receipt (assumptions)

`POST /users/{id}/receipts/simulate` генерирует правдоподобный чек из `user_features`, не показатель X5.

| Параметр | Значение | Константа |
|---|---|---|
| Число позиций | 3–6 | `SIMULATE_ITEMS_MIN/MAX` |
| Базовая корзина без истории | 500 ₽ | `SIMULATE_DEFAULT_AVG_BASKET` |
| Разброс суммы вокруг `avg_basket` | ×0.7 … ×1.3 | `SIMULATE_BASKET_VARIATION_MIN/MAX` |
| Разброс веса позиции при делении суммы чека | ×0.5 … ×1.5 | `SIMULATE_ITEM_WEIGHT_MIN/MAX` |
| Разброс скидки промо-позиции | 10–30 % | `SIMULATE_PROMO_DISCOUNT_MIN/MAX` |
| Дефолтные категории без affinity | `dairy, bakery, fruits_veg` | `SIMULATE_DEFAULT_CATEGORIES` |
| Позиций-бустов в `category_boost` | 2 | `SIMULATE_CATEGORY_BOOST_ITEMS` |
| Цена одной буст-позиции | 150 ₽ | `SIMULATE_BOOST_ITEM_PRICE` |
| Чеков в `fraud_burst` | 5 по 100 ₽ с интервалом 3 мин, один `pos_id` | `SIMULATE_FRAUD_BURST_COUNT/AMOUNT/INTERVAL_MIN/POS_ID` |
| Категория позиции в `fraud_burst` | `grocery` | `SIMULATE_FRAUD_BURST_CATEGORY` |

### Черновик чека (двухшаговая симуляция)

`GET /users/{id}/receipts/simulate/draft` отдаёт корзину на подтверждение: пользователь удаляет и добавляет позиции, затем шлёт их в `POST /users/{id}/receipts/simulate` полем `items`. Переданные `items` отменяют `scenario`.

| Параметр | Значение | Константа |
|---|---|---|
| Число позиций в черновике | 3–4 | `SIMULATE_DRAFT_ITEMS_MIN/MAX` |
| Категория цели недели в черновике | одна позиция гарантированно, если hero — категорийный | — |
| Скидка позиции, помеченной «по акции» вручную | 20 % от обычной цены | `SIMULATE_DRAFT_PROMO_DISCOUNT` |
| Цена по умолчанию для добавленной позиции | 150 ₽ | `SIMULATE_DRAFT_DEFAULT_PRICE` |
| Позиций в подтверждённом чеке | 1–20 | лимит контракта `SimulateReceiptInput.items` |

## 16. Recommended mechanic (Home)

`GET /users/{id}/home` выбирает одну механику в `recommended_mechanic`. Первое сработавшее правило побеждает, причина — одна фраза.

| # | Условие | Механика |
|---|---|---|
| 1 | `completed_challenges_count == 0` | `challenge` («Начни с первого челленджа») |
| 2 | `completed_challenges_count ≥ RECOMMENDED_MECHANIC_LEAGUE_MIN_COMPLETED (3)` и `has_league` | `league` |
| 3 | `social_propensity ≥ RECOMMENDED_MECHANIC_REFERRAL_MIN_SOCIAL_PROPENSITY (0.6)` и `completed_challenges_count ≥ RECOMMENDED_MECHANIC_REFERRAL_MIN_COMPLETED (2)` | `referral` |
| 4 | иначе | `challenge` («Выполни ещё один челлендж») |

`completed_challenges_count` — все челленджи пользователя со `status='completed'` за всё время, не только за неделю. `has_league` пока всегда `false` — лиги нет до BE-016, правило написано как чистая функция с этим параметром, чтобы ветку `league` можно было протестировать отдельно от интеграции. Решение сохраняется в `mechanic_decisions` при каждом вызове `GET /home`: `reasons` содержит фразу и контекст (`completed_challenges_count`, `has_league`, `social_propensity`) для будущей PM-объяснимости.
