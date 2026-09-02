# E4 — Domovoy

## BE-009 domovoy
**Файлы:** `app/features/domovoy/{service,database}.py`, `progression.py`, тесты.
**Описание:** `progression.py`: `level_for_xp` (из game_rules), `xp_to_next_level`, `mood_for_week(receipts_with_items) -> (mood, reason)` по §8, `next_streak(prev, completed_this_week, freeze_available) -> (streak, freeze_left)`. `service.on_receipt(conn, user_id, receipt) -> DomovoyDelta` (+XP_RECEIPT если counted, пересчёт mood, `last_fed_at`), `service.add_xp(conn, user_id, xp, kind, ref)` пишет в `reward_ledger` через `challenges.service`? Нет — ledger принадлежит `challenges`; `domovoy.service.add_xp` вызывает `challenges.service.record_reward`. `service.get_state(conn, user_id)`; создаёт строку при первом обращении.
**AC:**
- unit на пороги уровней и `xp_to_next_level` (L1 при 0 → 100 до L2; L2 при 150 → 150);
- unit на каждое правило mood, порядок приоритета (sleepy побеждает healthy);
- streak: пропуск с заморозкой сохраняет streak и снимает заморозку; без заморозки — 0;
- e2e: чек → xp +10, `last_fed_at` обновлён; чек `counted=false` → xp не меняется.
