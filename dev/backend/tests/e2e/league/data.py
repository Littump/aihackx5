from datetime import UTC, datetime
from decimal import Decimal

NOW = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)

LEAGUE_RESPONSE_FIELDS = {
    "division",
    "division_name",
    "week_start",
    "week_end",
    "size",
    "my_rank",
    "my_score",
    "my_zone",
    "promotion_cutoff",
    "demotion_cutoff",
    "members",
    "house",
}
LEAGUE_MEMBER_FIELDS = {"pseudonym", "level", "score", "rank", "is_me"}
LEAGUE_HOUSE_FIELDS = {"store_name", "avg_savings_rate", "district_rank", "district_size"}

NO_SAVINGS_ITEM: list[dict[str, object]] = [
    {
        "product_name": "Соль",
        "category": "grocery",
        "qty": Decimal("1"),
        "regular_price": Decimal("100.00"),
        "paid_price": Decimal("100.00"),
    }
]
DISCOUNT_ITEM: list[dict[str, object]] = [
    {
        "product_name": "Масло",
        "category": "dairy",
        "qty": Decimal("1"),
        "regular_price": Decimal("250.00"),
        "paid_price": Decimal("220.00"),
    }
]
HIGH_DISCOUNT_ITEM: list[dict[str, object]] = [
    {
        "product_name": "Кофе",
        "category": "grocery",
        "qty": Decimal("1"),
        "regular_price": Decimal("200.00"),
        "paid_price": Decimal("50.00"),
    }
]
LOW_DISCOUNT_ITEM: list[dict[str, object]] = [
    {
        "product_name": "Хлеб",
        "category": "bakery",
        "qty": Decimal("1"),
        "regular_price": Decimal("200.00"),
        "paid_price": Decimal("180.00"),
    }
]
