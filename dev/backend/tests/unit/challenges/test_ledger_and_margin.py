from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from psycopg import AsyncConnection

from app.core.clock import TZ, month_end, month_start
from app.features.challenges import database, service
from app.features.challenges.models import (
    ChallengeEconomics,
    ChallengeRow,
    RewardLedgerEntry,
    RewardLedgerTotals,
)
from tests.unit.challenges.data import make_challenge_row

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
CREATED_AT = datetime(2026, 9, 10, 9, 0, tzinfo=UTC)


def _economics(margin: float) -> ChallengeEconomics:
    return ChallengeEconomics(
        avg_basket=600.0,
        expected_incremental_purchases=1.0,
        expected_incremental_margin=margin,
        max_reward_rub=36.0,
        contribution_margin=0.15,
        reward_share_max=0.4,
    )


async def test_list_ledger_for_user_delegates_to_database(monkeypatch: pytest.MonkeyPatch) -> None:
    entries = [
        RewardLedgerEntry(
            id=1,
            user_id=1,
            kind="receipt_xp",
            xp_delta=5,
            points_delta=0,
            ref_type="receipt",
            ref_id=1,
            created_at=CREATED_AT,
        )
    ]

    async def fake_list(_: AsyncConnection, *, user_id: int, limit: int) -> list[RewardLedgerEntry]:
        assert user_id == 1
        assert limit == 20
        return entries

    monkeypatch.setattr(database, "list_reward_ledger_for_user", fake_list)

    result = await service.list_ledger_for_user(None, 1, 20)  # type: ignore[arg-type]

    assert result == entries


async def test_sum_ledger_for_user_delegates_to_database(monkeypatch: pytest.MonkeyPatch) -> None:
    totals = RewardLedgerTotals(points=120, xp=340)

    async def fake_sum(_: AsyncConnection, *, user_id: int) -> RewardLedgerTotals:
        assert user_id == 1
        return totals

    monkeypatch.setattr(database, "sum_reward_ledger_for_user", fake_sum)

    result = await service.sum_ledger_for_user(None, 1)  # type: ignore[arg-type]

    assert result == totals


async def test_sum_expected_margin_for_month_sums_active_and_completed_challenges(
    monkeypatch: pytest.MonkeyPatch, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    rows: list[ChallengeRow] = [
        make_challenge_row(id=1, status="active", economics=_economics(90.0)),
        make_challenge_row(id=2, status="completed", economics=_economics(45.5)),
    ]

    async def fake_list(
        _: AsyncConnection,
        *,
        user_id: int,
        month_start: datetime,
        month_end: datetime,
        statuses: list[str],
    ) -> list[ChallengeRow]:
        assert user_id == 1
        assert statuses == ["active", "completed"]
        return rows

    monkeypatch.setattr(database, "list_challenges_for_user_in_month", fake_list)

    result = await service.sum_expected_margin_for_month(None, 1)  # type: ignore[arg-type]

    assert result == 135.5


async def test_sum_expected_margin_for_month_is_zero_without_challenges(
    monkeypatch: pytest.MonkeyPatch, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)

    async def fake_list(_: AsyncConnection, **__: object) -> list[ChallengeRow]:
        return []

    monkeypatch.setattr(database, "list_challenges_for_user_in_month", fake_list)

    result = await service.sum_expected_margin_for_month(None, 1)  # type: ignore[arg-type]

    assert result == 0


MONTH_BOUNDARY_CASES: list[tuple[datetime, datetime, datetime]] = [
    (
        datetime(2026, 9, 15, 12, 0, tzinfo=UTC),
        datetime(2026, 9, 1, tzinfo=TZ),
        datetime(2026, 9, 30, 23, 59, 59, 999999, tzinfo=TZ),
    ),
    (
        datetime(2026, 12, 20, 8, 0, tzinfo=UTC),
        datetime(2026, 12, 1, tzinfo=TZ),
        datetime(2026, 12, 31, 23, 59, 59, 999999, tzinfo=TZ),
    ),
    (
        datetime(2027, 1, 5, 0, 0, tzinfo=UTC),
        datetime(2027, 1, 1, tzinfo=TZ),
        datetime(2027, 1, 31, 23, 59, 59, 999999, tzinfo=TZ),
    ),
    (
        datetime(2028, 2, 10, 0, 0, tzinfo=UTC),
        datetime(2028, 2, 1, tzinfo=TZ),
        datetime(2028, 2, 29, 23, 59, 59, 999999, tzinfo=TZ),
    ),
]


@pytest.mark.parametrize(("moment", "expected_start", "expected_end"), MONTH_BOUNDARY_CASES)
def test_month_start_and_end_span_expected_month(
    moment: datetime, expected_start: datetime, expected_end: datetime
) -> None:
    assert month_start(moment) == expected_start
    assert month_end(moment) == expected_end
