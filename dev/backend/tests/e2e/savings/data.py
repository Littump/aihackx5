from decimal import Decimal

SAVINGS_FIELDS = {
    "period",
    "amount",
    "previous_amount",
    "delta",
    "discount_amount",
    "points_earned",
    "points_spent",
    "receipts_count",
    "top_categories",
}
SAVINGS_CATEGORY_FIELDS = {"category", "amount", "items_count", "top_products"}

AC_ITEM = [
    {
        "product_name": "Корзина",
        "category": "grocery",
        "qty": Decimal("1"),
        "regular_price": Decimal("1000.00"),
        "paid_price": Decimal("850.00"),
    }
]

FOUR_CATEGORY_ITEMS = [
    {
        "product_name": "Молоко",
        "category": "dairy",
        "qty": Decimal("1"),
        "regular_price": Decimal("100.00"),
        "paid_price": Decimal("0.00"),
    },
    {
        "product_name": "Багет",
        "category": "bakery",
        "qty": Decimal("1"),
        "regular_price": Decimal("50.00"),
        "paid_price": Decimal("0.00"),
    },
    {
        "product_name": "Сок",
        "category": "drinks",
        "qty": Decimal("1"),
        "regular_price": Decimal("30.00"),
        "paid_price": Decimal("0.00"),
    },
    {
        "product_name": "Чипсы",
        "category": "snacks",
        "qty": Decimal("1"),
        "regular_price": Decimal("10.00"),
        "paid_price": Decimal("0.00"),
    },
]
