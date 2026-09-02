---
name: add-model
description: Добавить новую таблицу или изменить схему БД — SQL-миграция, функции доступа в database.py, обновление data-model.md, фабрика для тестов. Использовать на «добавь модель», «нужна таблица», «добавь колонку», «новая сущность», «напиши миграцию», «поменяй схему».
argument-hint: <имя_таблицы или что меняем>
---

# add-model — новая таблица или изменение схемы

Без ORM. Модель = таблица в миграции + функции в `database.py` + строка в `data-model.md`.

## Шаги

1. **Спроектировать.** Открыть `dev/docs/data-model.md` — проверить, что сущности ещё нет и что она не дублирует существующую. Определить: имя таблицы (`snake_case`, множественное), первичный ключ (`id BIGSERIAL` или естественный), внешние ключи с `ON DELETE`, `NOT NULL` по умолчанию, `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`, индексы под запросы, которые будут.
2. **Миграция.** Файл `dev/backend/migrations/NNN_<short_name>.sql`, `NNN` = последний + 1, три цифры. Один файл — одно логическое изменение. Только `CREATE`/`ALTER`/`CREATE INDEX`. Никаких `DROP` данных без задачи. Файл идемпотентным делать не нужно — runner хранит применённые в `schema_migrations`.
3. **Применить.** `make migrate`. Тестовая база мигрируется автоматически в `tests/conftest.py`.
4. **Функции доступа.** В `app/features/<feature>/database.py`: `insert_x`, `get_x`, `list_x_by_y`, `update_x_field`. Каждая — один запрос, именованные параметры, `dict_row`, `RETURNING` для insert. Таблица принадлежит одному feature; другие feature ходят к ней только через его `service.py`.
5. **Документация.** Добавить таблицу в `dev/docs/data-model.md`: назначение, колонки с типами, индексы, кто владелец.
6. **Фабрика.** В `dev/backend/tests/factories.py` — `async def make_x(conn, **overrides) -> dict` с разумными дефолтами, чтобы e2e-тесты создавали данные одной строкой.
7. **Тест.** Минимум один e2e-тест, который вставляет через фабрику и читает через функцию `database.py` или через ручку.

## Шаблон миграции

```sql
CREATE TABLE achievements (
    id           BIGSERIAL PRIMARY KEY,
    user_id      BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    code         TEXT NOT NULL,
    unlocked_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, code)
);

CREATE INDEX achievements_user_id_idx ON achievements (user_id);
```

## Типы данных

- Деньги и баллы — `NUMERIC(12, 2)` для рублей, `INTEGER` для баллов и XP.
- Время — только `TIMESTAMPTZ`.
- Гибкие структуры (category_affinity, fraud signals) — `JSONB`, но не вместо колонок, по которым фильтруем.
- Перечисления — `TEXT` + `CHECK (status IN (...))`, без `ENUM`-типов.
