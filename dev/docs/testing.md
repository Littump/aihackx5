# Тестирование

Полные правила — `.claude/rules/testing.md`. Здесь — устройство инфраструктуры.

## Backend

- `pytest` + `pytest-asyncio` (`asyncio_mode = auto`), `httpx.AsyncClient` поверх `ASGITransport`.
- База для тестов — реальный Postgres `domovoy_test` из `docker-compose.yml`, `TEST_DATABASE_URL` в `.env`.
- `tests/conftest.py`:
  - сессионная фикстура применяет миграции к тестовой базе;
  - `conn` — соединение на тест;
  - `client` — httpx-клиент с переопределённой зависимостью `get_conn`;
  - `autouse` фикстура очищает все таблицы после каждого теста (`TRUNCATE ... RESTART IDENTITY CASCADE`).
- `tests/factories.py` — `make_store`, `make_user`, `make_receipt`, `make_challenge` и т.д. Raw SQL, разумные дефолты, `**overrides`.
- Unit: `tests/unit/<feature>/` — чистые функции и сервисы с `monkeypatch` на `database.py`.
- E2E: `tests/e2e/<feature>/test_router.py` — через ручки.

Команды:
```bash
make test-be
cd dev/backend && uv run pytest -q -k "receipts and not slow"
cd dev/backend && uv run pytest tests/e2e/challenges -q -x
```

## Frontend

- `vitest` + `@testing-library/react` + `jsdom`, `msw` для API.
- `src/test/setup.ts` подключает `@testing-library/jest-dom` и MSW-сервер с хендлерами из `src/test/handlers.ts` (данные соответствуют контракту).
- Тесты рядом с feature: `src/features/<name>/__tests__/`.

```bash
make test-fe
cd dev/frontend && npm run test -- --watch
```

## Что проверяем обязательно

| Область | Тест |
|---|---|
| Economics engine | пример PRD (2→3, 600 ₽ → 30 баллов), минимум 30, максимум 150, отсутствие награды при малой марже |
| Fraud score | каждый сигнал по отдельности, пороги 0.5/0.8, правило «2 strong для block» |
| League score | пример из domain-rules (124), cap savings_rate, ранжирование и зоны |
| Receipt pipeline | чек → XP +10, прогресс +1, выполнение → награда в ledger, дубль в 30 мин не считается, возврат откатывает |
| Savings | формула по чеку, период, дельта, исключение возвратов |
| Referral | new/dormant/active, 500 ₽ порог, 7 дней между покупками, лимит 5/мес |
| Контракт | каждая ручка — набор полей ответа как в `openapi.yaml` |
| Экраны | рендер, ключевое действие, ошибка |
