import pytest
from psycopg import AsyncConnection

from app.features.health import database, service
from app.features.health.models import HealthStatus


@pytest.mark.parametrize(("ping_result", "expected"), [(True, "ok"), (False, "error")])
async def test_check_returns_model(
    monkeypatch: pytest.MonkeyPatch, ping_result: bool, expected: str
) -> None:
    async def fake_ping(_: AsyncConnection) -> bool:
        return ping_result

    monkeypatch.setattr(database, "ping", fake_ping)
    result = await service.check(None)  # type: ignore[arg-type]
    assert isinstance(result, HealthStatus)
    assert result.database == expected
