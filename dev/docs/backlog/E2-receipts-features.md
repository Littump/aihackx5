# E2 — Receipts & User features

## BE-005 users
**Файлы:** `app/features/users/{router,dto,service,database}.py`, тесты.
**Описание:** `GET /users?limit=` — список для переключателя демо (id, pseudonym, segment, level из `domovoy_states`, 1 если нет). `service.get_user(conn, user_id)` с `AppError("user_not_found", 404)`. Генерация псевдонима: `users/pseudonyms.py` — прилагательное + существительное из двух списков по 40 слов, уникальность через retry.
**AC:** список отсортирован по id; несуществующий id → 404 в формате `Error`; псевдонимы уникальны на 1000 генераций (unit).

## BE-006 receipts
**Файлы:** `app/features/receipts/{router,dto,service,database}.py`, тесты.
**Описание:** `POST /receipts` принимает `ReceiptInput`, считает totals из позиций, определяет `counted`: false, если в том же магазине есть counted-чек в пределах `RECEIPT_DEDUP_WINDOW_MIN` или за день уже `RECEIPTS_PER_DAY_MAX` counted-чеков; `counted_reason` — `dedup_window` / `daily_limit` / null. Пока без оркестратора: возвращает `ReceiptProcessingResult` с нулевыми дельтами и `fraud.decision=approve` (заглушка до BE-013/BE-020). `GET /users/{id}/receipts?limit=`.
**AC:**
- totals = сумма по позициям (`regular_price × qty`, `paid_price × qty`), с точностью до копейки;
- второй чек через 10 минут в том же магазине → `counted=false, counted_reason=dedup_window`; через 31 минуту → counted;
- четвёртый чек за день → `daily_limit`;
- чек в другом магазине через 10 минут → counted;
- 422 на пустой `items`; 404 на чужой `store_id`/`user_id`.

## BE-007 user_features
**Файлы:** `app/features/user_features/{service,database}.py`, `calc.py`, тесты.
**Описание:** `service.recompute(conn, user_id) -> UserFeatures` (pydantic-модель в `models.py`, `category_affinity: dict[str, CategoryAffinity]` с вложенной моделью) по §3 `domain-rules.md` за окно `FEATURES_WINDOW_WEEKS`, только counted и не возвращённые чеки. `calc.py` — чистые функции от списка чеков с позициями. Upsert в `user_features`. `service.get(conn, user_id)` — читает, если нет — пересчитывает.
**AC:**
- unit на каждую формулу из §3 на фиксированном наборе из 6 чеков (ожидаемые числа посчитаны руками в тесте);
- пользователь без чеков → `frequency_per_week=0, recency_days=null→ 999`, `avg_basket=0`, пустая affinity;
- `favourite_store_id` при равенстве — магазин последнего чека;
- e2e: после `POST /receipts` строка `user_features` обновлена.
