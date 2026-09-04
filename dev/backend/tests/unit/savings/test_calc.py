from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from app.features.savings import calc
from app.features.savings.models import SavingsCategory, SavingsPeriodRange
from app.game_rules import TIMEZONE
from tests.unit.savings.data import (
    AC_RECEIPT,
    EXPECTED_AC_SAVINGS,
    EXPECTED_SAME_CATEGORY_TOTAL,
    EXPECTED_TIE_CATEGORY_ORDER,
    EXPECTED_TOP_CATEGORIES,
    EXPECTED_TWO_RECEIPTS_SAVINGS,
    EXPECTED_ZERO_DISCOUNT_SAVINGS,
    FOUR_CATEGORY_RECEIPT,
    SAME_CATEGORY_ACROSS_RECEIPTS,
    TIE_CATEGORY_RECEIPT,
    TWO_RECEIPTS,
    WEEK_BOUNDARY_CASES,
    ZERO_DISCOUNT_WITH_POINTS_RECEIPT,
)

TZ = ZoneInfo(TIMEZONE)

MONTH_CASES = [
    (
        datetime(2026, 9, 15, 10, 0, tzinfo=TZ),
        datetime(2026, 9, 1, 0, 0, tzinfo=TZ),
        datetime(2026, 10, 1, 0, 0, tzinfo=TZ),
        datetime(2026, 8, 1, 0, 0, tzinfo=TZ),
        datetime(2026, 9, 1, 0, 0, tzinfo=TZ),
    ),
    (
        datetime(2026, 1, 10, 10, 0, tzinfo=TZ),
        datetime(2026, 1, 1, 0, 0, tzinfo=TZ),
        datetime(2026, 2, 1, 0, 0, tzinfo=TZ),
        datetime(2025, 12, 1, 0, 0, tzinfo=TZ),
        datetime(2026, 1, 1, 0, 0, tzinfo=TZ),
    ),
]


def test_receipt_savings_matches_ac_example() -> None:
    assert calc.receipt_savings(AC_RECEIPT) == EXPECTED_AC_SAVINGS


def test_total_savings_sums_receipts() -> None:
    assert calc.total_savings(TWO_RECEIPTS) == EXPECTED_TWO_RECEIPTS_SAVINGS


def test_total_savings_is_zero_without_receipts() -> None:
    assert calc.total_savings([]) == Decimal("0")


@pytest.mark.parametrize(("moment", "start", "end", "previous_start", "previous_end"), MONTH_CASES)
def test_month_range_matches_calendar_month(
    moment: datetime,
    start: datetime,
    end: datetime,
    previous_start: datetime,
    previous_end: datetime,
) -> None:
    result = calc.period_range("month", moment)
    assert (result.start, result.end) == (start, end)
    assert (result.previous_start, result.previous_end) == (previous_start, previous_end)


def test_week_range_is_last_seven_days_sliding_window() -> None:
    moment = datetime(2026, 9, 15, 10, 0, tzinfo=TZ)

    result = calc.period_range("week", moment)

    assert result.start == datetime(2026, 9, 9, 0, 0, tzinfo=TZ)
    assert result.end == datetime(2026, 9, 16, 0, 0, tzinfo=TZ)
    assert result.previous_start == datetime(2026, 9, 2, 0, 0, tzinfo=TZ)
    assert result.previous_end == datetime(2026, 9, 9, 0, 0, tzinfo=TZ)


def test_top_categories_sorted_and_capped_at_three() -> None:
    result = calc.top_categories([FOUR_CATEGORY_RECEIPT])
    assert [(c.category, c.amount) for c in result] == EXPECTED_TOP_CATEGORIES


def test_top_categories_empty_without_items() -> None:
    assert calc.top_categories([]) == []


def test_receipt_savings_with_zero_discount_counts_points_only() -> None:
    result = calc.receipt_savings(ZERO_DISCOUNT_WITH_POINTS_RECEIPT)
    assert result == EXPECTED_ZERO_DISCOUNT_SAVINGS


def test_top_categories_tie_break_preserves_item_order() -> None:
    result = calc.top_categories([TIE_CATEGORY_RECEIPT])
    assert [c.category for c in result] == EXPECTED_TIE_CATEGORY_ORDER


def test_top_categories_aggregates_same_category_across_receipts() -> None:
    result = calc.top_categories(SAME_CATEGORY_ACROSS_RECEIPTS)
    assert result == [
        SavingsCategory(
            category="dairy",
            amount=EXPECTED_SAME_CATEGORY_TOTAL,
            items_count=2,
            top_products=["товар"],
        )
    ]


def _bucket(range_: SavingsPeriodRange, moment: datetime) -> str:
    if range_.start <= moment < range_.end:
        return "current"
    if range_.previous_start <= moment < range_.previous_end:
        return "previous"
    return "none"


@pytest.mark.parametrize(("days_ago", "expected_bucket"), WEEK_BOUNDARY_CASES)
def test_week_range_boundaries_classify_receipt_correctly(
    days_ago: int, expected_bucket: str
) -> None:
    moment = datetime(2026, 9, 15, 10, 0, tzinfo=TZ)
    receipt_time = moment - timedelta(days=days_ago)

    range_ = calc.period_range("week", moment)

    assert _bucket(range_, receipt_time) == expected_bucket
