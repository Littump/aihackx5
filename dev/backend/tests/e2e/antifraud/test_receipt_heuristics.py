from collections.abc import Callable
from datetime import datetime, timedelta
from decimal import Decimal

from psycopg import AsyncConnection

from app.features.antifraud import service as antifraud_service
from app.features.challenges import database as challenges_db
from tests.e2e.antifraud.data import NOW
from tests.factories import make_challenge, make_receipt, make_user, make_user_features


async def _complete_challenge(conn: AsyncConnection, user_id: int, completed_at: datetime) -> None:
    challenge = await make_challenge(conn, user_id, status="completed")
    await challenges_db.update_progress(
        conn,
        challenge_id=challenge.id,
        progress=challenge.target,
        status="completed",
        completed_at=completed_at,
    )


async def test_return_after_reward_is_deterministic_with_two_challenges_same_day(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    purchase_day = NOW - timedelta(days=2)
    await _complete_challenge(conn, user.id, purchase_day.replace(hour=8))
    await _complete_challenge(conn, user.id, purchase_day.replace(hour=20))
    receipt = await make_receipt(
        conn,
        user.id,
        purchased_at=purchase_day.replace(hour=10),
        is_returned=True,
        returned_at=NOW,
    )

    decision = await antifraud_service.check_receipt(conn, user.id, receipt)

    return_signals = [s for s in decision.signals if s.code == "return_after_reward"]
    assert len(return_signals) == 1
    assert "2 дн." in return_signals[0].detail


async def test_return_after_reward_fires_for_unrelated_receipt_on_completion_day(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    completion_day = NOW - timedelta(days=1)
    await _complete_challenge(conn, user.id, completion_day.replace(hour=18))
    unrelated_receipt = await make_receipt(
        conn,
        user.id,
        purchased_at=completion_day.replace(hour=9),
        is_returned=True,
        returned_at=NOW,
    )

    decision = await antifraud_service.check_receipt(conn, user.id, unrelated_receipt)

    # эвристика вяжет по календарному дню, а не по id чека — известное ограничение схемы
    assert any(s.code == "return_after_reward" for s in decision.signals)


async def test_basket_monotony_fires_for_three_identical_consecutive_receipts(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    receipt = None
    for hours_ago in (6, 3, 0):
        receipt = await make_receipt(conn, user.id, purchased_at=NOW - timedelta(hours=hours_ago))
    assert receipt is not None

    decision = await antifraud_service.check_receipt(conn, user.id, receipt)

    codes = {s.code for s in decision.signals}
    assert "basket_monotony" in codes


async def test_basket_monotony_does_not_fire_when_basket_composition_changes(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    await make_receipt(conn, user.id, purchased_at=NOW - timedelta(hours=6))
    different_items = [
        {
            "product_name": "Пиво",
            "category": "alcohol",
            "qty": Decimal("1"),
            "regular_price": Decimal("199.00"),
            "paid_price": Decimal("199.00"),
        }
    ]
    await make_receipt(conn, user.id, purchased_at=NOW - timedelta(hours=3), items=different_items)
    receipt = await make_receipt(conn, user.id, purchased_at=NOW)

    decision = await antifraud_service.check_receipt(conn, user.id, receipt)

    codes = {s.code for s in decision.signals}
    assert "basket_monotony" not in codes


async def test_frequency_spike_fires_at_exact_boundary_with_real_receipt_history(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    await make_user_features(conn, user.id, frequency_per_week=Decimal("1"))
    receipt = None
    for days_ago in (3, 2, 1, 0):
        receipt = await make_receipt(conn, user.id, purchased_at=NOW - timedelta(days=days_ago))
    assert receipt is not None

    decision = await antifraud_service.check_receipt(conn, user.id, receipt)

    codes = {s.code for s in decision.signals}
    assert "frequency_spike" in codes
    signal = next(s for s in decision.signals if s.code == "frequency_spike")
    assert "4 чеков за 7 дней" in signal.detail


async def test_frequency_spike_does_not_fire_just_below_boundary(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    await make_user_features(conn, user.id, frequency_per_week=Decimal("1"))
    receipt = None
    for days_ago in (2, 1, 0):
        receipt = await make_receipt(conn, user.id, purchased_at=NOW - timedelta(days=days_ago))
    assert receipt is not None

    decision = await antifraud_service.check_receipt(conn, user.id, receipt)

    codes = {s.code for s in decision.signals}
    assert "frequency_spike" not in codes
