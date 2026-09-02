# E1 — Synthetic data (владелец: T)

Цель: правдоподобные пользователи с историей 8–12 недель, различающиеся по frequency, корзине, категориям, promo sensitivity, cadence, social propensity и фрод-паттернам. Пишем в таблицы по `data-model.md` через `database.py` features.

## AI-001 Генератор
**Файлы:** `app/synthetic/__init__.py`, `__main__.py`, `profiles.py`, `generator.py`, `catalog.py`, `tests/unit/synthetic/`.
**Описание:**
- `catalog.py`: 12 категорий из `game_rules.CATEGORIES`, по 6–10 товаров в каждой с регулярной ценой и долей промо; сети `pyaterochka` / `perekrestok`, 40 магазинов в 4 районах одного города.
- `profiles.py`: сегменты `regular_mid` (60 %, 3–7 чеков/мес), `light` (20 %, 1–2), `heavy` (10 %, 8+), `dormant` (10 %, чеки только в первые недели окна). Для каждого: λ покупок в неделю (гамма-пуассон), средний чек (лог-нормаль вокруг 555 ₽), веса категорий (Дирихле с «любимыми» 2–3 категориями), promo sensitivity 0.1–0.6, паттерн дней недели, любимый магазин + 1–2 запасных, `social_propensity`.
- `generator.py`: по неделям генерирует чеки с позициями, промо-скидками, `points_earned` = 1 % от paid (0.5 % без любимых категорий), `points_spent` иногда; `pos_id` случайный из 4 на магазин. Пишет через `users.database`, `receipts.database`. Детерминирован при `--seed`.
- CLI: `uv run python -m app.synthetic --users 300 --weeks 10 --seed 42 --fraud-share 0.03`.
**AC:**
- 300 пользователей генерируются < 30 с;
- распределение чеков/мес по сегментам соответствует профилям (unit-тест на средние ± 20 %);
- у каждого пользователя есть любимый магазин с ≥ 50 % чеков;
- `regular_total ≥ paid_total`, `discount_total = regular − paid`, суммы совпадают с позициями (тест);
- один и тот же `--seed` даёт одинаковые данные.

## AI-002 Фрод-паттерны
**Файлы:** `app/synthetic/fraud.py`, тесты.
**Описание:** доля `--fraud-share` пользователей получает один из паттернов, помеченный в `users.segment`? Нет — сегмент не трогаем; метка в отдельной таблице не нужна: генератор пишет `expected_fraud.json` в `dev/backend/.synthetic/` с `user_id → pattern` для eval precision/recall. Паттерны по `domain-rules.md` §11: `cashier` (6–10 чеков в день в одном магазине с одним `pos_id`, разнообразные корзины), `split` (3–5 чеков подряд с интервалом 2–5 мин), `referral_farm` (пользователь с 6–10 приглашёнными, у каждого ровно одна покупка 500–550 ₽ и общий `device_fingerprint`), `self_referral` (пара с одинаковым fingerprint, регистрация через 3 минуты после ссылки).
**AC:** каждый паттерн генерируется и обнаружим правилами из §11 (тест: скоринг из BE-018, когда появится, даёт `block` на `cashier` и `referral_farm`; до BE-018 — тест на факты: число чеков, интервалы, fingerprint).

## AI-003 make synth
**Файлы:** `Makefile` (цель уже есть, подключить команду), `dev/backend/scripts/seed.py`.
**Описание:** `make synth` очищает данные (кроме `schema_migrations`) и генерирует 300 пользователей / 10 недель / seed 42, затем вызывает `challenges.service.refresh_weekly` для всех (когда BE-011 готов; до этого — пропуск с сообщением).
**AC:** после `make synth` `GET /users` возвращает 300 записей; повторный запуск даёт те же данные.
