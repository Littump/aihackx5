from datetime import UTC, datetime
from decimal import Decimal

from app.features.receipts.models import ReceiptDetail, ReceiptRow

NOW = datetime(2026, 9, 15, 10, 0, tzinfo=UTC)

ACHIEVEMENT_FIELDS = {"code", "title", "unlocked_at"}

SAVER_ITEM = [
    {
        "product_name": "Крупный чек",
        "category": "grocery",
        "qty": Decimal("1"),
        "regular_price": Decimal("2000.00"),
        "paid_price": Decimal("900.00"),
    }
]

BELOW_SAVER_THRESHOLD_ITEM = [
    {
        "product_name": "Почти тысяча",
        "category": "grocery",
        "qty": Decimal("1"),
        "regular_price": Decimal("1099.99"),
        "paid_price": Decimal("100.00"),
    }
]

AT_SAVER_THRESHOLD_ITEM = [
    {
        "product_name": "Ровно тысяча",
        "category": "grocery",
        "qty": Decimal("1"),
        "regular_price": Decimal("1100.00"),
        "paid_price": Decimal("100.00"),
    }
]


def receipt_detail(row: ReceiptRow, *, counted: bool | None = None) -> ReceiptDetail:
    return ReceiptDetail(
        id=row.id,
        store_id=row.store_id,
        store_name="Дом",
        purchased_at=row.purchased_at,
        regular_total=row.regular_total,
        paid_total=row.paid_total,
        discount_total=row.discount_total,
        points_earned=row.points_earned,
        points_spent=row.points_spent,
        counted=row.counted if counted is None else counted,
        is_returned=row.is_returned,
        items=[],
    )


def not_counted_receipt() -> ReceiptDetail:
    return ReceiptDetail(
        id=999,
        store_id=1,
        store_name="Дом",
        purchased_at=NOW,
        regular_total=Decimal("0"),
        paid_total=Decimal("0"),
        discount_total=Decimal("0"),
        points_earned=0,
        points_spent=0,
        counted=False,
        is_returned=False,
        items=[],
    )
