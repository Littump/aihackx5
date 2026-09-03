from datetime import UTC, datetime
from decimal import Decimal

from app.features.receipts.models import ReceiptItemDraft
from app.features.user_features.models import CategoryAffinity, UserFeaturesRow

TOTALS_CASES: list[tuple[list[ReceiptItemDraft], Decimal, Decimal, Decimal]] = [
    (
        [
            ReceiptItemDraft(
                product_name="Молоко",
                category="dairy",
                qty=Decimal("1"),
                regular_price=Decimal("89.90"),
                paid_price=Decimal("79.90"),
            ),
            ReceiptItemDraft(
                product_name="Багет",
                category="bakery",
                qty=Decimal("2"),
                regular_price=Decimal("59.90"),
                paid_price=Decimal("49.90"),
                is_promo=True,
            ),
        ],
        Decimal("209.70"),
        Decimal("179.70"),
        Decimal("30.00"),
    ),
    (
        [
            ReceiptItemDraft(
                product_name="Сыр",
                category="dairy",
                qty=Decimal("0.500"),
                regular_price=Decimal("20.03"),
                paid_price=Decimal("20.02"),
            ),
        ],
        Decimal("10.02"),
        Decimal("10.01"),
        Decimal("0.01"),
    ),
    (
        [],
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
    ),
    (
        [
            ReceiptItemDraft(
                product_name="Оливки",
                category="grocery",
                qty=Decimal("0.333"),
                regular_price=Decimal("19.99"),
                paid_price=Decimal("15.90"),
            ),
        ],
        Decimal("6.66"),
        Decimal("5.29"),
        Decimal("1.37"),
    ),
    (
        [
            ReceiptItemDraft(
                product_name="Сыр 1",
                category="dairy",
                qty=Decimal("1"),
                regular_price=Decimal("10.004"),
                paid_price=Decimal("9.996"),
            ),
            ReceiptItemDraft(
                product_name="Сыр 2",
                category="dairy",
                qty=Decimal("1"),
                regular_price=Decimal("10.004"),
                paid_price=Decimal("9.996"),
            ),
        ],
        Decimal("20.01"),
        Decimal("19.99"),
        Decimal("0.02"),
    ),
]

SIMULATE_COMPUTED_AT = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)

SKEWED_AFFINITY: dict[str, CategoryAffinity] = {
    "dairy": CategoryAffinity(share=0.9, visits=10, cadence_days=3.0),
    "bakery": CategoryAffinity(share=0.1, visits=2, cadence_days=10.0),
}

PICK_STORE_CASES: list[tuple[int | None, int | None, int | None]] = [
    (5, 7, 5),
    (None, 7, 7),
    (None, None, None),
]

SEED_SAMPLE = list(range(30))
AVG_BASKET_CASES = [Decimal("600"), Decimal("1200"), Decimal("0")]


def make_features(
    *,
    avg_basket: Decimal = Decimal("0"),
    promo_sensitivity: Decimal = Decimal("0"),
    category_affinity: dict[str, CategoryAffinity] | None = None,
    favourite_store_id: int | None = None,
) -> UserFeaturesRow:
    return UserFeaturesRow(
        user_id=1,
        computed_at=SIMULATE_COMPUTED_AT,
        window_weeks=10,
        frequency_per_week=Decimal("2"),
        recency_days=5,
        avg_basket=avg_basket,
        promo_sensitivity=promo_sensitivity,
        cadence_days=Decimal("3"),
        category_affinity=category_affinity or {},
        weekday_pattern=[0.0] * 7,
        realized_savings_30d=Decimal("0"),
        favourite_store_id=favourite_store_id,
        cross_chain_share=Decimal("0"),
    )
