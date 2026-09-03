import pytest
from psycopg import AsyncConnection

from app.core.errors import AppError
from app.features.domovoy import service as domovoy_service
from app.features.domovoy.models import DomovoyLevelRow
from app.features.users import database, service
from app.features.users.models import UserBasicRow, UserRow


async def test_get_user_raises_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get(_: AsyncConnection, *, user_id: int) -> UserRow | None:
        return None

    monkeypatch.setattr(database, "get_user_by_id", fake_get)

    with pytest.raises(AppError) as exc_info:
        await service.get_user(None, 999)  # type: ignore[arg-type]

    assert exc_info.value.code == "user_not_found"
    assert exc_info.value.status == 404


async def test_list_users_uses_level_from_domovoy_or_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    basics = [
        UserBasicRow(id=1, pseudonym="Уютный Домовой", segment="regular_mid"),
        UserBasicRow(id=2, pseudonym="Тёплый Огонёк", segment="light"),
    ]

    async def fake_list(_: AsyncConnection, *, limit: int) -> list[UserBasicRow]:
        return basics

    async def fake_levels(_: AsyncConnection, *, user_ids: list[int]) -> list[DomovoyLevelRow]:
        return [DomovoyLevelRow(user_id=1, level=5)]

    monkeypatch.setattr(database, "list_users", fake_list)
    monkeypatch.setattr(domovoy_service, "get_levels", fake_levels)

    summaries = await service.list_users(None, limit=50)  # type: ignore[arg-type]

    assert [(s.id, s.level) for s in summaries] == [(1, 5), (2, 1)]


async def test_list_users_returns_empty_without_query(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_list(_: AsyncConnection, *, limit: int) -> list[UserBasicRow]:
        return []

    async def fail_levels(*args: object, **kwargs: object) -> list[DomovoyLevelRow]:
        raise AssertionError("get_levels must not be called for an empty user list")

    monkeypatch.setattr(database, "list_users", fake_list)
    monkeypatch.setattr(domovoy_service, "get_levels", fail_levels)

    assert await service.list_users(None, limit=50) == []  # type: ignore[arg-type]


async def test_generate_pseudonym_retries_until_database_reports_unique(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call_count = 0

    async def fake_exists(_: AsyncConnection, *, pseudonym: str) -> bool:
        nonlocal call_count
        call_count += 1
        return call_count < 3

    monkeypatch.setattr(database, "pseudonym_exists", fake_exists)

    result = await service.generate_pseudonym(None)  # type: ignore[arg-type]

    assert call_count == 3
    assert " " in result
