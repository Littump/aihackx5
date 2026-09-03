from datetime import UTC, datetime
from decimal import Decimal

NOW = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)
BURST_HISTORY_OFFSETS_MIN = (50, 40, 30, 20, 10)
DAILY_LIMIT_HOUR_OFFSETS = (0, 2, 4)

HISTORY_ITEM: dict[str, object] = {
    "product_name": "Тест-товар",
    "category": "grocery",
    "qty": Decimal("1"),
    "regular_price": Decimal("100.00"),
    "paid_price": Decimal("100.00"),
}
FINAL_ITEM_PAYLOAD = [
    {
        "product_name": "Тест-товар",
        "category": "grocery",
        "qty": 1,
        "regular_price": 100.0,
        "paid_price": 100.0,
    }
]
