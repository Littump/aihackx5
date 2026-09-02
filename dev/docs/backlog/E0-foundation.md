# E0 — Foundation

Цель: любой агент может взять любую следующую задачу, и у него есть база, константы, фабрики и контракт.

## INF-001 Скелет backend — done
`dev/backend/`: `pyproject.toml` (fastapi, uvicorn, psycopg[binary,pool], pydantic-settings, anthropic; dev: pytest, pytest-asyncio, httpx, ruff, mypy, pyyaml), `app/main.py` с `create_app()` и lifespan, `core/config.py`, `core/db.py` (пул + `get_conn`), `core/errors.py`, `core/logging.py`, `features/health`, `migrations/`, `scripts/migrate.py`, `scripts/export_openapi.py`, `tests/conftest.py`.

## INF-002 Скелет frontend — done
`dev/frontend/`: Vite + React + TS, Tailwind, TanStack Query, react-router, оболочка телефона, ESLint flat, Prettier, Vitest + Testing Library + MSW, `openapi-typescript`.

## INF-003 pre-commit, Makefile, docker-compose — done

## INF-004 Контракт — done
`dev/contracts/openapi.yaml` на все ручки MVP; `make contract-types`, `make contract-check`, `make contract-lint`.

## BE-001 Миграция 001
**Файлы:** `migrations/001_core.sql`.
**Описание:** таблицы `stores`, `users`, `receipts`, `receipt_items`, `user_features`, `domovoy_states`, `challenges`, `reward_ledger` строго по `data-model.md`, с индексами и CHECK.
**AC:**
- `make migrate` применяется на чистой базе и повторно не падает;
- все колонки, типы, NOT NULL, FK и индексы совпадают с `data-model.md`;
- e2e-тест `tests/e2e/test_migrations.py` проверяет наличие всех таблиц через `information_schema`.

## BE-002 Миграция 002
**Файлы:** `migrations/002_social_risk.sql`.
**Описание:** `leagues`, `league_members`, `referrals`, `fraud_checks`, `achievements`, `mechanic_decisions`, `simulation_runs`, `eval_runs`.
**AC:** как BE-001, плюс уникальности `referrals.referee_user_id`, `achievements(user_id, code)`.

## BE-003 game_rules.py
**Файлы:** `app/game_rules.py`, `tests/unit/test_game_rules.py`.
**Описание:** все константы из `domain-rules.md` с теми же именами. Категории, XP, пороги уровней (функция `level_for_xp`), economics, лига, рефералы, веса сигналов антифрода (dict `RECEIPT_SIGNALS`, `REFERRAL_SIGNALS` с `weight` и `strong`), ачивки, параметры симуляции по умолчанию.
**AC:**
- каждая константа из документа есть в модуле;
- `level_for_xp(0)=1, (100)=2, (299)=2, (300)=3, (4500)=10`;
- сумма весов strong-сигналов чека ≥ 0.8 (иначе block недостижим) — тест;
- в модуле нет ничего, кроме констант и `level_for_xp`.

## BE-004 Фабрики
**Файлы:** `tests/factories.py`.
**Описание:** `make_store`, `make_user`, `make_receipt(conn, user_id, *, items=None, purchased_at=None, store_id=None, **overrides)` — вставляет чек с позициями и считает totals, `make_challenge`, `make_domovoy_state`, `make_user_features`.
**AC:** каждая фабрика возвращает dict строки; `make_receipt` без аргументов создаёт валидный чек с 3 позициями двух категорий; тест `tests/e2e/test_factories.py`.
