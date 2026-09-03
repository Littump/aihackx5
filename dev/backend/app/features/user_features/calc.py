from datetime import datetime
from decimal import Decimal
from itertools import pairwise
from zoneinfo import ZoneInfo

from app.features.receipts.models import ReceiptWithItems
from app.features.user_features.models import CategoryAffinity, UserFeaturesCalc
from app.features.users.models import StoreRow
from app.game_rules import TIMEZONE, USER_FEATURES_RECENCY_NO_HISTORY_DAYS

FREQUENCY_PRECISION = Decimal("0.001")
MONEY_PRECISION = Decimal("0.01")
SHARE_PRECISION = Decimal("0.001")
CADENCE_PRECISION = Decimal("0.01")
WEEKDAYS_COUNT = 7
TZ = ZoneInfo(TIMEZONE)


def compute_frequency_per_week(receipts: list[ReceiptWithItems], *, window_weeks: int) -> Decimal:
    raw = Decimal(len(receipts)) / Decimal(window_weeks)
    return raw.quantize(FREQUENCY_PRECISION)


def compute_recency_days(receipts: list[ReceiptWithItems], *, now: datetime) -> int:
    if not receipts:
        return USER_FEATURES_RECENCY_NO_HISTORY_DAYS
    last = max(r.purchased_at for r in receipts)
    return max((now - last).days, 0)


def compute_avg_basket(receipts: list[ReceiptWithItems]) -> Decimal:
    if not receipts:
        return Decimal("0")
    total = sum((r.paid_total for r in receipts), Decimal("0"))
    return (total / Decimal(len(receipts))).quantize(MONEY_PRECISION)


def compute_promo_sensitivity(receipts: list[ReceiptWithItems]) -> Decimal:
    promo_sum, total_sum = _promo_and_total_sums(receipts)
    if total_sum == 0:
        return Decimal("0")
    return (promo_sum / total_sum).quantize(SHARE_PRECISION)


def compute_cadence_days(receipts: list[ReceiptWithItems]) -> Decimal | None:
    if len(receipts) < 2:
        return None
    moments = sorted(r.purchased_at for r in receipts)
    avg = _average_interval_days(moments)
    return Decimal(str(avg)).quantize(CADENCE_PRECISION)


def compute_category_affinity(receipts: list[ReceiptWithItems]) -> dict[str, CategoryAffinity]:
    totals_by_category, total_all = _category_totals(receipts)
    moments_by_category = _category_visit_moments(receipts)
    result: dict[str, CategoryAffinity] = {}
    for category, moments in moments_by_category.items():
        share = float(totals_by_category[category] / total_all) if total_all else 0.0
        cadence = _average_interval_days(sorted(moments)) if len(moments) >= 2 else 0.0
        result[category] = CategoryAffinity(share=share, visits=len(moments), cadence_days=cadence)
    return result


def compute_favourite_store_id(receipts: list[ReceiptWithItems]) -> int | None:
    if not receipts:
        return None
    counts: dict[int, int] = {}
    for receipt in receipts:
        counts[receipt.store_id] = counts.get(receipt.store_id, 0) + 1
    max_count = max(counts.values())
    for receipt in sorted(receipts, key=lambda r: r.purchased_at, reverse=True):
        if counts[receipt.store_id] == max_count:
            return receipt.store_id
    return None


def compute_cross_chain_share(
    receipts: list[ReceiptWithItems],
    *,
    store_chains: list[StoreRow],
    favourite_store_id: int | None,
) -> Decimal:
    if not receipts or favourite_store_id is None:
        return Decimal("0")
    chain_by_store = {store.id: store.chain for store in store_chains}
    favourite_chain = chain_by_store.get(favourite_store_id)
    other = sum(1 for r in receipts if chain_by_store.get(r.store_id) != favourite_chain)
    return (Decimal(other) / Decimal(len(receipts))).quantize(SHARE_PRECISION)


def compute_realized_savings_30d(receipts: list[ReceiptWithItems]) -> Decimal:
    if not receipts:
        return Decimal("0")
    total = Decimal("0")
    for r in receipts:
        total += (r.regular_total - r.paid_total) + r.points_earned - r.points_spent
    return total.quantize(MONEY_PRECISION)


def compute_weekday_pattern(receipts: list[ReceiptWithItems]) -> list[float]:
    if not receipts:
        return [0.0] * WEEKDAYS_COUNT
    counts = [0] * WEEKDAYS_COUNT
    for r in receipts:
        counts[r.purchased_at.astimezone(TZ).weekday()] += 1
    return [count / len(receipts) for count in counts]


def compute(
    receipts: list[ReceiptWithItems],
    savings_receipts: list[ReceiptWithItems],
    *,
    now: datetime,
    window_weeks: int,
    store_chains: list[StoreRow],
) -> UserFeaturesCalc:
    favourite_store_id = compute_favourite_store_id(receipts)
    return UserFeaturesCalc(
        window_weeks=window_weeks,
        frequency_per_week=compute_frequency_per_week(receipts, window_weeks=window_weeks),
        recency_days=compute_recency_days(receipts, now=now),
        avg_basket=compute_avg_basket(receipts),
        promo_sensitivity=compute_promo_sensitivity(receipts),
        cadence_days=compute_cadence_days(receipts),
        category_affinity=compute_category_affinity(receipts),
        weekday_pattern=compute_weekday_pattern(receipts),
        realized_savings_30d=compute_realized_savings_30d(savings_receipts),
        favourite_store_id=favourite_store_id,
        cross_chain_share=compute_cross_chain_share(
            receipts, store_chains=store_chains, favourite_store_id=favourite_store_id
        ),
    )


def _promo_and_total_sums(receipts: list[ReceiptWithItems]) -> tuple[Decimal, Decimal]:
    promo_sum = Decimal("0")
    total_sum = Decimal("0")
    for receipt in receipts:
        for item in receipt.items:
            line = item.regular_price * item.qty
            total_sum += line
            if item.is_promo:
                promo_sum += line
    return promo_sum, total_sum


def _category_totals(receipts: list[ReceiptWithItems]) -> tuple[dict[str, Decimal], Decimal]:
    totals_by_category: dict[str, Decimal] = {}
    total_all = Decimal("0")
    for receipt in receipts:
        for item in receipt.items:
            line = item.regular_price * item.qty
            total_all += line
            totals_by_category[item.category] = (
                totals_by_category.get(item.category, Decimal("0")) + line
            )
    return totals_by_category, total_all


def _category_visit_moments(receipts: list[ReceiptWithItems]) -> dict[str, list[datetime]]:
    moments_by_category: dict[str, list[datetime]] = {}
    for receipt in receipts:
        categories = {item.category for item in receipt.items}
        for category in categories:
            moments_by_category.setdefault(category, []).append(receipt.purchased_at)
    return moments_by_category


def _average_interval_days(moments: list[datetime]) -> float:
    if len(moments) < 2:
        return 0.0
    intervals = [(b - a).total_seconds() / 86400 for a, b in pairwise(moments)]
    return sum(intervals) / len(intervals)
