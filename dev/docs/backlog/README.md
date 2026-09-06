# Backlog — доска

Статусы: `todo`, `in_progress`, `review`, `done`, `blocked`. Владельцы: R — Роман, T — Татьяна, A — Анна. Порядок в таблице — порядок выполнения. Задача берётся, только если все `deps` в `done`.

Описания и acceptance criteria — в файлах эпиков. Обновлять эту таблицу при каждой смене статуса.

| ID | Эпик | Задача | Владелец | Deps | Статус | Дата |
|---|---|---|---|---|---|---|
| INF-001 | E0 | Скелет backend: FastAPI, config, db pool, errors, health, миграции, pytest с Postgres | R | — | done | 2026-09-02 |
| INF-002 | E0 | Скелет frontend: Vite+React+TS, Tailwind, Query, router, оболочка телефона, Vitest, MSW | R | — | done | 2026-09-02 |
| INF-003 | E0 | pre-commit: ruff, mypy, eslint, prettier, check_comments; Makefile; docker-compose | R | — | done | 2026-09-02 |
| INF-004 | E0 | Контракт openapi.yaml для всех ручек MVP + генерация типов + contract-check | R | — | done | 2026-09-02 |
| BE-001 | E0 | Миграция 001: stores, users, receipts, receipt_items, user_features, domovoy_states, challenges, reward_ledger | R | INF-001 | done | 2026-09-03 |
| BE-002 | E0 | Миграция 002: leagues, league_members, referrals, fraud_checks, achievements, mechanic_decisions, simulation_runs, eval_runs | R | BE-001 | done | 2026-09-03 |
| BE-003 | E0 | Дополнить `game_rules.py` всеми константами из domain-rules.md + тест на соответствие документу | R | INF-001 | done | 2026-09-03 |
| BE-004 | E0 | `tests/factories.py`: make_store, make_user, make_receipt, make_challenge | R | BE-002 | done | 2026-09-03 |
| AI-001 | E1 | Генератор синтетики: профили, магазины, чеки 8–12 недель, категории, промо, баллы | T | BE-004 | todo | |
| AI-002 | E1 | Фрод-паттерны в синтетике: кассир, дробление, ферма рефералов, самореферал (3 %) | T | AI-001, BE-002 | todo | |
| AI-003 | E1 | `make synth` и seed 300 пользователей для dev | T | AI-001 | todo | |
| BE-005 | E2 | `users`: список демо-пользователей, `GET /users`, псевдонимы | R | BE-004 | done | 2026-09-03 |
| BE-006 | E2 | `receipts`: приём чека, дедуп 30 мин, дневной лимит, `POST /receipts`, `GET /users/{id}/receipts` | R | BE-005 | done | 2026-09-03 |
| BE-007 | E2 | `user_features`: расчёт всех features по §3 domain-rules, пересчёт после чека | R | BE-006 | done | 2026-09-03 |
| BE-008 | E3 | `savings`: расчёт по §2, `GET /users/{id}/savings` | R | BE-006 | done | 2026-09-03 |
| BE-009 | E4 | `domovoy`: XP, уровень, настроение, streak, `progression.py`, on_receipt | R | BE-007 | done | 2026-09-03 |
| BE-010 | E5 | `challenges/candidate.py` + `economics.py`: кандидаты, target, max reward по §4–6 | R | BE-007, BE-003 | done | 2026-09-03 |
| BE-011 | E5 | `challenges`: personalization (hero/side), генерация набора, `refresh`, `GET` ручки, заглушка copy | R | BE-010 | done | 2026-09-03 |
| AI-004 | E5 | `app/llm/`: клиент Anthropic, `render_challenge`, `render_insight`, шаблоны fallback | T | BE-011 | todo | |
| BE-012 | E5 | Прогресс челленджа от чека, выполнение → reward_ledger + XP + streak, возврат откатывает | R | BE-011, BE-009 | done | 2026-09-03 |
| BE-013 | E6 | `receipts.process_receipt`: оркестратор по порядку из architecture.md, `ReceiptProcessingResult` | R | BE-012, BE-008 | done | 2026-09-03 |
| BE-014 | E6 | `POST /users/{id}/receipts/simulate`: генерация правдоподобного чека по features, сценарии | R | BE-013 | done | 2026-09-03 |
| BE-015 | E6 | `GET /users/{id}/home`: агрегат + recommended_mechanic (правила) + insight | R | BE-013 | done | 2026-09-03 |
| FE-001 | E6 | Оболочка: роутер, нижняя навигация, переключатель пользователя, MSW-хендлеры под контракт | R | INF-002, INF-004 | done | 2026-09-03 |
| FE-002 | E6 | Home: Домовой, XP, настроение, savings, insight, hero challenge, «Почему это мне?», кнопка Simulate | R | FE-001 | done | 2026-09-03 |
| FE-003 | E6 | Challenge: hero + side, прогресс, дедлайн, награда, explanation, история | R | FE-001 | done | 2026-09-03 |
| BE-016 | E7 | `league`: формирование лиг по дому и дивизиону, `scoring.py`, on_receipt, `GET /users/{id}/league` | R | BE-013 | done | 2026-09-03 |
| BE-017 | E7 | `POST /league/rollover`: недельный сброс, зоны, повышение/понижение, XP | R | BE-016 | done | 2026-09-03 |
| BE-018 | E8 | `antifraud/scoring.py`: сигналы чека и реферала по §11, решение, `fraud_checks` | R | BE-013 | done | 2026-09-03 |
| BE-019 | E8 | `referrals`: код, `redeem`, referee_kind, qualifying purchases, награда после антифрода, лимиты, `GET /users/{id}/referral` | R | BE-018 | done | 2026-09-03 |
| BE-020 | E8 | Антифрод в pipeline чека: block → counted=false, hold → отложенная награда | R | BE-018 | done | 2026-09-03 |
| BE-021 | E8 | `achievements`: правила §12, on_receipt, `GET` | R | BE-013 | done | 2026-09-03 |
| FE-004 | E9 | League: дивизион, список под псевдонимами, моё место, зоны, дельта после покупки, «дом vs район» | R | FE-001, BE-016 | done | 2026-09-03 |
| FE-005 | E9 | Referral: код/QR, правила, приглашённые со статусами, лимиты | R | FE-001, BE-019 | done | 2026-09-03 |
| BE-022 | E10 | `pm`: `GET /pm/users/{id}`, `GET /pm/fraud`, `mechanic_decisions` | R | BE-019, BE-021 | done | 2026-09-03 |
| BE-023 | E10 | `GET /pm/simulation/latest`, `GET /pm/eval/latest` | R | BE-002 | done | 2026-09-03 |
| FE-006 | E10 | PM view: features, механика + причины, челлендж + экономика, фрод, ledger, симуляция, eval | R | FE-001, BE-022, BE-023 | done | 2026-09-03 |
| AI-005 | E11 | `app/eval`: relevance по §14 на 30–50 профилях, запись в eval_runs | T | BE-011, AI-003 | todo | |
| AI-006 | E11 | `app/simulation`: control vs treatment по §13, запись в simulation_runs | T | AI-003, BE-013 | todo | |
| AI-007 | E11 | Промпт-тюнинг и проверка, что LLM-тексты содержат числа из features (fallback rate < 20 %) | T | AI-004, AI-005 | todo | |
| BE-024 | E14 | Миграция 003: `sku_catalog`, `receipt_items.sku_id`, `challenges` (+sku_refs/reward_level/reward_kind/plan_step/activates_on/plan_source), `llm_plans`, типы basket/streak/replenishment/collection | R | BE-002 | todo | |
| BE-025 | E14 | Константы планировщика в `game_rules.py` (PROMO_LEVEL_SHARE, CHURN_RISK, CHALLENGE_LIBRARY, ladder) + зеркало domain-rules | R | BE-024, BE-003 | todo | |
| BE-026 | E14 | Feature `catalog`: чтение `sku_catalog`, подсказки SKU, `GET /catalog` | R | BE-024 | todo | |
| BE-027 | E14 | Insight Builder: `PlannerInput` (агрегаты + category timeseries + churn_risk) детерминированно | R | BE-007, BE-025 | todo | |
| BE-028 | E14 | `economics.py`: `reward_level` → доля бюджета (формула §6 без изменений) | R | BE-025 | todo | |
| AI-008 | E14 | `app/llm/planner.py`: tool `emit_challenge_plan`, tool-use forcing, `ChallengePlan` (steps[] + reward_kind), fallback без ключа | T | BE-027, BE-025 | todo | |
| BE-029 | E14 | `plan_validator.py`: проверка SKU/target/типа/rationale, repair, fallback на rule-based | R | BE-027, AI-008 | todo | |
| BE-030 | E14 | Библиотека челленджей: предикаты basket / streak / replenishment / collection + target-правила | R | BE-012, BE-025 | todo | |
| BE-031 | E14 | `refresh_weekly` через planner→validator→economics→ladder, запись `llm_plans`/`plan_source` | R | BE-029, BE-030, BE-028, BE-032 | todo | |
| BE-032 | E14 | Reward Ladder: награда за опыт по XP/level+tenure, new-user буст, decay + XP за ladder-челленджи (вне LLM/Economics) | R | BE-009, BE-025 | todo | |
| AI-009 | E14 | Каталог SKU в синтетике + LLM-персоны поверх числовых профилей | T | AI-001, BE-024 | todo | |
| AI-010 | E14 | Eval: продолжение истории (counterfactual, без LLM-судьи) — incremental revenue/margin, net_effect | T | AI-005, AI-008 | todo | |
| AI-011 | E14 | Simulation: 3 ветки (control_x5 / treatment_llm / treatment_rules) из точки T, per-user cap (без knapsack) | T | AI-006, BE-031 | todo | |
| AI-012 | E14 | Промпт-тюнинг планировщика: fallback rate < 20 %, число из инсайта в rationale, отчёт | T | AI-008, AI-010 | todo | |
| BE-033 | E14 | Контракт: `ChallengeDetail` (+sku_refs/reward_level/plan_source), PM `ChallengePlanAudit` | R | INF-004, BE-031 | todo | |
| FE-007 | E14 | PM view: показать план LLM (insight_used, reward_level, sku_refs, plan_source, fallback) | R | FE-006, BE-033 | todo | |
| DOC-001 | E12 | Демо-сценарий по §17 PRD с конкретными user_id и ожидаемыми цифрами | A | FE-006 | todo | |
| INF-005 | E12 | `make demo`: поднять всё, засеять, прогнать eval и simulation одной командой | R | AI-005, AI-006 | todo | |
| INF-006 | E13 | Dockerfile backend/frontend, nginx.conf, docker-compose.prod.yml, .env.prod.example | R | INF-001, INF-002 | done | 2026-09-03 |
| INF-009 | E13 | Миграции как одноразовый сервис перед backend, rollback.sh, правило откатов | R | INF-006 | done | 2026-09-03 |
| INF-007 | E13 | setup-vm.sh: docker, ufw, пользователь деплоя, pg_dump по cron | R | INF-006 | done | 2026-09-03 |
| INF-008 | E13 | CD workflow: сборка образов в ghcr, деплой на VM по SSH после зелёного CI | R | INF-007, INF-009 | done | 2026-09-03 |
| INF-011 | E13 | Демо-данные на VM: синтетика, DEMO_NOW, eval и simulation | R | INF-008, AI-003 | blocked: нужна VM | |
| INF-010 | E13 | Домен и TLS, если будет домен | R | INF-008 | blocked: нужен домен | |
| DOC-002 | E12 | Одностраничник пилота и README для жюри | A | DOC-001 | todo | |
| FE-D01 | E15 | Токены дизайн-системы в `@theme static` + `shared/ui`: Card, Button, ProgressBar, Badge, StatusChip, ListRow, Skeleton, Tile | R | FE-001 | done | 2026-09-04 |
| FE-D02 | E15 | Персонаж: `DomovoyAvatar` на SVG, 5 настроений, слои обжитости, размеры 32/48/80 | R | FE-D01 | done | 2026-09-04 |
| FE-D03 | E15 | Оболочка: PhoneShell со скроллером, новая нижняя навигация, демо-полоса вместо селекта, широкий режим для PM | R | FE-D01 | done | 2026-09-04 |
| FE-D04 | E15 | Home по макету: компактный персонаж, свёрнутая экономия, цель недели в первом экране | R | FE-D02, FE-D03 | done | 2026-09-04 |
| FE-D05 | E15 | Challenge по макету: плитки baseline/target, объяснение в карточке, история со статусами | R | FE-D03 | done | 2026-09-04 |
| FE-D06 | E15 | League по макету: шапка со статами, зоны разделителями, строка «Вы», дом vs район | R | FE-D03 | done | 2026-09-04 |
| FE-D07 | E15 | Referral по макету: QR и код, награды, лимит, приглашённые, легенда статусов | R | FE-D03 | done | 2026-09-04 |
| FE-D08 | E15 | Состояния: скелетоны, ошибка, пусто, подсветка изменений после симуляции покупки | R | FE-D04, FE-D05, FE-D06, FE-D07, FE-D09 | done | 2026-09-04 |
| FE-D09 | E15 | PM view по макету: широкая раскладка, плашка допущений, шкала антифрода с засечками | R | FE-D01, FE-D03 | done | 2026-09-04 |
| BE-D01 | E12 | Черновик чека: `GET /users/{id}/receipts/simulate/draft` и подтверждённые `items` в `POST .../simulate` | R | BE-014 | done | 2026-09-04 |
| FE-D10 | E12 | Экран чека перед симуляцией: список позиций, удалить, добавить категорию и цену, подсказка цели, подтверждение | R | BE-D01, FE-D04 | done | 2026-09-04 |
| BE-T01 | E16 | Ручка `GET /users/{id}/rewards`: баланс баллов, опыт, справочник начислений, история; `points_balance` в `/home` | R | BE-012 | done | 2026-09-04 |
| BE-T02 | E16 | Объяснимая экономия: `receipts_count`, `items_count` и `top_products` в savings | R | BE-009 | done | 2026-09-04 |
| FE-T01 | E16 | Экран «Баллы и опыт» на `/rewards` и вход с карточки Домового | R | BE-T01, FE-D04 | done | 2026-09-04 |
| FE-T02 | E16 | Подсказки «?» (`InfoHint`) и расшифровка экономии по категориям | R | BE-T02, FE-D04 | done | 2026-09-04 |
| DOC-003 | E17 | Канонизировать типы челленджей в доках (5 типов, убрать streak/neighbors) | A | — | todo | |
| BE-034 | E17 | `game_rules`: `CHALLENGE_LIBRARY` (5 типов, без streak) + пороги/target для basket/replenishment/collection, зеркало domain-rules | R | BE-003, DOC-003 | todo | |
| BE-035 | E17 | Миграция 005: расширить `challenges.type` CHECK до 5 канонических типов + `sku_refs` | R | BE-002, BE-034 | todo | |
| BE-036 | E17 | Прогресс/выполнение по чеку для basket/replenishment/collection, откат при возврате | R | BE-035, BE-012 | todo | |
| BE-037 | E17 | `candidate`/`economics` для новых типов: кандидаты, priority, max reward в пределах cap | R | BE-034, BE-010 | todo | |
| AI-013 | E17 | `app/ml` к канону (убрать streak) + тип-специфичная completion-семантика в eval, перегенерация отчёта | T | BE-034, AI-012 | todo | |
| BE-038 | E17 | Интеграция планировщика в production challenges: `planner`/`plan_validator`, rule-based как fallback | R | BE-036, BE-037, AI-013 | todo | |

## Эпики

| Эпик | Файл | Цель |
|---|---|---|
| E0 Foundation | [E0-foundation.md](E0-foundation.md) | Скелеты, схема, константы, контракт |
| E1 Synthetic | [E1-synthetic.md](E1-synthetic.md) | Данные, на которых всё живёт |
| E2 Receipts & Features | [E2-receipts-features.md](E2-receipts-features.md) | Чек и признаки |
| E3 Savings | [E3-savings.md](E3-savings.md) | Экономия |
| E4 Domovoy | [E4-domovoy.md](E4-domovoy.md) | Персонаж |
| E5 Challenges | [E5-challenges.md](E5-challenges.md) | Кандидаты, экономика, LLM-текст, прогресс |
| E6 Pipeline & Frontend core | [E6-pipeline-frontend-core.md](E6-pipeline-frontend-core.md) | Оркестратор, Home, Challenge |
| E7 League | [E7-league.md](E7-league.md) | Лига |
| E8 Referral & Antifraud | [E8-referral-antifraud.md](E8-referral-antifraud.md) | Рефералы, фрод, ачивки |
| E9 Frontend social | [E9-frontend-social.md](E9-frontend-social.md) | League, Referral экраны |
| E10 PM view | [E10-pm-view.md](E10-pm-view.md) | Объяснимость |
| E11 Eval & Simulation | [E11-eval-simulation.md](E11-eval-simulation.md) | Числа для жюри |
| E12 Demo | [E12-demo.md](E12-demo.md) | Сдача |
| E13 Deploy | [E13-deploy.md](E13-deploy.md) | Yandex Cloud VM, образы, CD |
| E14 ML Planner | [E14-ml-planner.md](E14-ml-planner.md) | LLM-планировщик, каталог SKU, reward ladder, синтет-eval |
| E15 Redesign | [E15-redesign.md](E15-redesign.md) | Перерисовка фронта по дизайн-макету |
| E16 Transparency | [E16-transparency.md](E16-transparency.md) | За что баллы и опыт, из чего экономия |
| E17 Challenge types | [E17-challenge-types.md](E17-challenge-types.md) | Единый словарь типов челленджей, интеграция планировщика |
