from datetime import timedelta
from decimal import Decimal

import pytest

from app.features.antifraud import service as antifraud_service
from app.features.antifraud.models import FraudDecision
from app.features.challenges import service as challenges_service
from app.features.domovoy import service as domovoy_service
from app.features.referrals import database, service
from app.features.referrals.models import ReferralRow
from tests.unit.referrals.data import PURCHASED_AT, make_receipt_detail, make_referral_row

FIRST_PURCHASE_BOUNDARY_CASES: list[tuple[Decimal, bool]] = [
    (Decimal("499.99"), False),
    (Decimal("500.01"), True),
]


@pytest.mark.parametrize("paid_total, should_qualify", FIRST_PURCHASE_BOUNDARY_CASES)
async def test_on_receipt_first_purchase_amount_boundary(
    monkeypatch: pytest.MonkeyPatch, paid_total: Decimal, should_qualify: bool
) -> None:
    referral = make_referral_row(status="pending")
    marked = {"called": False}

    async def fake_get(_: object, *, referee_user_id: int) -> ReferralRow:
        return referral

    async def fake_mark_first_purchase(_: object, **kwargs: object) -> ReferralRow:
        marked["called"] = True
        return make_referral_row(status="first_purchase")

    async def fake_record_reward(_: object, **kwargs: object) -> None:
        return None

    monkeypatch.setattr(database, "get_referral_by_referee", fake_get)
    monkeypatch.setattr(database, "mark_first_purchase", fake_mark_first_purchase)
    monkeypatch.setattr(challenges_service, "record_reward", fake_record_reward)

    delta = await service.on_receipt(
        None,  # type: ignore[arg-type]
        20,
        make_receipt_detail(paid_total=paid_total),
    )

    assert marked["called"] is should_qualify
    assert (delta is not None) is should_qualify


SECOND_PURCHASE_TIMING_CASES: list[tuple[timedelta, bool]] = [
    (timedelta(days=6, hours=23, minutes=59), False),
    (timedelta(days=7, minutes=1), True),
]


@pytest.mark.parametrize("gap, should_qualify", SECOND_PURCHASE_TIMING_CASES)
async def test_on_receipt_second_purchase_timing_boundary(
    monkeypatch: pytest.MonkeyPatch, gap: timedelta, should_qualify: bool
) -> None:
    first_purchase_at = PURCHASED_AT - gap
    referral = make_referral_row(status="first_purchase", first_purchase_at=first_purchase_at)
    marked = {"called": False}

    async def fake_get(_: object, *, referee_user_id: int) -> ReferralRow:
        return referral

    async def fake_mark_qualified(_: object, **kwargs: object) -> ReferralRow:
        marked["called"] = True
        return make_referral_row(status="qualified", first_purchase_at=first_purchase_at)

    async def fake_check_referral(_: object, referral_id: int) -> FraudDecision:
        return FraudDecision(score=0.0, decision="approve", signals=[])

    async def fake_count_rewarded_in_range(*args: object, **kwargs: object) -> int:
        return 0

    async def fake_mark_decision(_: object, **kwargs: object) -> ReferralRow:
        return make_referral_row(status="rewarded")

    async def fake_add_xp(_: object, user_id: int, xp: int, **kwargs: object) -> None:
        return None

    monkeypatch.setattr(database, "get_referral_by_referee", fake_get)
    monkeypatch.setattr(database, "mark_qualified", fake_mark_qualified)
    monkeypatch.setattr(antifraud_service, "check_referral", fake_check_referral)
    monkeypatch.setattr(database, "count_rewarded_in_range", fake_count_rewarded_in_range)
    monkeypatch.setattr(database, "mark_decision", fake_mark_decision)
    monkeypatch.setattr(domovoy_service, "add_xp", fake_add_xp)

    delta = await service.on_receipt(
        None,  # type: ignore[arg-type]
        20,
        make_receipt_detail(purchased_at=PURCHASED_AT),
    )

    assert marked["called"] is should_qualify
    assert (delta is not None) is should_qualify
