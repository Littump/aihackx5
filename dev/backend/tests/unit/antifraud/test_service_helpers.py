from datetime import timedelta
from decimal import Decimal

import pytest

from app.features.antifraud import service as antifraud_service
from tests.unit.antifraud.service_helpers_data import (
    ANCHOR,
    receipt_detail,
    receipt_row,
    receipt_row_with_pos,
    referral_row,
)

TOLERANCE_CASES: list[tuple[str, str, bool]] = [
    ("100", "105", True),
    ("100", "95", True),
    ("100", "105.01", False),
    ("100", "94.99", False),
    ("0", "0", True),
    ("0", "1", False),
]


@pytest.mark.parametrize(("anchor", "amount", "expected"), TOLERANCE_CASES)
def test_within_tolerance_boundary(anchor: str, amount: str, expected: bool) -> None:
    result = antifraud_service._within_tolerance(Decimal(amount), Decimal(anchor))
    assert result is expected


SINGLE_PURCHASE_CASES: list[tuple[list[Decimal], bool]] = [
    ([Decimal("500")], True),
    ([Decimal("550")], True),
    ([Decimal("499.99")], False),
    ([Decimal("550.01")], False),
    ([Decimal("500"), Decimal("500")], False),
    ([], False),
]


@pytest.mark.parametrize(("amounts", "expected"), SINGLE_PURCHASE_CASES)
def test_is_single_matching_purchase_boundary(amounts: list[Decimal], expected: bool) -> None:
    receipts = [receipt_detail(id=i, paid_total=a) for i, a in enumerate(amounts)]
    assert antifraud_service._is_single_matching_purchase(receipts) is expected


def test_minutes_since_rounds_down_to_whole_minutes() -> None:
    assert antifraud_service._minutes_since(ANCHOR, ANCHOR + timedelta(minutes=15)) == 15
    assert antifraud_service._minutes_since(ANCHOR, ANCHOR + timedelta(seconds=59)) == 0


def test_count_invite_burst_boundary_inclusive_at_60_minutes_lookback_only() -> None:
    invitees = [
        referral_row(id=1, created_at=ANCHOR - timedelta(minutes=60)),
        referral_row(id=2, created_at=ANCHOR - timedelta(minutes=61)),
        referral_row(id=3, created_at=ANCHOR),
        referral_row(id=4, created_at=ANCHOR + timedelta(minutes=1)),
    ]
    assert antifraud_service._count_invite_burst(invitees, ANCHOR) == 2


def test_count_invite_burst_is_lookback_only_not_symmetric() -> None:
    invitees = [
        referral_row(id=1, created_at=ANCHOR - timedelta(minutes=55)),
        referral_row(id=2, created_at=ANCHOR + timedelta(minutes=55)),
    ]
    assert antifraud_service._count_invite_burst(invitees, ANCHOR) == 1


def test_is_referral_ring_direct_reverse_invite() -> None:
    referee_invitees = [referral_row(id=2, referee_user_id=1, created_at=ANCHOR)]
    assert antifraud_service._is_referral_ring(referee_invitees, 1, []) is True


def test_is_referral_ring_via_shared_invitee() -> None:
    referrer_invitees = [referral_row(id=2, referee_user_id=99, created_at=ANCHOR)]
    referee_invitees = [referral_row(id=3, referee_user_id=99, created_at=ANCHOR)]
    assert antifraud_service._is_referral_ring(referee_invitees, 1, referrer_invitees) is True


def test_is_referral_ring_false_without_overlap() -> None:
    referrer_invitees = [referral_row(id=2, referee_user_id=10, created_at=ANCHOR)]
    referee_invitees = [referral_row(id=3, referee_user_id=20, created_at=ANCHOR)]
    assert antifraud_service._is_referral_ring(referee_invitees, 1, referrer_invitees) is False


def test_is_referral_ring_false_when_referee_invited_nobody() -> None:
    assert antifraud_service._is_referral_ring([], 1, []) is False


def test_consecutive_matching_baskets_counts_full_matching_streak() -> None:
    receipts = [receipt_detail(id=i, paid_total=Decimal("100")) for i in range(3)]
    assert antifraud_service._consecutive_matching_baskets(receipts, target_id=0) == 3


def test_consecutive_matching_baskets_breaks_on_category_change() -> None:
    receipts = [
        receipt_detail(id=0, paid_total=Decimal("100"), categories=("dairy",)),
        receipt_detail(id=1, paid_total=Decimal("100"), categories=("dairy",)),
        receipt_detail(id=2, paid_total=Decimal("100"), categories=("bakery",)),
    ]
    assert antifraud_service._consecutive_matching_baskets(receipts, target_id=0) == 2


def test_consecutive_matching_baskets_breaks_on_amount_outside_tolerance() -> None:
    receipts = [
        receipt_detail(id=0, paid_total=Decimal("100")),
        receipt_detail(id=1, paid_total=Decimal("100")),
        receipt_detail(id=2, paid_total=Decimal("200")),
    ]
    assert antifraud_service._consecutive_matching_baskets(receipts, target_id=0) == 2


def test_consecutive_matching_baskets_returns_zero_when_target_missing() -> None:
    receipts = [receipt_detail(id=0, paid_total=Decimal("100"))]
    assert antifraud_service._consecutive_matching_baskets(receipts, target_id=99) == 0


def test_count_in_window_boundary_inclusive_at_60_minutes_same_store() -> None:
    receipts = [
        receipt_row(id=1, store_id=1, purchased_at=ANCHOR - timedelta(minutes=60)),
        receipt_row(id=2, store_id=1, purchased_at=ANCHOR - timedelta(minutes=61)),
        receipt_row(id=3, store_id=2, purchased_at=ANCHOR),
        receipt_row(id=4, store_id=1, purchased_at=ANCHOR),
    ]
    count = antifraud_service._count_in_window(
        receipts, store_id=1, anchor=ANCHOR, window=timedelta(minutes=60)
    )
    assert count == 2


def test_count_same_day_boundary_inclusive_at_day_edges() -> None:
    from app.core.clock import day_end, day_start

    receipts = [
        receipt_row(id=1, purchased_at=day_start(ANCHOR)),
        receipt_row(id=2, purchased_at=day_end(ANCHOR)),
        receipt_row(id=3, purchased_at=day_end(ANCHOR) + timedelta(microseconds=1)),
    ]
    assert antifraud_service._count_same_day(receipts, ANCHOR) == 2


def test_pos_share_computes_top_pos_ratio_over_receipts_with_pos_only() -> None:
    receipts = [
        receipt_row_with_pos(id=1, pos_id="A"),
        receipt_row_with_pos(id=2, pos_id="A"),
        receipt_row_with_pos(id=3, pos_id="A"),
        receipt_row_with_pos(id=4, pos_id="B"),
        receipt_row_with_pos(id=5, pos_id=None),
    ]
    share, sample = antifraud_service._pos_share(receipts)
    assert sample == 4
    assert share == Decimal("3") / Decimal("4")


def test_pos_share_returns_zero_when_no_pos_ids() -> None:
    receipts = [receipt_row_with_pos(id=1, pos_id=None)]
    assert antifraud_service._pos_share(receipts) == (Decimal("0"), 0)
