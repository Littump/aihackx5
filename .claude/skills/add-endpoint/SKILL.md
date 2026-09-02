---
name: add-endpoint
description: Добавить новую HTTP-ручку в backend по слоям router/dto/service/database с контрактом и тестами. Использовать на «добавь ручку», «нужен эндпоинт», «сделай GET /users/{id}/…», «новый роут», «добавь API для экрана».
argument-hint: <METHOD /api/v1/path>
---

# add-endpoint — новая ручка

## Порядок (строго в этой последовательности)

1. **Контракт.** Добавить путь в `dev/contracts/openapi.yaml`: метод, параметры, `requestBody`, `responses` с `$ref` на схемы в `components/schemas`. Имена полей `snake_case`. Ошибки — через общую схему `Error`. Если есть сомнения в форме ответа — посмотреть соседние ручки того же ресурса и PRD-экран, который её потребляет.
2. **DTO.** В `app/features/<feature>/dto.py` — pydantic-модели один-в-один со схемами контракта. Имена классов совпадают с именами схем (`HomeResponse`, `ChallengeDto`).
3. **Database.** Если нужны новые запросы — функции в `database.py` того же feature: `async def get_x(conn, *, user_id: int) -> dict | None`, именованные параметры `%(user_id)s`, `dict_row`. Только свои таблицы.
4. **Service.** Функция в `service.py`: принимает `conn` и простые аргументы, возвращает dict/dataclass. Всю логику — сюда. Числа — из `game_rules.py`. Ошибки — `raise AppError(...)`.
5. **Router.** В `router.py`: `@router.get("/users/{user_id}/x", response_model=XResponse)`, соединение через алиас `Conn` из `app.core.db` (это `Annotated[AsyncConnection, Depends(get_conn)]`), вызов service, преобразование в DTO. Ничего больше.
6. **Регистрация.** Если feature новый — `app/features/<feature>/__init__.py` и `include_router` в `app/main.py` с префиксом `/api/v1`.
7. **Тесты.** `tests/e2e/<feature>/test_router.py`: happy path, 404, 422 (если есть body), сценарий с состоянием. Данные — через `tests/factories.py`. Проверить набор полей ответа по контракту. `tests/unit/<feature>/test_service.py` — на логику.
8. **Проверка.** `make check`, `make test-be`, `make contract-check`. Если фронт уже есть — `make contract-types`.

## Шаблон router

```python
from fastapi import APIRouter

from app.core.db import Conn
from app.features.league import service
from app.features.league.dto import LeagueResponse

router = APIRouter(tags=["league"])


@router.get("/users/{user_id}/league", response_model=LeagueResponse)
async def get_league(user_id: int, conn: Conn) -> LeagueResponse:
    data = await service.get_league_view(conn, user_id=user_id)
    return LeagueResponse.model_validate(data)
```

## Шаблон database

```python
from psycopg import AsyncConnection
from psycopg.rows import dict_row


async def get_league_member(conn: AsyncConnection, *, user_id: int) -> dict | None:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT league_id, score FROM league_members WHERE user_id = %(user_id)s",
            {"user_id": user_id},
        )
        return await cur.fetchone()
```

## Чего не делать

- Не писать SQL в service. Не возвращать из service pydantic-модели ответов.
- Не добавлять ручку, которой нет в контракте.
- Не делать «универсальную» ручку с десятком опциональных параметров — лучше две.
