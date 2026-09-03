from datetime import timedelta
from decimal import Decimal

import pytest

from app.features.antifraud import service as antifraud_service
from app.features.antifraud.models import FraudDecision
from app.features.challenges import service as challenges_service
from app.features.domovoy import service as domovoy_service
from app.features.referrals import database, service
from app.features.referrals.models import ReferralRow
from app.game_rules import REFERRAL_SECOND_PURCHASE_MIN_DAYS
from tests.unit.referrals.data import PURCHASED_AT, make_receipt_detail, make_referral_row


async def test_on_receipt_not_counted_is_a_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fail_lookup(*args: object, **kwargs: object) -> ReferralRow | None:
        raise AssertionError("must not query referrals for a not counted receipt")

    monkeypatch.setattr(database, "get_referral_by_referee", fail_lookup)

    delta = await service.on_receipt(
        None,  # type: ignore[arg-type]
        20,
        make_receipt_detail(counted=False),
    )

    assert delta is None


async def test_on_receipt_below_threshold_first_purchase_is_a_noop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    referral = make_referral_row(status="pending")

    async def fake_get(_: object, *, referee_user_id: int) -> ReferralRow:
        return referral

    async def fail_mark(*args: object, **kwargs: object) -> ReferralRow:
        raise AssertionError("must not mark first purchase below the threshold")

    monkeypatch.setattr(database, "get_referral_by_referee", fake_get)
    monkeypatch.setattr(database, "mark_first_purchase", fail_mark)

    delta = await service.on_receipt(
        None,  # type: ignore[arg-type]
        20,
        make_receipt_detail(paid_total=Decimal("450")),
    )

    assert delta is None


async def test_on_receipt_first_purchase_rewards_referee(monkeypatch: pytest.MonkeyPatch) -> None:
    referral = make_referral_row(status="pending")
    updated = make_referral_row(status="first_purchase", first_purchase_at=PURCHASED_AT)
    recorded: list[dict[str, object]] = []

    async def fake_get(_: object, *, referee_user_id: int) -> ReferralRow:
        return referral

    async def fake_mark_first_purchase(_: object, **kwargs: object) -> ReferralRow:
        return updated

    async def fake_record_reward(_: object, **kwargs: object) -> None:
        recorded.append(kwargs)

    monkeypatch.setattr(database, "get_referral_by_referee", fake_get)
    monkeypatch.setattr(database, "mark_first_purchase", fake_mark_first_purchase)
    monkeypatch.setattr(challenges_service, "record_reward", fake_record_reward)

    delta = await service.on_receipt(
        None,  # type: ignore[arg-type]
        20,
        make_receipt_detail(paid_total=Decimal("600")),
    )

    assert delta is not None
    assert delta.status == "first_purchase"
    assert recorded == [
        {
            "user_id": 20,
            "kind": "referral",
            "xp_delta": 0,
            "points_delta": 200,
            "ref_type": "referral",
            "ref_id": 1,
        }
    ]


async def test_on_receipt_second_purchase_approved_rewards_referrer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_purchase_at = PURCHASED_AT - timedelta(days=REFERRAL_SECOND_PURCHASE_MIN_DAYS)
    referral = make_referral_row(status="first_purchase", first_purchase_at=first_purchase_at)
    qualified = make_referral_row(status="qualified", first_purchase_at=first_purchase_at)
    rewarded = make_referral_row(status="rewarded", referrer_reward_points=150)
    add_xp_calls: list[dict[str, object]] = []

    async def fake_get(_: object, *, referee_user_id: int) -> ReferralRow:
        return referral

    async def fake_mark_qualified(_: object, **kwargs: object) -> ReferralRow:
        return qualified

    async def fake_check_referral(_: object, referral_id: int) -> FraudDecision:
        return FraudDecision(score=0.0, decision="approve", signals=[])

    async def fake_count_rewarded_in_range(*args: object, **kwargs: object) -> int:
        return 0

    async def fake_mark_decision(_: object, **kwargs: object) -> ReferralRow:
        return rewarded

    async def fake_add_xp(_: object, user_id: int, xp: int, **kwargs: object) -> None:
        add_xp_calls.append({"user_id": user_id, "xp": xp, **kwargs})

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

    assert delta is not None
    assert delta.status == "rewarded"
    assert add_xp_calls == [
        {
            "user_id": 10,
            "xp": 100,
            "kind": "referral",
            "ref_type": "referral",
            "ref_id": 1,
            "points_delta": 150,
        }
    ]
