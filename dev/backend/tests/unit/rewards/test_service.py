from datetime import UTC, datetime
from decimal import Decimal

import pytest
from psycopg import AsyncConnection

from app.features.challenges import service as challenges_service
from app.features.challenges.models import (
    ChallengeRow,
    RewardKind,
    RewardLedgerEntry,
    RewardLedgerTotals,
)
from app.features.domovoy import service as domovoy_service
from app.features.domovoy.models import DomovoyStateRow
from app.features.receipts import service as receipts_service
from app.features.receipts.models import ReceiptPointsTotals, ReceiptRow
from app.features.rewards import service
from app.features.users import service as users_service
from app.features.users.models import UserRow
from tests.unit.challenges.data import make_challenge_row, make_user_row

NOW = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)


def _ledger_entry(
    *,
    entry_id: int,
    kind: RewardKind,
    xp_delta: int = 0,
    points_delta: int = 0,
    ref_type: str | None = None,
    ref_id: int | None = None,
) -> RewardLedgerEntry:
    return RewardLedgerEntry(
        id=entry_id,
        user_id=1,
        kind=kind,
        xp_delta=xp_delta,
        points_delta=points_delta,
        ref_type=ref_type,
        ref_id=ref_id,
        created_at=NOW,
    )


def _receipt_row(*, receipt_id: int = 7, paid_total: Decimal = Decimal("640.00")) -> ReceiptRow:
    return ReceiptRow(
        id=receipt_id,
        user_id=1,
        store_id=1,
        purchased_at=NOW,
        regular_total=paid_total,
        paid_total=paid_total,
        discount_total=Decimal("0"),
        points_earned=0,
        points_spent=0,
        counted=True,
        is_returned=False,
        returned_at=None,
        source="api",
        pos_id=None,
        created_at=NOW,
    )


def _domovoy_state(xp: int) -> DomovoyStateRow:
    return DomovoyStateRow(
        user_id=1,
        xp=xp,
        level=1,
        mood="cozy",
        mood_reason="",
        streak_weeks=0,
        streak_freeze_available=True,
        items=[],
        last_fed_at=None,
        updated_at=NOW,
    )


def _patch_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    *,
    entries: list[RewardLedgerEntry],
    ledger_points: int,
    receipt_points: ReceiptPointsTotals,
    xp: int = 160,
    challenges: list[ChallengeRow] | None = None,
    receipts: list[ReceiptRow] | None = None,
) -> None:
    async def fake_get_user(_: AsyncConnection, user_id: int) -> UserRow:
        return make_user_row(user_id=user_id)

    async def fake_get_state(_: AsyncConnection, user_id: int) -> DomovoyStateRow:
        return _domovoy_state(xp)

    async def fake_sum_ledger(_: AsyncConnection, user_id: int) -> RewardLedgerTotals:
        return RewardLedgerTotals(points=ledger_points, xp=xp)

    async def fake_list_ledger(
        _: AsyncConnection, user_id: int, limit: int
    ) -> list[RewardLedgerEntry]:
        return entries[:limit]

    async def fake_list_challenges(
        _: AsyncConnection, challenge_ids: list[int]
    ) -> list[ChallengeRow]:
        return challenges or []

    async def fake_list_receipts(_: AsyncConnection, *, receipt_ids: list[int]) -> list[ReceiptRow]:
        return receipts or []

    async def fake_sum_points(_: AsyncConnection, *, user_id: int) -> ReceiptPointsTotals:
        return receipt_points

    monkeypatch.setattr(users_service, "get_user", fake_get_user)
    monkeypatch.setattr(domovoy_service, "get_state", fake_get_state)
    monkeypatch.setattr(challenges_service, "sum_ledger_for_user", fake_sum_ledger)
    monkeypatch.setattr(challenges_service, "list_ledger_for_user", fake_list_ledger)
    monkeypatch.setattr(challenges_service, "list_by_ids", fake_list_challenges)
    monkeypatch.setattr(receipts_service, "list_receipts_by_ids", fake_list_receipts)
    monkeypatch.setattr(receipts_service, "sum_points", fake_sum_points)


async def test_balance_sums_rewards_and_receipt_points(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_dependencies(
        monkeypatch,
        entries=[],
        ledger_points=180,
        receipt_points=ReceiptPointsTotals(earned=90, spent=40),
    )

    result = await service.get_rewards(None, 1, limit=50)  # type: ignore[arg-type]

    assert result.points_from_rewards == 180
    assert result.points_from_receipts == 50
    assert result.points_balance == 230


async def test_history_explains_challenge_and_receipt_entries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entries = [
        _ledger_entry(
            entry_id=2,
            kind="challenge",
            xp_delta=50,
            points_delta=30,
            ref_type="challenge",
            ref_id=9,
        ),
        _ledger_entry(entry_id=1, kind="receipt_xp", xp_delta=10, ref_type="receipt", ref_id=7),
    ]
    _patch_dependencies(
        monkeypatch,
        entries=entries,
        ledger_points=30,
        receipt_points=ReceiptPointsTotals(earned=0, spent=0),
        challenges=[make_challenge_row(id=9)],
        receipts=[_receipt_row()],
    )

    result = await service.get_rewards(None, 1, limit=50)  # type: ignore[arg-type]

    assert [event.title for event in result.history] == [
        "Цель недели выполнена",
        "Покупка засчитана",
    ]
    assert result.history[0].detail == "Заголовок"
    assert result.history[1].detail == "Чек на 640 ₽"


async def test_history_keeps_detail_empty_when_reference_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entries = [_ledger_entry(entry_id=3, kind="streak", xp_delta=100)]
    _patch_dependencies(
        monkeypatch,
        entries=entries,
        ledger_points=0,
        receipt_points=ReceiptPointsTotals(earned=0, spent=0),
    )

    result = await service.get_rewards(None, 1, limit=50)  # type: ignore[arg-type]

    assert result.history[0].detail is None
    assert result.history[0].xp_delta == 100


async def test_level_and_next_level_come_from_xp(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_dependencies(
        monkeypatch,
        entries=[],
        ledger_points=0,
        receipt_points=ReceiptPointsTotals(earned=0, spent=0),
        xp=350,
    )

    result = await service.get_rewards(None, 1, limit=50)  # type: ignore[arg-type]

    assert result.xp == 350
    assert result.level == 3
    assert result.xp_to_next_level == 250
