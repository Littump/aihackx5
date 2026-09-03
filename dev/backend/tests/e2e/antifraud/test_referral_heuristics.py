from collections.abc import Callable
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from psycopg import AsyncConnection

from app.features.antifraud import service as antifraud_service
from tests.e2e.antifraud.data import NOW, REFERRER_CREATED_AT
from tests.factories import make_receipt, make_referral, make_user


def _single_purchase_item(amount: str) -> list[dict[str, object]]:
    return [
        {
            "product_name": "Товар",
            "category": "grocery",
            "qty": Decimal("1"),
            "regular_price": Decimal(amount),
            "paid_price": Decimal(amount),
        }
    ]


NO_SHARED_DEVICE_CASES: list[tuple[str | None, str | None]] = [
    (None, None),
    ("device-a", "device-b"),
]


@pytest.mark.parametrize(("referrer_fp", "referee_fp"), NO_SHARED_DEVICE_CASES)
async def test_shared_device_does_not_fire_without_a_real_match(
    conn: AsyncConnection,
    freeze_time: Callable[[datetime], None],
    referrer_fp: str | None,
    referee_fp: str | None,
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn, device_fingerprint=referrer_fp, created_at=REFERRER_CREATED_AT)
    referee = await make_user(conn, device_fingerprint=referee_fp, created_at=NOW)
    referral = await make_referral(conn, referrer.id, referee.id, created_at=NOW)

    decision = await antifraud_service.check_referral(conn, referral.id)

    codes = {s.code for s in decision.signals}
    assert "shared_device" not in codes
    assert decision.decision == "approve"


async def test_instant_signup_fires_when_referee_created_within_ten_minutes(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn, created_at=NOW - timedelta(minutes=5))
    referee = await make_user(conn, created_at=NOW)
    referral = await make_referral(conn, referrer.id, referee.id, created_at=NOW)

    decision = await antifraud_service.check_referral(conn, referral.id)

    codes = {s.code for s in decision.signals}
    assert "instant_signup" in codes


async def test_referral_ring_fires_when_referee_invited_the_referrer_back(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user_a = await make_user(conn, created_at=REFERRER_CREATED_AT)
    user_b = await make_user(conn, created_at=REFERRER_CREATED_AT)
    referral_ab = await make_referral(conn, user_a.id, user_b.id, created_at=NOW)
    await make_referral(conn, user_b.id, user_a.id, created_at=NOW - timedelta(days=1))

    decision = await antifraud_service.check_referral(conn, referral_ab.id)

    codes = {s.code for s in decision.signals}
    assert "referral_ring" in codes


async def test_min_purchase_pattern_fires_when_all_invitees_bought_once_in_range(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn, created_at=REFERRER_CREATED_AT)
    checked_referral_id = None
    for i, amount in enumerate(("500", "525", "550")):
        invitee = await make_user(conn, created_at=REFERRER_CREATED_AT)
        r = await make_referral(
            conn, referrer.id, invitee.id, created_at=REFERRER_CREATED_AT + timedelta(hours=i)
        )
        await make_receipt(conn, invitee.id, items=_single_purchase_item(amount), purchased_at=NOW)
        checked_referral_id = r.id
    assert checked_referral_id is not None

    decision = await antifraud_service.check_referral(conn, checked_referral_id)

    codes = {s.code for s in decision.signals}
    assert "min_purchase_pattern" in codes


async def test_min_purchase_pattern_does_not_fire_when_one_invitee_has_no_purchase(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn, created_at=REFERRER_CREATED_AT)
    for i, amount in enumerate(("500", "525")):
        invitee = await make_user(conn, created_at=REFERRER_CREATED_AT)
        await make_referral(
            conn, referrer.id, invitee.id, created_at=REFERRER_CREATED_AT + timedelta(hours=i)
        )
        await make_receipt(conn, invitee.id, items=_single_purchase_item(amount), purchased_at=NOW)
    invitee_without_purchase = await make_user(conn, created_at=REFERRER_CREATED_AT)
    referral = await make_referral(
        conn,
        referrer.id,
        invitee_without_purchase.id,
        created_at=REFERRER_CREATED_AT + timedelta(hours=2),
    )

    decision = await antifraud_service.check_referral(conn, referral.id)

    codes = {s.code for s in decision.signals}
    assert "min_purchase_pattern" not in codes


async def test_same_store_zero_activity_fires_at_exact_14_day_boundary(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn, created_at=REFERRER_CREATED_AT)
    referee = await make_user(conn, created_at=REFERRER_CREATED_AT)
    second_purchase_at = NOW - timedelta(days=14)
    referral = await make_referral(
        conn,
        referrer.id,
        referee.id,
        created_at=REFERRER_CREATED_AT,
        second_purchase_at=second_purchase_at,
    )

    decision = await antifraud_service.check_referral(conn, referral.id)

    codes = {s.code for s in decision.signals}
    assert "same_store_zero_activity" in codes


async def test_same_store_zero_activity_does_not_fire_when_receipt_exists_after(
    conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn, created_at=REFERRER_CREATED_AT)
    referee = await make_user(conn, created_at=REFERRER_CREATED_AT)
    second_purchase_at = NOW - timedelta(days=20)
    referral = await make_referral(
        conn,
        referrer.id,
        referee.id,
        created_at=REFERRER_CREATED_AT,
        second_purchase_at=second_purchase_at,
    )
    await make_receipt(conn, referee.id, purchased_at=second_purchase_at + timedelta(days=1))

    decision = await antifraud_service.check_referral(conn, referral.id)

    codes = {s.code for s in decision.signals}
    assert "same_store_zero_activity" not in codes
