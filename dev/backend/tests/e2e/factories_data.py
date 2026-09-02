from decimal import Decimal

RECEIPT_ITEM_CASES: list[tuple[list[dict[str, object]], Decimal, Decimal, Decimal]] = [
    (
        [
            {
                "product_name": "Молоко",
                "category": "dairy",
                "qty": Decimal("1"),
                "regular_price": Decimal("100.00"),
                "paid_price": Decimal("90.00"),
            },
            {
                "product_name": "Багет",
                "category": "bakery",
                "qty": Decimal("2"),
                "regular_price": Decimal("50.00"),
                "paid_price": Decimal("45.00"),
            },
        ],
        Decimal("200.00"),
        Decimal("180.00"),
        Decimal("20.00"),
    ),
    (
        [
            {
                "product_name": "Йогурт",
                "category": "dairy",
                "qty": Decimal("3"),
                "regular_price": Decimal("35.50"),
                "paid_price": Decimal("29.90"),
            },
        ],
        Decimal("106.50"),
        Decimal("89.70"),
        Decimal("16.80"),
    ),
    (
        [
            {
                "product_name": "Сыр",
                "category": "dairy",
                "qty": Decimal("0.500"),
                "regular_price": Decimal("20.03"),
                "paid_price": Decimal("20.02"),
            },
        ],
        Decimal("10.02"),
        Decimal("10.01"),
        Decimal("0.01"),
    ),
]

DEFAULT_RECEIPT_REGULAR_TOTAL = Decimal("389.80")
DEFAULT_RECEIPT_PAID_TOTAL = Decimal("349.80")
DEFAULT_RECEIPT_DISCOUNT_TOTAL = Decimal("40.00")
