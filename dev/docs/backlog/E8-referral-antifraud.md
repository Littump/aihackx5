# E8 — Referral, Antifraud, Achievements

## BE-018 antifraud scoring
**Файлы:** `app/features/antifraud/scoring.py`, `service.py`, `database.py`, тесты.
**Описание:** `scoring.score_receipt(ctx) -> FraudDecision` и `score_referral(ctx) -> FraudDecision` по §11: `ctx` — pydantic-модель `ReceiptFraudContext` / `ReferralFraudContext` в `models.py` с уже загруженными фактами (чеки за 60 мин/день/7 дней, pos-доля, fingerprint-совпадения, приглашённые и их покупки). Решение по порогам и правилу «2 strong». `service.check_receipt(conn, receipt)` и `check_referral(conn, referral)` собирают ctx через `database.py` (читают `receipts`, `users`, `referrals` — через сервисы владельцев), пишут `fraud_checks`.
**AC:**
- каждый сигнал по отдельности: тест на срабатывание и на несрабатывание у границы;
- score 0.85 с одним strong → hold; с двумя → block; 0.6 → hold; 0.3 → approve;
- `signals[*].detail` — человекочитаемая строка с числами;
- `fraud_checks` получает строку на каждую проверку.

## BE-019 referrals
**Файлы:** `app/features/referrals/{router,dto,service,database}.py`, тесты.
**Описание:** `POST /referrals/redeem` — создаёт пользователя-приглашённого (сегмент `dormant`/`regular_mid` для демо задаётся `referee_kind` по правилу: новый → `new`), проверяет лимиты (`referral_limit_reached` 409), связывает. `service.on_receipt(conn, referee_user_id, receipt)`: первая покупка ≥ 500 → `first_purchase` + награда приглашённому; вторая через ≥ 7 дней → `antifraud.check_referral` → `rewarded` / `on_review` / `blocked`, награда пригласившему через `record_reward` (`kind=referral`). `GET /users/{id}/referral` с `invitees` под метками «Сосед №N».
**AC:**
- таблица наград §10 на три `referee_kind`;
- покупка 450 ₽ не qualifying; вторая через 5 дней — не qualifying, через 7 — да;
- 6-е оплаченное приглашение за месяц → лимит, статус `qualified` без награды (реализовано на этапе BE-019: реферал уже прошёл first_purchase, откат в pending не имеет смысла; см. domain-rules.md §10);
- ответ не содержит id/псевдонима приглашённых.

## BE-020 антифрод в pipeline
**Файлы:** `app/features/receipts/service.py`, тесты.
**Описание:** шаг 2 оркестратора: `block` → `counted=false, counted_reason=fraud_block`, дальнейшие шаги идут, но без наград; `hold` → чек counted, награды челленджа пишутся в ledger с `kind=challenge` только после... нет: в MVP `hold` откладывает только реферальную награду; чек-награды при `hold` начисляются, но PM view показывает флаг. Зафиксировать это в `domain-rules.md` §11 при реализации.
**AC:** `fraud_burst` из BE-014 после 5 чеков (число уточнено при реализации BE-020 — 4 чеков не хватало для срабатывания `same_pos_share`) даёт `decision=hold` или `block` и `counted=false` у заблокированных; approve-путь не меняет поведение BE-013.

## BE-021 achievements
**Файлы:** `app/features/achievements/{router,dto,service,database}.py`, тесты.
**Описание:** правила §12, `on_receipt` и `on_challenge_completed` возвращают новые коды, XP через `record_reward`. `GET /users/{id}/achievements` с русскими названиями из константы `ACHIEVEMENT_TITLES` в `service.py`.
**AC:** каждая ачивка — один тест; повторное срабатывание не дублирует (UNIQUE).
