# Локальная установка

## Нужно на машине

- Python 3.12 и `uv`
- Node 22+ и `npm`
- Docker с Compose v2 (плагин `docker compose` или бинарь `docker-compose` — Makefile найдёт любой)
- `pre-commit` (`uv tool install pre-commit`)

## Первый запуск

```bash
cp .env.example .env
make setup      # uv sync в dev/backend, npm install в dev/frontend, pre-commit install
make up         # Postgres 16 на localhost:5433, базы domovoy и domovoy_test
make migrate    # SQL-миграции в domovoy
make synth      # 300 синтетических пользователей на 10 недель (после E1)
make dev-be     # http://localhost:8000, swagger на /docs
make dev-fe     # http://localhost:5173
```

## Переменные окружения (`.env`)

| Переменная | Значение по умолчанию | |
|---|---|---|
| `DATABASE_URL` | `postgresql://domovoy:domovoy@localhost:5433/domovoy` | |
| `TEST_DATABASE_URL` | `postgresql://domovoy:domovoy@localhost:5433/domovoy_test` | |
| `ANTHROPIC_API_KEY` | пусто | без ключа работает fallback-шаблон |
| `LLM_MODEL` | `claude-sonnet-5` | сверять по скиллу `claude-api` |
| `APP_ENV` | `dev` | |
| `DEMO_NOW` | пусто | ISO-время с зоной, например `2026-09-05T12:00:00+03:00`; замораживает «сейчас» для демо |
| `VITE_API_URL` | `http://localhost:8000` | фронт |

## Проверки

```bash
make check      # ruff, mypy, eslint, prettier --check, check_comments
make format     # ruff format + ruff --fix + prettier --write + eslint --fix
make test-be
make test-fe
make contract-check
make contract-types
```

## Если что-то не так

- Порт 5433 занят — поменять в `docker-compose.yml` и `.env`.
- pre-commit не найден после `make setup` — добавить `~/.local/bin` в `PATH` (туда ставит `uv tool install`).
- `psycopg` не находит libpq — используем `psycopg[binary]`, ничего ставить не нужно.
- Тесты падают с `connection refused` — `make up` и подождать 3 секунды.
- pre-commit ругается «files were modified by this hook» — хук отформатировал файлы, `git add -A` и коммит повторно.
