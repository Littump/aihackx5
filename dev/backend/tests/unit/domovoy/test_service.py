import pytest
from psycopg import AsyncConnection

from app.features.challenges import service as challenges_service
from app.features.challenges.models import RewardKind, RewardLedgerEntry
from app.features.domovoy import database, service
from app.features.domovoy.models import DomovoyLevelRow, DomovoyStateRow
from tests.unit.domovoy.data import PURCHASED_AT, make_domovoy_state_row


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


async def test_add_xp_forwards_a_custom_points_delta_to_the_ledger(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    async def fake_get(_: AsyncConnection, *, user_id: int) -> DomovoyStateRow | None:
        return make_domovoy_state_row(xp=0)

    async def fake_record_reward(
        _: AsyncConnection,
        *,
        user_id: int,
        kind: RewardKind,
        xp_delta: int,
        points_delta: int,
        ref_type: str | None,
        ref_id: int | None,
    ) -> RewardLedgerEntry:
        captured.update(xp_delta=xp_delta, points_delta=points_delta)
        return RewardLedgerEntry(
            id=1,
            user_id=user_id,
            kind=kind,
            xp_delta=xp_delta,
            points_delta=points_delta,
            ref_type=ref_type,
            ref_id=ref_id,
            created_at=PURCHASED_AT,
        )

    async def fake_update_xp(
        _: AsyncConnection, *, user_id: int, xp: int, level: int
    ) -> DomovoyStateRow:
        return make_domovoy_state_row(xp=xp, level=level)

    monkeypatch.setattr(database, "get_domovoy_state", fake_get)
    monkeypatch.setattr(challenges_service, "record_reward", fake_record_reward)
    monkeypatch.setattr(database, "update_domovoy_xp", fake_update_xp)

    await service.add_xp(
        None,  # type: ignore[arg-type]
        1,
        50,
        kind="challenge",
        ref_type="challenge",
        ref_id=9,
        points_delta=30,
    )

    assert captured == {"xp_delta": 50, "points_delta": 30}
