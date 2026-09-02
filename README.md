# aihackx5 — «Домовой»

Хакатон X5: проектирование системы игровой лояльности. Персональный игровой слой поверх X5 Клуба: персонаж, которого кормят реальные чеки, персональный челлендж экономии от ИИ, анонимная «Лига дома» и реферал «Позови соседа».

## Структура

| Путь | Что внутри |
|---|---|
| `docs/product-analysis/` | Продуктовый анализ: [PRODUCT.md](docs/product-analysis/PRODUCT.md), [CONTEXT_PACK.md](docs/product-analysis/CONTEXT_PACK.md), [mechanics/PRD.md](docs/product-analysis/mechanics/PRD.md) — что делаем |
| `dev/docs/` | Техническая документация: [архитектура](dev/docs/architecture.md), [доменные правила](dev/docs/domain-rules.md), [модель данных](dev/docs/data-model.md), [pipeline](dev/docs/dev-pipeline.md), [backlog](dev/docs/backlog/README.md), [команда](dev/docs/team.md) |
| `dev/contracts/openapi.yaml` | Контракт API, пишется до кода |
| `dev/backend/` | FastAPI-монолит, raw SQL (psycopg 3), PostgreSQL 16, SQL-миграции, pytest |
| `dev/frontend/` | React + TypeScript + Vite, mobile-first веб, Vitest |
| `CLAUDE.md`, `.claude/` | Точка входа, правила, скиллы и субагенты для агентной разработки |

## Быстрый старт

```bash
cp .env.example .env
make setup
make up
make migrate
make dev-be
make dev-fe
```

Подробнее — [dev/docs/local-setup.md](dev/docs/local-setup.md). Как работать по задачам — [dev/docs/dev-pipeline.md](dev/docs/dev-pipeline.md), для агента — `CLAUDE.md` и скилл `run-task`.

## Проверки

```bash
make check      # ruff, mypy, eslint, prettier, чекер комментариев
make test-be
make test-fe
make contract-check
```
