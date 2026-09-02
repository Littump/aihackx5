# E7 — League

## BE-016 league
**Файлы:** `app/features/league/{router,dto,service,database}.py`, `scoring.py`, тесты.
**Описание:** `scoring.week_score(...)` по §9. `service.ensure_member(conn, user_id)`: лига текущей недели по `favourite_store_id` и дивизиону пользователя (хранить дивизион в `league_members` последней недели; новичок — 1), open-лига до 30, иначе новая. `on_receipt` пересчитывает score участника, возвращает rank до/после. `GET /users/{id}/league`: участники под псевдонимами (`pseudonym, level, score, rank, is_me`), зоны, house-агрегат (средний savings_rate дома и место среди магазинов района).
**AC:**
- пример §9 → 124;
- 31-й участник попадает в новую лигу того же магазина;
- ответ не содержит ФИО/адресов/сумм других (тест проверяет набор ключей `members[*]`);
- зоны: ранги 1–7 promotion, 26–30 demotion при 30 участниках; при 12 участниках demotion — последние 5.

## BE-017 rollover
**Файлы:** `app/features/league/service.py` (`rollover_week`), router `POST /league/rollover` (добавить в контракт через скилл), тесты.
**Описание:** закрывает лиги прошедшей недели, повышает/понижает дивизионы, пишет XP (`XP_LEAGUE_PROMOTION`, `XP_LEAGUE_TOP3`) через `challenges.service.record_reward`, создаёт участие на новую неделю.
**AC:** топ-7 повышены, низ-5 понижены, дивизион 1 не понижается, 5 не повышается; XP начислен ровно один раз (идемпотентность при повторном вызове за ту же неделю).
