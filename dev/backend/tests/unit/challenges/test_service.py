from datetime import UTC, datetime

import pytest
from psycopg import AsyncConnection

from app.core.errors import AppError
from app.features.challenges import database, service
from app.features.challenges.models import ChallengeRow, RewardLedgerEntry
from app.features.users import service as users_service
from app.features.users.models import UserRow
from tests.unit.challenges.data import make_challenge_row, make_user_row

CREATED_AT = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)


async def test_record_reward_passes_fields_through_to_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    async def fake_insert(
        _: AsyncConnection,
        *,
        user_id: int,
        kind: str,
        xp_delta: int,
        points_delta: int,
        ref_type: str | None,
        ref_id: int | None,
    ) -> RewardLedgerEntry:
        captured.update(
            user_id=user_id,
            kind=kind,
            xp_delta=xp_delta,
            points_delta=points_delta,
            ref_type=ref_type,
            ref_id=ref_id,
        )
        return RewardLedgerEntry(
            id=1,
            user_id=user_id,
            kind="receipt_xp",
            xp_delta=xp_delta,
            points_delta=points_delta,
            ref_type=ref_type,
            ref_id=ref_id,
            created_at=CREATED_AT,
        )

    monkeypatch.setattr(database, "insert_reward_ledger_entry", fake_insert)

    entry = await service.record_reward(
        None,  # type: ignore[arg-type]
        user_id=1,
        kind="receipt_xp",
        xp_delta=10,
        points_delta=0,
        ref_type="receipt",
        ref_id=7,
    )

    assert captured == {
        "user_id": 1,
        "kind": "receipt_xp",
        "xp_delta": 10,
        "points_delta": 0,
        "ref_type": "receipt",
        "ref_id": 7,
    }
    assert entry.kind == "receipt_xp"
    assert entry.xp_delta == 10
    assert entry.points_delta == 0
    assert entry.ref_type == "receipt"
    assert entry.ref_id == 7


async def test_record_reward_accepts_null_ref(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    async def fake_insert(
        _: AsyncConnection,
        *,
        user_id: int,
        kind: str,
        xp_delta: int,
        points_delta: int,
        ref_type: str | None,
        ref_id: int | None,
    ) -> RewardLedgerEntry:
        captured.update(ref_type=ref_type, ref_id=ref_id)
        return RewardLedgerEntry(
            id=2,
            user_id=user_id,
            kind="achievement",
            xp_delta=xp_delta,
            points_delta=points_delta,
            ref_type=ref_type,
            ref_id=ref_id,
            created_at=CREATED_AT,
        )

    monkeypatch.setattr(database, "insert_reward_ledger_entry", fake_insert)

    entry = await service.record_reward(
        None,  # type: ignore[arg-type]
        user_id=1,
        kind="achievement",
        xp_delta=25,
        points_delta=0,
        ref_type=None,
        ref_id=None,
    )

    assert captured["ref_type"] is None
    assert captured["ref_id"] is None
    assert entry.kind == "achievement"


async def test_get_list_splits_rows_into_hero_side_and_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hero_row = make_challenge_row(id=1, is_hero=True, status="active")
    side_row = make_challenge_row(id=2, is_hero=False, status="active", type="category")
    history_row = make_challenge_row(id=3, is_hero=True, status="expired")

    async def fake_get_user(_: AsyncConnection, user_id: int) -> UserRow:
        return make_user_row(user_id=user_id)

    async def fake_list(_: AsyncConnection, *, user_id: int) -> list[ChallengeRow]:
        return [hero_row, side_row, history_row]

    monkeypatch.setattr(users_service, "get_user", fake_get_user)
    monkeypatch.setattr(database, "list_challenges_by_user", fake_list)

    result = await service.get_list(None, 1)  # type: ignore[arg-type]

    assert result.hero == hero_row
    assert result.side == [side_row]
    assert result.history == [history_row]


async def test_get_list_hero_is_none_without_an_active_hero_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    side_row = make_challenge_row(id=2, is_hero=False, status="active")

    async def fake_get_user(_: AsyncConnection, user_id: int) -> UserRow:
        return make_user_row(user_id=user_id)

    async def fake_list(_: AsyncConnection, *, user_id: int) -> list[ChallengeRow]:
        return [side_row]

    monkeypatch.setattr(users_service, "get_user", fake_get_user)
    monkeypatch.setattr(database, "list_challenges_by_user", fake_list)

    result = await service.get_list(None, 1)  # type: ignore[arg-type]

    assert result.hero is None
    assert result.side == [side_row]
    assert result.history == []


async def test_get_one_returns_row_for_the_owning_user(monkeypatch: pytest.MonkeyPatch) -> None:
    row = make_challenge_row(id=5, user_id=1)

    async def fake_get_user(_: AsyncConnection, user_id: int) -> UserRow:
        return make_user_row(user_id=user_id)

    async def fake_get_challenge(_: AsyncConnection, *, challenge_id: int) -> ChallengeRow:
        return row

    monkeypatch.setattr(users_service, "get_user", fake_get_user)
    monkeypatch.setattr(database, "get_challenge_by_id", fake_get_challenge)

    result = await service.get_one(None, 1, 5)  # type: ignore[arg-type]

    assert result == row


async def test_get_one_raises_not_found_when_challenge_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get_user(_: AsyncConnection, user_id: int) -> UserRow:
        return make_user_row(user_id=user_id)

    async def fake_get_challenge(_: AsyncConnection, *, challenge_id: int) -> ChallengeRow | None:
        return None

    monkeypatch.setattr(users_service, "get_user", fake_get_user)
    monkeypatch.setattr(database, "get_challenge_by_id", fake_get_challenge)

    with pytest.raises(AppError) as exc_info:
        await service.get_one(None, 1, 999)  # type: ignore[arg-type]

    assert exc_info.value.code == "challenge_not_found"
    assert exc_info.value.status == 404


async def test_get_one_raises_not_found_for_a_foreign_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    foreign_row = make_challenge_row(id=5, user_id=2)

    async def fake_get_user(_: AsyncConnection, user_id: int) -> UserRow:
        return make_user_row(user_id=user_id)

    async def fake_get_challenge(_: AsyncConnection, *, challenge_id: int) -> ChallengeRow:
        return foreign_row

    monkeypatch.setattr(users_service, "get_user", fake_get_user)
    monkeypatch.setattr(database, "get_challenge_by_id", fake_get_challenge)

    with pytest.raises(AppError) as exc_info:
        await service.get_one(None, 1, 5)  # type: ignore[arg-type]

    assert exc_info.value.code == "challenge_not_found"
