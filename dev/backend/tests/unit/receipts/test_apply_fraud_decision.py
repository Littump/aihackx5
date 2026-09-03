from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.features.antifraud.models import FraudDecision, FraudDecisionKind
from app.features.receipts import database as receipts_db
from app.features.receipts import service
from app.features.receipts.models import CountedDecision, ReceiptRow

PURCHASED_AT = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)
CREATED_AT = datetime(2026, 9, 2, 10, 0, tzinfo=UTC)


def _receipt_row(*, counted: bool) -> ReceiptRow:
    return ReceiptRow(
        id=10,
        user_id=1,
        store_id=5,
        purchased_at=PURCHASED_AT,
        regular_total=Decimal("100.00"),
        paid_total=Decimal("100.00"),
        discount_total=Decimal("0.00"),
        points_earned=0,
        points_spent=0,
        counted=counted,
        is_returned=False,
        returned_at=None,
        source="api",
        pos_id=None,
        created_at=CREATED_AT,
    )


def _fraud_decision(decision: FraudDecisionKind) -> FraudDecision:
    return FraudDecision(score=0.9, decision=decision, signals=[])


def _patch_update_counted(monkeypatch: pytest.MonkeyPatch) -> list[bool]:
    calls: list[bool] = []

    async def _fake(_: object, *, receipt_id: int, counted: bool) -> ReceiptRow:
        calls.append(counted)
        return _receipt_row(counted=counted)

    monkeypatch.setattr(receipts_db, "update_receipt_counted", _fake)
    return calls


async def test_apply_fraud_decision_block_flips_counted_receipt_to_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _patch_update_counted(monkeypatch)
    receipt_row = _receipt_row(counted=True)
    decision = CountedDecision(counted=True, counted_reason=None)

    updated_row, updated_decision = await service._apply_fraud_decision(
        None,  # type: ignore[arg-type]
        receipt_row=receipt_row,
        decision=decision,
        fraud_decision=_fraud_decision("block"),
    )

    assert calls == [False]
    assert updated_row.counted is False
    assert updated_decision.counted is False
    assert updated_decision.counted_reason == "fraud_block"


async def test_apply_fraud_decision_block_keeps_original_reason_when_already_uncounted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _patch_update_counted(monkeypatch)
    receipt_row = _receipt_row(counted=False)
    decision = CountedDecision(counted=False, counted_reason="dedup_window")

    updated_row, updated_decision = await service._apply_fraud_decision(
        None,  # type: ignore[arg-type]
        receipt_row=receipt_row,
        decision=decision,
        fraud_decision=_fraud_decision("block"),
    )

    assert calls == []
    assert updated_row is receipt_row
    assert updated_decision.counted_reason == "dedup_window"


async def test_apply_fraud_decision_hold_does_not_change_counted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _patch_update_counted(monkeypatch)
    receipt_row = _receipt_row(counted=True)
    decision = CountedDecision(counted=True, counted_reason=None)

    updated_row, updated_decision = await service._apply_fraud_decision(
        None,  # type: ignore[arg-type]
        receipt_row=receipt_row,
        decision=decision,
        fraud_decision=_fraud_decision("hold"),
    )

    assert calls == []
    assert updated_row is receipt_row
    assert updated_decision.counted is True
    assert updated_decision.counted_reason is None


async def test_apply_fraud_decision_approve_does_not_change_counted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _patch_update_counted(monkeypatch)
    receipt_row = _receipt_row(counted=True)
    decision = CountedDecision(counted=True, counted_reason=None)

    updated_row, updated_decision = await service._apply_fraud_decision(
        None,  # type: ignore[arg-type]
        receipt_row=receipt_row,
        decision=decision,
        fraud_decision=_fraud_decision("approve"),
    )

    assert calls == []
    assert updated_row is receipt_row
    assert updated_decision.counted is True
