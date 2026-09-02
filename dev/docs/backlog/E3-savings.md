# E3 — Savings

## BE-008 savings
**Файлы:** `app/features/savings/{router,dto,service,database}.py`, тесты.
**Описание:** `service.summary(conn, user_id, period) -> SavingsSummary` по §2: сумма, предыдущий период, дельта, разбивка на discount / points_earned / points_spent, топ-3 категории. Только counted и не возвращённые. `GET /users/{id}/savings?period=week|month`.
**AC:**
- чек 1000 регулярных, 850 оплачено, 10 баллов начислено, 50 списано → savings 210;
- возвращённый чек не учитывается;
- month = календарный месяц по `purchased_at`, previous — прошлый месяц; week — последние 7 дней, previous — 7 до них;
- топ-категории отсортированы по вкладу, максимум 3;
- e2e: поля ответа по контракту, 404.
