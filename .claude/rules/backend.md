---
paths:
  - "dev/backend/**"
---

# Backend: FastAPI + raw SQL + pydantic между слоями

## Структура

```
dev/backend/
  app/
    main.py              # create_app(), подключение роутеров, lifespan с пулом
    game_rules.py        # все числа игровых правил, единственное место
    core/
      config.py          # Settings (pydantic-settings), читает .env
      db.py              # пул psycopg, get_conn() и алиас Conn для роутеров
      models.py          # AppModel — базовый класс всех pydantic-моделей
      clock.py           # now(), today(), week_start(), week_end(); единственный источник времени
      errors.py          # AppError + exception handler
      logging.py
    features/<name>/
      router.py          # только HTTP: path, status, dto in/out, вызов service
      dto.py             # pydantic-модели запросов и ответов API, зеркало openapi.yaml
      models.py          # pydantic-модели строк таблиц и доменных объектов feature
      service.py         # бизнес-логика, принимает conn, вызывает database.py
      database.py        # только SQL. Принимает conn и параметры, возвращает модели из models.py
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
| `service.py` | `models.py` и `database.py` свои, `service.py` и `models.py` соседей, `game_rules`, `llm` | HTTP, `fastapi`, `Request`, DTO из `dto.py` |
| `database.py` | `psycopg`, `models.py` свой | всё остальное; никакой логики, только запросы к своим таблицам |
| `models.py` | `core/models.AppModel`, `pydantic` | всё остальное |
| `dto.py` | `core/models.AppModel`, `pydantic`, `models.py` свой | всё остальное |

- Соединение в router — параметр `conn: Conn` (`app.core.db.Conn`). Транзакция открывается там и живёт один запрос; исключение из service откатывает её целиком. Service не открывает соединений.
- Кросс-feature логика (обработка чека, которая трогает challenges, league, domovoy) живёт в service того feature, которому принадлежит событие, и вызывает сервисы соседей. Не database соседей.

## Данные между слоями: только pydantic

- `database.py` возвращает модель из `models.py`, `list[Model]`, скаляр (`int`, `bool`, `Decimal`) или `None`. **Никогда** `dict`, `tuple`, `Row`. Для этого курсор создаётся с `row_factory=class_row(Model)`.
- `service.py` принимает и возвращает модели из `models.py` (свои или соседей), списки моделей, скаляры. Никаких `dict` в сигнатурах и в возвращаемых значениях. Промежуточные структуры тоже модели, а не словари.
- `router.py` превращает модель service в DTO: `XResponse.model_validate(model)` при `model_config = ConfigDict(from_attributes=True)` у DTO. Если DTO агрегирует несколько моделей — собирается явно через конструктор.
- Все модели наследуют `AppModel` из `app/core/models.py` (там уже `from_attributes=True`), а не `BaseModel` напрямую.
- `models.py`: `class UserRow(AppModel)` — строка таблицы, поля один-в-один с колонками (см. `data-model.md`); доменные объекты (`UserFeatures`, `ChallengeDraft`, `FraudDecision`) — тоже здесь. JSONB-колонки описываются вложенными моделями, не `dict[str, Any]`.
- `dict` допустим только как параметры SQL-запроса (`{"user_id": user_id}`) внутри `database.py` и как `params`/`results` при записи JSONB через `model.model_dump(mode="json")`.
- Деньги: в `models.py` — `Decimal` (как отдаёт `NUMERIC`), в `dto.py` — `float`. Pydantic сам приводит `Decimal → float` при `model_validate`; `Decimal` в DTO запрещён, потому что в JSON он превращается в строку, а контракт обещает `number`. Баллы и XP — `int` везде.

## Время

- Текущее время только через `app.core.clock.now()` / `today()` / `week_start()` / `week_end()`. `datetime.now()`, `utcnow()`, `date.today()` запрещены ruff-правилом `TID251`; naive datetime запрещён правилами `DTZ`.
- Все `datetime` aware. Таймзона бизнес-логики — `game_rules.TIMEZONE` (`Europe/Moscow`): неделя лиги и челленджа начинается в понедельник 00:00 по ней. В базе `TIMESTAMPTZ`, psycopg возвращает aware.
- В тестах время замораживается фикстурой `freeze_time(datetime(..., tzinfo=UTC))`. Для демо — `DEMO_NOW=2026-09-05T12:00:00+03:00` в `.env`.

## SQL

- Только `database.py`. Именованные параметры `%(name)s`, никакой конкатенации строк.
- Каждая функция делает один запрос или один логический шаг. Имя функции — глагол: `insert_receipt`, `get_active_challenge`, `list_league_members`.
- Список колонок в `SELECT` пишется явно и совпадает с полями модели. `SELECT *` запрещён.
- Индексы и ограничения — в миграции, не «потом».
- Миграции — только вперёд, файл `migrations/NNN_short_name.sql`, номер на единицу больше последнего. Изменил схему — обновил `dev/docs/data-model.md` и `models.py`.

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
- LLM возвращает текст, никогда — числа наград, порогов, скоров. Вход и выход `llm/` — pydantic-модели.

## Чего не делать

- Не создавать общий `utils.py`. Общее — в `core/` с понятным именем.
- Не хранить состояние в памяти процесса. Всё в Postgres.
- Не писать `async def` там, где нет await.
- Не использовать `dataclass` и `TypedDict` для данных между слоями — только pydantic.
