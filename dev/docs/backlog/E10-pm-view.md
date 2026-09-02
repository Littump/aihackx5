# E10 — PM view

## BE-022 pm users + fraud
**Файлы:** `app/features/pm/{router,dto,service,database}.py`, тесты.
**Описание:** `GET /pm/users/{id}` собирает `PmUserResponse`: features, последняя запись `mechanic_decisions` с причинами, hero challenge с economics и rationale, суммы ledger, `expected_incremental_margin_month` = сумма по активным/выполненным челленджам месяца, последние 10 `fraud_checks`, последние 20 ledger. `GET /pm/fraud?limit&decision`.
**AC:** ответ по контракту; фильтр по decision работает; у пользователя без истории поля заполнены нулями, а не 500.

## BE-023 pm simulation/eval
**Описание:** `GET /pm/simulation/latest`, `GET /pm/eval/latest` читают последние строки; 404 если пусто. `pm.database.insert_simulation_run`, `insert_eval_run` — для AI-005/006.
**AC:** e2e с вставкой через фабрику.

## FE-006 PM view
**Описание:** экран `/pm`: выбор пользователя, блоки «Features», «Механика и почему», «Челлендж и экономика» (baseline, target, expected margin, max reward, выданный reward, deadweight note), «Антифрод» (таблица проверок с сигналами), «Ledger», «Симуляция» (карточки метрик + assumptions), «Eval» (hit rate, invalid, fallback, таблица профилей). Десктопная ширина допустима — это не consumer-экран.
**AC:** тесты рендера всех блоков; при 404 симуляции — «ещё не запускали».
