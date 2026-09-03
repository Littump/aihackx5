import pytest
from psycopg import AsyncConnection

from app.features.domovoy import database, service
from app.features.domovoy.models import DomovoyLevelRow


async def test_get_levels_skips_query_for_empty_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fail_list(*args: object, **kwargs: object) -> list[DomovoyLevelRow]:
        raise AssertionError("list_levels must not be called for an empty id list")

    monkeypatch.setattr(database, "list_levels", fail_list)

    assert await service.get_levels(None, user_ids=[]) == []  # type: ignore[arg-type]


async def test_get_levels_returns_rows_from_database(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = [DomovoyLevelRow(user_id=1, level=3)]

    async def fake_list(_: AsyncConnection, *, user_ids: list[int]) -> list[DomovoyLevelRow]:
        assert user_ids == [1]
        return expected

    monkeypatch.setattr(database, "list_levels", fake_list)

    result = await service.get_levels(None, user_ids=[1])  # type: ignore[arg-type]
    assert result == expected
