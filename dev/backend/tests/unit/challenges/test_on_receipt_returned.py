from datetime import datetime
from decimal import Decimal
from typing import Literal

import pytest
from psycopg import AsyncConnection

from app.features.challenges import database, service
from app.features.challenges.models import ChallengeRow, RewardLedgerEntry
from app.features.receipts.models import ReceiptDetail
from tests.unit.challenges.data import COMPUTED_AT, make_challenge_row, make_receipt_detail

Status = Literal["active", "completed", "failed", "expired"]


async def _echo_update_progress(
    _: AsyncConnection,
    *,
    challenge_id: int,
    progress: Decimal,
    status: Status,
    completed_at: datetime | None,
) -> ChallengeRow:
    return make_challenge_row(id=challenge_id, progress=progress, status=status)


async def test_on_receipt_returned_reopens_completed_challenge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    challenge = make_challenge_row(
        id=5, type="frequency", status="completed", progress=Decimal("3"), target=Decimal("3")
    )
    ledger_calls: list[dict[str, object]] = []

    async def fake_list(
        _: AsyncConnection, *, user_id: int, purchased_at: datetime, statuses: list[str]
    ) -> list[ChallengeRow]:
        assert set(statuses) == {"active", "completed"}
        return [challenge]

    async def fake_record_reward(
        _: AsyncConnection,
        *,
        user_id: int,
        kind: str,
        xp_delta: int,
        points_delta: int,
        ref_type: str | None,
        ref_id: int | None,
    ) -> RewardLedgerEntry:
        ledger_calls.append(
            {
                "kind": kind,
                "xp_delta": xp_delta,
                "points_delta": points_delta,
                "ref_type": ref_type,
                "ref_id": ref_id,
            }
        )
        return RewardLedgerEntry(
            id=1,
            user_id=user_id,
            kind="challenge",
            xp_delta=xp_delta,
            points_delta=points_delta,
            ref_type=ref_type,
            ref_id=ref_id,
            created_at=COMPUTED_AT,
        )

    monkeypatch.setattr(database, "list_challenges_for_period", fake_list)
    monkeypatch.setattr(database, "update_progress", _echo_update_progress)
    monkeypatch.setattr(service, "record_reward", fake_record_reward)

    deltas = await service.on_receipt_returned(
        None,  # type: ignore[arg-type]
        1,
        make_receipt_detail(),
    )

    assert deltas[0].progress_before == Decimal("3")
    assert deltas[0].progress_after == Decimal("2")
    assert deltas[0].completed is False
    assert deltas[0].reward_points == -30
    assert ledger_calls == [
        {
            "kind": "challenge",
            "xp_delta": 0,
            "points_delta": -30,
            "ref_type": "challenge",
            "ref_id": 5,
        }
    ]


async def test_on_receipt_returned_keeps_completed_above_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    challenge = make_challenge_row(
        id=6, type="frequency", status="completed", progress=Decimal("4"), target=Decimal("3")
    )

    async def fake_list(
        _: AsyncConnection, *, user_id: int, purchased_at: datetime, statuses: list[str]
    ) -> list[ChallengeRow]:
        return [challenge]

    async def fail_record_reward(*args: object, **kwargs: object) -> RewardLedgerEntry:
        raise AssertionError("must not reopen a challenge still above target")

    monkeypatch.setattr(database, "list_challenges_for_period", fake_list)
    monkeypatch.setattr(database, "update_progress", _echo_update_progress)
    monkeypatch.setattr(service, "record_reward", fail_record_reward)

    deltas = await service.on_receipt_returned(
        None,  # type: ignore[arg-type]
        1,
        make_receipt_detail(),
    )

    assert deltas[0].progress_after == Decimal("3")
    assert deltas[0].completed is True
    assert deltas[0].reward_points == 0


async def test_on_receipt_returned_active_challenge_only_decrements(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    challenge = make_challenge_row(
        id=7, type="frequency", status="active", progress=Decimal("2"), target=Decimal("3")
    )

    async def fake_list(
        _: AsyncConnection, *, user_id: int, purchased_at: datetime, statuses: list[str]
    ) -> list[ChallengeRow]:
        return [challenge]

    async def fail_record_reward(*args: object, **kwargs: object) -> RewardLedgerEntry:
        raise AssertionError("must not touch the ledger for an active challenge")

    monkeypatch.setattr(database, "list_challenges_for_period", fake_list)
    monkeypatch.setattr(database, "update_progress", _echo_update_progress)
    monkeypatch.setattr(service, "record_reward", fail_record_reward)

    deltas = await service.on_receipt_returned(
        None,  # type: ignore[arg-type]
        1,
        make_receipt_detail(),
    )

    assert deltas[0].progress_after == Decimal("1")
    assert deltas[0].completed is False


async def test_on_receipt_returned_ignores_non_matching_category(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    challenge = make_challenge_row(
        id=8, type="category", category="dairy", status="active", progress=Decimal("1")
    )

    async def fake_list(
        _: AsyncConnection, *, user_id: int, purchased_at: datetime, statuses: list[str]
    ) -> list[ChallengeRow]:
        return [challenge]

    async def fail_update(*args: object, **kwargs: object) -> ChallengeRow:
        raise AssertionError("must not update a challenge the receipt never touched")

    monkeypatch.setattr(database, "list_challenges_for_period", fake_list)
    monkeypatch.setattr(database, "update_progress", fail_update)

    receipt: ReceiptDetail = make_receipt_detail(categories=["bakery"])
    deltas = await service.on_receipt_returned(None, 1, receipt)  # type: ignore[arg-type]

    assert deltas == []


async def test_on_receipt_returned_not_counted_is_a_noop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_list(*args: object, **kwargs: object) -> list[ChallengeRow]:
        raise AssertionError("a not counted receipt never moved progress, nothing to revert")

    monkeypatch.setattr(database, "list_challenges_for_period", fail_list)

    receipt: ReceiptDetail = make_receipt_detail(counted=False)
    deltas = await service.on_receipt_returned(None, 1, receipt)  # type: ignore[arg-type]

    assert deltas == []
