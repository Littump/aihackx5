from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from psycopg import AsyncConnection
from psycopg.types.json import Jsonb

from app.core.clock import month_end, month_start
from tests.factories import make_challenge, make_user

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
MARGIN = 90.0
MICROSECOND = timedelta(microseconds=1)
CHALLENGE_ECONOMICS = Jsonb(
    {
        "avg_basket": 600.0,
        "expected_incremental_purchases": 1.0,
        "expected_incremental_margin": MARGIN,
        "max_reward_rub": 36.0,
        "contribution_margin": 0.15,
        "reward_share_max": 0.4,
    }
)

MONTH_START = month_start(NOW)
MONTH_END = month_end(NOW)
MONTH_BOUNDARY_CASES: list[tuple[datetime, bool]] = [
    (MONTH_START, True),
    (MONTH_END, True),
    (MONTH_START - MICROSECOND, False),
    (MONTH_END + MICROSECOND, False),
]


@pytest.mark.parametrize(("period_start", "included"), MONTH_BOUNDARY_CASES)
async def test_expected_margin_month_respects_calendar_month_boundary(
    client: AsyncClient,
    conn: AsyncConnection,
    freeze_time: Callable[[datetime], None],
    period_start: datetime,
    included: bool,
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    await make_challenge(
        conn,
        user.id,
        status="active",
        period_start=period_start,
        economics=CHALLENGE_ECONOMICS,
    )

    response = await client.get(f"/api/v1/pm/users/{user.id}")

    assert response.status_code == 200
    expected = MARGIN if included else 0
    assert response.json()["expected_incremental_margin_month"] == expected


async def test_expected_margin_month_excludes_previous_month_challenge(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    await make_challenge(
        conn,
        user.id,
        status="completed",
        period_start=NOW.replace(month=8, day=10),
        economics=CHALLENGE_ECONOMICS,
    )
    await make_challenge(
        conn,
        user.id,
        status="active",
        is_hero=False,
        period_start=NOW,
        economics=Jsonb(
            {
                "avg_basket": 600.0,
                "expected_incremental_purchases": 1.0,
                "expected_incremental_margin": 45.0,
                "max_reward_rub": 18.0,
                "contribution_margin": 0.15,
                "reward_share_max": 0.4,
            }
        ),
    )

    response = await client.get(f"/api/v1/pm/users/{user.id}")

    assert response.status_code == 200
    assert response.json()["expected_incremental_margin_month"] == 45.0
