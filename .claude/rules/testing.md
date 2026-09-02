# Тестирование

## Принцип

Тест — часть задачи, не отдельная задача. Задача без тестов не закрывается. QA-агент пишет и запускает тесты после разработчика, разработчик пишет базовые тесты сам.

## Backend

### Unit (`tests/unit/<feature>/`)
- Тестируют `service.py` и чистые функции (`game_rules`, экономика, скоринг). База мокается на уровне функций `database.py` через `monkeypatch`, или сервис принимает готовые данные.
- Обязательны для: economics engine, fraud score, league score, расчёт savings, XP/level/mood, выбор challenge. На каждую формулу из `domain-rules.md` — минимум один тест с числовым примером из документа.

### E2E (`tests/e2e/<feature>/`)
- Один файл на router. Через `httpx.AsyncClient` поверх приложения и реального Postgres (`TEST_DATABASE_URL`).
- Фикстуры из `tests/conftest.py`: `client`, `conn`, автоочистка таблиц после каждого теста. Данные создаются через `tests/factories.py` (raw SQL), не через ручки, если только сама ручка не тестируется.
- На каждую ручку: happy path, 404 для чужого/несуществующего ресурса, валидационная ошибка (422) если есть body, и один сценарий с состоянием (например, чек обновил прогресс челленджа).
- Проверять ответ по контракту: поля и типы из `openapi.yaml`. Лишние поля — ошибка.

### Запуск
```bash
make test-be                       # всё
cd dev/backend && uv run pytest tests/unit -q
cd dev/backend && uv run pytest tests/e2e -q -k receipts
```

## Frontend

- Vitest + Testing Library, `features/<name>/__tests__/`.
- На экран: рендер с моком API, ключевое действие, состояние ошибки.
- `npm run test` в `dev/frontend`.

## Что не делаем

- Не тестируем pydantic-валидацию сама по себе, только свои правила.
- Не пишем тесты, которые проверяют SQL-строку текстом.
- Не мокаем Postgres в e2e.

## Definition of Done для задачи

- [ ] acceptance criteria из backlog выполнены;
- [ ] unit-тесты на логику, e2e на ручки, тесты экрана на фронте;
- [ ] `make check` и `make test-be` / `make test-fe` зелёные;
- [ ] контракт, `data-model.md`, `domain-rules.md` обновлены, если менялись;
- [ ] статус задачи в `dev/docs/backlog/README.md` обновлён.
