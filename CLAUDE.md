# aihackx5 — «Домовой»

Персональный игровой слой поверх X5 Клуба. Хакатон, MVP за несколько дней. Продукт описан в `docs/product-analysis/mechanics/PRD.md` — это источник истины по функциональности. Всё, что ниже, — как мы это строим.

## Стек

- Backend: Python 3.12, FastAPI, монолит, raw SQL через psycopg 3 (без ORM), PostgreSQL 16, SQL-миграции.
- Frontend: TypeScript, React, Vite, mobile-first веб (один экран шириной до 430px), TanStack Query, react-router, Tailwind.
- LLM: Anthropic SDK, только для текста и объяснений. LLM не назначает награды и не считает деньги.
- Тесты: pytest (unit + e2e через реальный Postgres), Vitest.
- Качество: ruff, mypy, ESLint, Prettier, pre-commit. Коммит без зелёных хуков невозможен.

## Где что лежит

| Путь | Что там |
|---|---|
| `docs/product-analysis/mechanics/PRD.md` | Что делаем. Читать первым |
| `dev/docs/README.md` | Индекс технической документации |
| `dev/docs/architecture.md` | Слои, папки, поток данных, границы модулей |
| `dev/docs/domain-rules.md` | Все числа и формулы: XP, savings, economics, лига, антифрод, рефералы |
| `dev/docs/data-model.md` | Таблицы и колонки |
| `dev/contracts/openapi.yaml` | Контракт API. Меняется до кода, а не после |
| `dev/docs/dev-pipeline.md` | Как берём задачу и доводим до done |
| `dev/docs/backlog/` | Эпики и задачи с acceptance criteria |
| `dev/docs/team.md` | Кто что делает |
| `dev/docs/decisions.md` | Почему архитектура такая; не переспаривать без новой информации |
| `dev/docs/deploy.md` | Деплой на Yandex Cloud VM и CD |
| `.claude/rules/` | Правила для кода: backend, frontend, testing, style |
| `.claude/skills/` | Рецепты: run-task, add-endpoint, add-model, add-logic, add-screen, update-api-contract |
| `.claude/agents/` | Субагенты: backend-dev, frontend-dev, qa-tester, reviewer |

## Обязательный порядок перед любой задачей

1. Прочитать `dev/docs/backlog/README.md` и файл эпика задачи — там acceptance criteria.
2. Прочитать `dev/docs/architecture.md` и `.claude/rules/code-style.md`.
3. Прочитать профильные правила: `.claude/rules/backend.md` или `.claude/rules/frontend.md`, всегда `.claude/rules/testing.md`.
4. Если задача про числа и формулы — `dev/docs/domain-rules.md`. Если про API — `dev/contracts/openapi.yaml`.
5. Если задача укладывается в скилл (`add-endpoint`, `add-model`, `add-logic`, `add-screen`, `update-api-contract`) — работать по скиллу, а не по памяти.

Полный цикл одной задачи — скилл `run-task`: разработчик → тестировщик → ревьюер → статус в backlog.

## Жёсткие правила (нарушение = задача не принята)

- Слои backend: `router.py` → `service.py` → `database.py`. Router не знает про SQL, database не знает про HTTP, service не знает ни того, ни другого. DTO только в `dto.py`.
- SQL пишется руками в `database.py` и нигде больше. ORM, query builder и SQL-строки в сервисах запрещены.
- Между слоями ходят только pydantic-модели из `models.py`: `database.py` возвращает модели через `class_row`, `service.py` принимает и отдаёт модели, `router.py` превращает их в DTO. Никаких `dict`, `tuple`, `dataclass`, `TypedDict`.
- Докстринги и комментарии не длиннее одной строки. Многострочные докстринги, блочные комментарии и два комментария подряд запрещены — это проверяет хук `scripts/check_comments.py`.
- Каждая ручка имеет e2e-тест через реальный Postgres. Каждая функция сервиса с логикой имеет unit-тест.
- Каждое изменение API начинается с `dev/contracts/openapi.yaml`, затем backend, затем `make contract-types` для фронта.
- Числа игровых правил живут только в `dev/backend/app/game_rules.py` и зеркалятся в `dev/docs/domain-rules.md`. Магические константы в сервисах запрещены.
- Время только через `app/core/clock.py`; `datetime.now()` и naive datetime не проходят ruff. Деньги: `Decimal` в моделях, `float` в DTO.
- LLM-вызовы только через `app/llm/`, всегда с детерминированным fallback, чтобы тесты и демо работали без ключа.
- Никаких ФИО, адресов и абсолютных чужих трат в ответах API рейтинга.

## Команды

```bash
make setup          # uv sync, npm install, pre-commit install
make up             # Postgres в docker (порт 5433)
make migrate        # применить SQL-миграции
make test-db-reset  # пересоздать domovoy_test (после правки уже применённой миграции)
make dev-be         # uvicorn с reload на :8000
make dev-fe         # vite на :5173
make test-be        # pytest unit + e2e
make test-fe        # vitest
make check          # ruff + mypy + eslint + prettier --check + check_comments
make format         # автоформат всего
make contract-types # openapi.yaml -> src/shared/api/schema.d.ts
make contract-check # сравнить openapi.yaml с тем, что отдаёт backend
```

## Язык

Документация, комментарии в backlog, сообщения коммитов — русский. Код, идентификаторы, названия таблиц и полей API — английский.
