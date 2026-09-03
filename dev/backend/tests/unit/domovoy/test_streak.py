import pytest
from psycopg import AsyncConnection

from app.features.domovoy import database, service
from app.features.domovoy.models import DomovoyStateRow
from tests.unit.domovoy.data import make_domovoy_state_row


async def test_advance_streak_increments_on_a_completed_hero_week(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    async def fake_get(_: AsyncConnection, *, user_id: int) -> DomovoyStateRow | None:
        return make_domovoy_state_row(streak_weeks=3, streak_freeze_available=True)

    async def fake_update_streak(
        _: AsyncConnection, *, user_id: int, streak_weeks: int, streak_freeze_available: bool
    ) -> DomovoyStateRow:
        captured.update(streak_weeks=streak_weeks, streak_freeze_available=streak_freeze_available)
        return make_domovoy_state_row(
            streak_weeks=streak_weeks, streak_freeze_available=streak_freeze_available
        )

    monkeypatch.setattr(database, "get_domovoy_state", fake_get)
    monkeypatch.setattr(database, "update_streak", fake_update_streak)

    state = await service.advance_streak(
        None,  # type: ignore[arg-type]
        1,
        completed_this_week=True,
    )

    assert captured == {"streak_weeks": 4, "streak_freeze_available": True}
    assert state.streak_weeks == 4


async def test_advance_streak_burns_the_freeze_on_a_missed_week(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    async def fake_get(_: AsyncConnection, *, user_id: int) -> DomovoyStateRow | None:
        return make_domovoy_state_row(streak_weeks=3, streak_freeze_available=True)

    async def fake_update_streak(
        _: AsyncConnection, *, user_id: int, streak_weeks: int, streak_freeze_available: bool
    ) -> DomovoyStateRow:
        captured.update(streak_weeks=streak_weeks, streak_freeze_available=streak_freeze_available)
        return make_domovoy_state_row(
            streak_weeks=streak_weeks, streak_freeze_available=streak_freeze_available
        )

    monkeypatch.setattr(database, "get_domovoy_state", fake_get)
    monkeypatch.setattr(database, "update_streak", fake_update_streak)

    await service.advance_streak(None, 1, completed_this_week=False)  # type: ignore[arg-type]

    assert captured == {"streak_weeks": 3, "streak_freeze_available": False}
