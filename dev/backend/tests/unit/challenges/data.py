from datetime import UTC, datetime
from decimal import Decimal

from app.features.user_features.models import CategoryAffinity, UserFeaturesRow

COMPUTED_AT = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
DEFAULT_WINDOW_WEEKS = 10
FREQUENCY_DISABLED = Decimal("6")


def make_features(
    *,
    frequency_per_week: Decimal = Decimal("0"),
    recency_days: int | None = 999,
    avg_basket: Decimal = Decimal("0"),
    category_affinity: dict[str, CategoryAffinity] | None = None,
    window_weeks: int = DEFAULT_WINDOW_WEEKS,
) -> UserFeaturesRow:
    return UserFeaturesRow(
        user_id=1,
        computed_at=COMPUTED_AT,
        window_weeks=window_weeks,
        frequency_per_week=frequency_per_week,
        recency_days=recency_days,
        avg_basket=avg_basket,
        promo_sensitivity=Decimal("0"),
        cadence_days=None,
        category_affinity=category_affinity or {},
        weekday_pattern=[0.0] * 7,
        realized_savings_30d=Decimal("0"),
        favourite_store_id=None,
        cross_chain_share=Decimal("0"),
    )


NO_HISTORY_FEATURES = make_features()

FREQUENCY_HEADROOM_CASES: list[tuple[Decimal, bool]] = [
    (Decimal("5.9"), True),
    (Decimal("5.99"), True),
    (Decimal("6"), False),
    (Decimal("6.1"), False),
]

RECENCY_BOUNDARY_CASES: list[tuple[int, bool]] = [
    (21, True),
    (22, False),
]

CATEGORY_AFFINITY_CASES: list[tuple[str, float, int, bool]] = [
    ("dairy", 0.10, 3, True),
    ("dairy", 0.099, 3, False),
    ("dairy", 0.10, 2, False),
    ("alcohol", 0.5, 10, False),
    ("alcohol", 0.10, 3, False),
]

TARGET_CASES: list[tuple[Decimal, Decimal]] = [
    (Decimal("2"), Decimal("3")),
    (Decimal("5"), Decimal("6")),
]

BASELINE_FLOOR_CASES: list[tuple[Decimal, Decimal]] = [
    (Decimal("0"), Decimal("1")),
    (Decimal("0.4"), Decimal("1")),
]

ECONOMICS_CASES: list[tuple[Decimal, Decimal, Decimal, Decimal, Decimal, int]] = [
    (Decimal("2"), Decimal("3"), Decimal("600"), Decimal("90"), Decimal("36"), 30),
    (Decimal("1.5"), Decimal("3"), Decimal("555"), Decimal("124.875"), Decimal("49.95"), 40),
    (Decimal("2"), Decimal("3"), Decimal("150"), Decimal("22.5"), Decimal("9"), 0),
]
