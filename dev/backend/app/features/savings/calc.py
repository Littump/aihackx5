from datetime import datetime, timedelta
from decimal import Decimal
from typing import Literal
from zoneinfo import ZoneInfo

from app.core.clock import day_start
from app.features.receipts.models import ReceiptWithItems
from app.features.savings.models import ReceiptSavingsLike, SavingsCategory, SavingsPeriodRange
from app.game_rules import SAVINGS_TOP_CATEGORIES_LIMIT, SAVINGS_WEEK_WINDOW_DAYS, TIMEZONE

MONEY_PRECISION = Decimal("0.01")
TZ = ZoneInfo(TIMEZONE)


def period_range(period: Literal["week", "month"], moment: datetime) -> SavingsPeriodRange:
    if period == "week":
        return _week_range(moment)
    return _month_range(moment)


def receipt_savings(receipt: ReceiptSavingsLike) -> Decimal:
    return (
        (receipt.regular_total - receipt.paid_total) + receipt.points_earned + receipt.points_spent
    )


def total_savings(receipts: list[ReceiptWithItems]) -> Decimal:
    return sum((receipt_savings(r) for r in receipts), Decimal("0"))


def total_discount(receipts: list[ReceiptWithItems]) -> Decimal:
    return sum((r.regular_total - r.paid_total for r in receipts), Decimal("0"))


def total_points_earned(receipts: list[ReceiptWithItems]) -> int:
    return sum(r.points_earned for r in receipts)


def total_points_spent(receipts: list[ReceiptWithItems]) -> int:
    return sum(r.points_spent for r in receipts)


def top_categories(receipts: list[ReceiptWithItems]) -> list[SavingsCategory]:
    totals: dict[str, Decimal] = {}
    for receipt in receipts:
        for item in receipt.items:
            contribution = (item.regular_price - item.paid_price) * item.qty
            totals[item.category] = totals.get(item.category, Decimal("0")) + contribution
    ranked = sorted(totals.items(), key=lambda pair: pair[1], reverse=True)
    return [
        SavingsCategory(category=category, amount=amount.quantize(MONEY_PRECISION))
        for category, amount in ranked[:SAVINGS_TOP_CATEGORIES_LIMIT]
    ]


def _week_range(moment: datetime) -> SavingsPeriodRange:
    end = day_start(moment) + timedelta(days=1)
    start = end - timedelta(days=SAVINGS_WEEK_WINDOW_DAYS)
    previous_end = start
    previous_start = previous_end - timedelta(days=SAVINGS_WEEK_WINDOW_DAYS)
    return SavingsPeriodRange(
        start=start, end=end, previous_start=previous_start, previous_end=previous_end
    )


def _month_range(moment: datetime) -> SavingsPeriodRange:
    local = moment.astimezone(TZ)
    start = datetime(local.year, local.month, 1, tzinfo=TZ)
    end = _next_month_start(start)
    previous_end = start
    previous_start = _previous_month_start(start)
    return SavingsPeriodRange(
        start=start, end=end, previous_start=previous_start, previous_end=previous_end
    )


def _next_month_start(month_start: datetime) -> datetime:
    if month_start.month == 12:
        return datetime(month_start.year + 1, 1, 1, tzinfo=TZ)
    return datetime(month_start.year, month_start.month + 1, 1, tzinfo=TZ)


def _previous_month_start(month_start: datetime) -> datetime:
    if month_start.month == 1:
        return datetime(month_start.year - 1, 12, 1, tzinfo=TZ)
    return datetime(month_start.year, month_start.month - 1, 1, tzinfo=TZ)
