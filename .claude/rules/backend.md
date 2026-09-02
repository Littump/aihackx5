---
paths:
  - "dev/backend/**"
---

# Backend: FastAPI + raw SQL

## Структура

```
dev/backend/
  app/
    main.py              # create_app(), подключение роутеров, lifespan с пулом
    game_rules.py        # все числа игровых правил, единственное место
    core/
      config.py          # Settings (pydantic-settings), читает .env
      db.py              # пул psycopg, get_conn() и алиас Conn для роутеров
      errors.py          # AppError + exception handler
      logging.py
    features/<name>/
      router.py          # только HTTP: path, status, dto in/out, вызов service
      dto.py             # pydantic-модели запросов и ответов, ничего больше
      service.py         # бизнес-логика, принимает conn, вызывает database.py
      database.py        # только SQL. Функции принимают conn и параметры, возвращают dict/list[dict]
    llm/                 # клиент Anthropic, промпты, fallback-шаблоны
    synthetic/           # генератор синтетических данных (CLI)
    eval/                # оценка relevance челленджей
    simulation/          # control vs treatment
  migrations/NNN_name.sql
  scripts/migrate.py
  tests/
    conftest.py
    factories.py
    unit/<feature>/test_service.py
    e2e/<feature>/test_router.py
```

## Слои и что кому можно

| Слой | Импортирует | Запрещено |
|---|---|---|
| `router.py` | `dto.py`, `service.py` своего feature, `core/db.Conn` | SQL, другие features, бизнес-логика, `game_rules` |
| `service.py` | `database.py` своего feature, `service.py` других features, `game_rules`, `llm` | HTTP, `fastapi`, `Request`, DTO ответов |
| `database.py` | `psycopg` | всё остальное; никакой логики, только запросы к своим таблицам |
| `dto.py` | `pydantic` | всё остальное |

- Соединение в router — параметр `conn: Conn` (`app.core.db.Conn`). Транзакция открывается там и живёт один запрос; исключение из service откатывает её целиком. Service не открывает соединений.
- Service получает и возвращает простые типы: dict, dataclass, list. Преобразование в DTO — в router.
- Кросс-feature логика (например, обработка чека, которая трогает challenges, league, domovoy) живёт в service того feature, которому принадлежит событие, и вызывает сервисы соседей. Не database соседей.

## SQL

- Только `database.py`. Именованные параметры `%(name)s`, никакой конкатенации строк.
- Каждая функция делает один запрос или один логический шаг. Имя функции — глагол: `insert_receipt`, `get_active_challenge`, `list_league_members`.
- Возвращать `dict_row`. Не возвращать курсор.
- Индексы и ограничения — в миграции, не «потом».
- Миграции — только вперёд, файл `migrations/NNN_short_name.sql`, номер на единицу больше последнего. Изменил схему — обновил `dev/docs/data-model.md`.

## Ручки

- Префикс `/api/v1`. Именование ресурсное: `GET /users/{user_id}/challenges`, `POST /receipts`.
- Сначала правишь `dev/contracts/openapi.yaml`, потом код. Response-модель в router обязательна (`response_model=`).
- Ошибки только через `AppError`. Формат ответа об ошибке — `{"error": {"code": "...", "message": "..."}}`.
- Демо-ручки (`/receipts/simulate`, переключение пользователя) — обычные ручки, тестируются так же.

## Типы и инструменты

- Аннотации типов везде. `mypy` в `make check` должен быть зелёным.
- `ruff` — линтер и форматтер, конфиг в `pyproject.toml`. Не добавлять `# noqa` без причины в той же строке.
- Зависимости через `uv add`. Не редактировать `pyproject.toml` руками ради версии.

## LLM

- Только `app/llm/`. Перед первым использованием Anthropic SDK прочитать скилл `claude-api` — модели и параметры сверять там, не по памяти.
- Любая функция в `llm/` имеет fallback на шаблон, если нет `ANTHROPIC_API_KEY` или вызов упал. Тесты работают без ключа и без сети.
- LLM возвращает текст, никогда — числа наград, порогов, скоров.

## Чего не делать

- Не создавать общий `utils.py`. Общее — в `core/` с понятным именем.
- Не хранить состояние в памяти процесса. Всё в Postgres.
- Не писать `async def` там, где нет await.
