from datetime import UTC, datetime

import pytest
from psycopg import AsyncConnection

from app.features.challenges import database, service
from app.features.challenges.models import RewardLedgerEntry

CREATED_AT = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)


async def test_record_reward_inserts_ledger_entry_with_given_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    async def fake_insert(_: AsyncConnection, params: dict[str, object]) -> RewardLedgerEntry:
        captured.update(params)
        return RewardLedgerEntry(
            id=1,
            user_id=1,
            kind="receipt_xp",
            xp_delta=10,
            points_delta=0,
            ref_type="receipt",
            ref_id=7,
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

    async def fake_insert(_: AsyncConnection, params: dict[str, object]) -> RewardLedgerEntry:
        captured.update(params)
        return RewardLedgerEntry(
            id=2,
            user_id=1,
            kind="achievement",
            xp_delta=25,
            points_delta=0,
            ref_type=None,
            ref_id=None,
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
