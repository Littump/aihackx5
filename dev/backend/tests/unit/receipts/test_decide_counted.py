from datetime import UTC, datetime

import pytest

from app.features.receipts import database as receipts_db
from app.features.receipts import service
from app.game_rules import RECEIPTS_PER_DAY_MAX

PURCHASED_AT = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)


def _patch_dedup(monkeypatch: pytest.MonkeyPatch, *, exists: bool) -> None:
    async def _fake(*args: object, **kwargs: object) -> bool:
        return exists

    monkeypatch.setattr(receipts_db, "exists_counted_receipt_in_store_within_window", _fake)


def _patch_daily_count(monkeypatch: pytest.MonkeyPatch, *, count: int) -> None:
    async def _fake(*args: object, **kwargs: object) -> int:
        return count

    monkeypatch.setattr(receipts_db, "count_counted_receipts_in_range", _fake)


async def test_decide_counted_true_when_no_dedup_and_below_daily_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_dedup(monkeypatch, exists=False)
    _patch_daily_count(monkeypatch, count=0)

    decision = await service._decide_counted(
        None,  # type: ignore[arg-type]
        user_id=1,
        store_id=5,
        purchased_at=PURCHASED_AT,
    )

    assert decision.counted is True
    assert decision.counted_reason is None


async def test_decide_counted_dedup_window_when_recent_receipt_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_dedup(monkeypatch, exists=True)
    _patch_daily_count(monkeypatch, count=0)

    decision = await service._decide_counted(
        None,  # type: ignore[arg-type]
        user_id=1,
        store_id=5,
        purchased_at=PURCHASED_AT,
    )

    assert decision.counted is False
    assert decision.counted_reason == "dedup_window"


async def test_decide_counted_daily_limit_when_max_already_reached(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_dedup(monkeypatch, exists=False)
    _patch_daily_count(monkeypatch, count=RECEIPTS_PER_DAY_MAX)

    decision = await service._decide_counted(
        None,  # type: ignore[arg-type]
        user_id=1,
        store_id=5,
        purchased_at=PURCHASED_AT,
    )

    assert decision.counted is False
    assert decision.counted_reason == "daily_limit"


async def test_decide_counted_dedup_wins_over_daily_limit_when_both_true(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_dedup(monkeypatch, exists=True)
    _patch_daily_count(monkeypatch, count=RECEIPTS_PER_DAY_MAX)

    decision = await service._decide_counted(
        None,  # type: ignore[arg-type]
        user_id=1,
        store_id=5,
        purchased_at=PURCHASED_AT,
    )

    assert decision.counted is False
    assert decision.counted_reason == "dedup_window"
