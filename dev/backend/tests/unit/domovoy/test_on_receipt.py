from datetime import UTC, datetime
from decimal import Decimal

import pytest
from psycopg import AsyncConnection

from app.features.challenges import service as challenges_service
from app.features.challenges.models import RewardKind, RewardLedgerEntry
from app.features.domovoy import database, service
from app.features.domovoy.models import DomovoyStateRow
from app.features.receipts import service as receipts_service
from app.features.receipts.models import ReceiptRow, ReceiptWithItems
from app.game_rules import XP_RECEIPT

CREATED_AT = datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
PURCHASED_AT = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)


def _state(**overrides: object) -> DomovoyStateRow:
    base: dict[str, object] = {
        "user_id": 1,
        "xp": 0,
        "level": 1,
        "mood": "bored",
        "mood_reason": "",
        "streak_weeks": 0,
        "streak_freeze_available": True,
        "items": [],
        "last_fed_at": None,
        "updated_at": CREATED_AT,
    }
    base.update(overrides)
    return DomovoyStateRow.model_validate(base)


def _receipt(*, counted: bool) -> ReceiptRow:
    return ReceiptRow(
        id=10,
        user_id=1,
        store_id=5,
        purchased_at=PURCHASED_AT,
        regular_total=Decimal("100.00"),
        paid_total=Decimal("90.00"),
        discount_total=Decimal("10.00"),
        points_earned=0,
        points_spent=0,
        counted=counted,
        is_returned=False,
        returned_at=None,
        source="api",
        pos_id=None,
        created_at=CREATED_AT,
    )


async def test_get_state_returns_existing_row(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get(_: AsyncConnection, *, user_id: int) -> DomovoyStateRow | None:
        assert user_id == 1
        return _state(xp=42)

    async def fail_insert(*args: object, **kwargs: object) -> DomovoyStateRow:
        raise AssertionError("must not create a row when one already exists")

    monkeypatch.setattr(database, "get_domovoy_state", fake_get)
    monkeypatch.setattr(database, "insert_domovoy_state", fail_insert)

    state = await service.get_state(None, 1)  # type: ignore[arg-type]
    assert state.xp == 42


async def test_get_state_creates_default_row_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    async def fake_get(_: AsyncConnection, *, user_id: int) -> DomovoyStateRow | None:
        return None

    async def fake_insert(_: AsyncConnection, params: dict[str, object]) -> DomovoyStateRow:
        captured.update(params)
        return _state()

    monkeypatch.setattr(database, "get_domovoy_state", fake_get)
    monkeypatch.setattr(database, "insert_domovoy_state", fake_insert)

    state = await service.get_state(None, 1)  # type: ignore[arg-type]

    assert state.xp == 0
    assert state.mood == "bored"
    assert captured["user_id"] == 1
    assert captured["xp"] == 0
    assert captured["level"] == 1
    assert captured["mood"] == "bored"
    assert captured["streak_freeze_available"] is True


async def test_add_xp_records_ledger_and_bumps_level(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    async def fake_get(_: AsyncConnection, *, user_id: int) -> DomovoyStateRow | None:
        return _state(xp=95)

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
        captured.update(
            kind=kind,
            xp_delta=xp_delta,
            points_delta=points_delta,
            ref_type=ref_type,
            ref_id=ref_id,
        )
        return RewardLedgerEntry(
            id=1,
            user_id=user_id,
            kind=kind,
            xp_delta=xp_delta,
            points_delta=points_delta,
            ref_type=ref_type,
            ref_id=ref_id,
            created_at=CREATED_AT,
        )

    async def fake_update_xp(
        _: AsyncConnection, *, user_id: int, xp: int, level: int
    ) -> DomovoyStateRow:
        captured.update(xp=xp, level=level)
        return _state(xp=xp, level=level)

    monkeypatch.setattr(database, "get_domovoy_state", fake_get)
    monkeypatch.setattr(challenges_service, "record_reward", fake_record_reward)
    monkeypatch.setattr(database, "update_domovoy_xp", fake_update_xp)

    updated = await service.add_xp(
        None,  # type: ignore[arg-type]
        1,
        XP_RECEIPT,
        kind="receipt_xp",
        ref_type="receipt",
        ref_id=10,
    )

    assert captured == {
        "kind": "receipt_xp",
        "xp_delta": XP_RECEIPT,
        "points_delta": 0,
        "ref_type": "receipt",
        "ref_id": 10,
        "xp": 105,
        "level": 2,
    }
    assert updated.xp == 105
    assert updated.level == 2


async def test_on_receipt_counted_adds_xp_and_feeds_domovoy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _receipt(counted=True)

    async def fake_add_xp(
        _: AsyncConnection,
        user_id: int,
        xp: int,
        *,
        kind: RewardKind,
        ref_type: str | None,
        ref_id: int | None,
    ) -> DomovoyStateRow:
        assert (user_id, xp, kind, ref_type, ref_id) == (1, XP_RECEIPT, "receipt_xp", "receipt", 10)
        return _state(xp=XP_RECEIPT, last_fed_at=None)

    async def fake_list_receipts(
        _: AsyncConnection, *, user_id: int, since: datetime
    ) -> list[ReceiptWithItems]:
        return []

    async def fake_update_mood(
        _: AsyncConnection,
        *,
        user_id: int,
        mood: str,
        mood_reason: str,
        last_fed_at: datetime | None,
    ) -> DomovoyStateRow:
        assert mood == "sleepy"
        assert last_fed_at == PURCHASED_AT
        return _state(xp=XP_RECEIPT, mood=mood, mood_reason=mood_reason, last_fed_at=last_fed_at)

    monkeypatch.setattr(service, "add_xp", fake_add_xp)
    monkeypatch.setattr(receipts_service, "list_counted_receipts_with_items", fake_list_receipts)
    monkeypatch.setattr(database, "update_domovoy_mood", fake_update_mood)

    delta = await service.on_receipt(None, 1, receipt)  # type: ignore[arg-type]

    assert delta.xp_delta == XP_RECEIPT
    assert delta.xp == XP_RECEIPT
    assert delta.mood == "sleepy"
    assert delta.last_fed_at == PURCHASED_AT


async def test_on_receipt_not_counted_keeps_xp_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _receipt(counted=False)

    async def fail_add_xp(*args: object, **kwargs: object) -> DomovoyStateRow:
        raise AssertionError("add_xp must not run for a not counted receipt")

    async def fake_get_state(_: AsyncConnection, *, user_id: int) -> DomovoyStateRow | None:
        return _state(xp=0, last_fed_at=None)

    async def fake_list_receipts(
        _: AsyncConnection, *, user_id: int, since: datetime
    ) -> list[ReceiptWithItems]:
        return []

    async def fake_update_mood(
        _: AsyncConnection,
        *,
        user_id: int,
        mood: str,
        mood_reason: str,
        last_fed_at: datetime | None,
    ) -> DomovoyStateRow:
        assert last_fed_at is None
        return _state(mood=mood, mood_reason=mood_reason, last_fed_at=last_fed_at)

    monkeypatch.setattr(service, "add_xp", fail_add_xp)
    monkeypatch.setattr(database, "get_domovoy_state", fake_get_state)
    monkeypatch.setattr(receipts_service, "list_counted_receipts_with_items", fake_list_receipts)
    monkeypatch.setattr(database, "update_domovoy_mood", fake_update_mood)

    delta = await service.on_receipt(None, 1, receipt)  # type: ignore[arg-type]

    assert delta.xp_delta == 0
    assert delta.xp == 0
    assert delta.last_fed_at is None
