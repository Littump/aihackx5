from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.features.receipts.models import ReceiptItemRow, ReceiptWithItems
from app.game_rules import TIMEZONE

TZ = ZoneInfo(TIMEZONE)
BASE_TIME = datetime(2026, 9, 15, 10, 0, tzinfo=TZ)


def _item(category: str, regular: str, paid: str) -> ReceiptItemRow:
    return ReceiptItemRow(
        id=1,
        receipt_id=1,
        product_name="товар",
        category=category,
        qty=Decimal("1"),
        regular_price=Decimal(regular),
        paid_price=Decimal(paid),
        is_promo=False,
    )


AC_RECEIPT = ReceiptWithItems(
    id=1,
    store_id=1,
    purchased_at=BASE_TIME,
    regular_total=Decimal("1000.00"),
    paid_total=Decimal("850.00"),
    points_earned=10,
    points_spent=50,
    items=[],
)
EXPECTED_AC_SAVINGS = Decimal("210.00")

NO_DISCOUNT_RECEIPT = ReceiptWithItems(
    id=2,
    store_id=1,
    purchased_at=BASE_TIME,
    regular_total=Decimal("300.00"),
    paid_total=Decimal("300.00"),
    points_earned=0,
    points_spent=0,
    items=[],
)
TWO_RECEIPTS = [AC_RECEIPT, NO_DISCOUNT_RECEIPT]
EXPECTED_TWO_RECEIPTS_SAVINGS = Decimal("210.00")

FOUR_CATEGORY_RECEIPT = ReceiptWithItems(
    id=3,
    store_id=1,
    purchased_at=BASE_TIME,
    regular_total=Decimal("190.00"),
    paid_total=Decimal("0.00"),
    points_earned=0,
    points_spent=0,
    items=[
        _item("dairy", "100.00", "0.00"),
        _item("bakery", "50.00", "0.00"),
        _item("drinks", "30.00", "0.00"),
        _item("snacks", "10.00", "0.00"),
    ],
)
EXPECTED_TOP_CATEGORIES = [
    ("dairy", Decimal("100.00")),
    ("bakery", Decimal("50.00")),
    ("drinks", Decimal("30.00")),
]

TIE_CATEGORY_RECEIPT = ReceiptWithItems(
    id=4,
    store_id=1,
    purchased_at=BASE_TIME,
    regular_total=Decimal("100.00"),
    paid_total=Decimal("0.00"),
    points_earned=0,
    points_spent=0,
    items=[
        _item("snacks", "50.00", "0.00"),
        _item("drinks", "50.00", "0.00"),
    ],
)
EXPECTED_TIE_CATEGORY_ORDER = ["snacks", "drinks"]

ZERO_DISCOUNT_WITH_POINTS_RECEIPT = ReceiptWithItems(
    id=5,
    store_id=1,
    purchased_at=BASE_TIME,
    regular_total=Decimal("300.00"),
    paid_total=Decimal("300.00"),
    points_earned=20,
    points_spent=15,
    items=[],
)
EXPECTED_ZERO_DISCOUNT_SAVINGS = Decimal("35.00")

SAME_CATEGORY_ACROSS_RECEIPTS = [
    ReceiptWithItems(
        id=6,
        store_id=1,
        purchased_at=BASE_TIME,
        regular_total=Decimal("20.00"),
        paid_total=Decimal("0.00"),
        points_earned=0,
        points_spent=0,
        items=[_item("dairy", "20.00", "0.00")],
    ),
    ReceiptWithItems(
        id=7,
        store_id=1,
        purchased_at=BASE_TIME,
        regular_total=Decimal("30.00"),
        paid_total=Decimal("0.00"),
        points_earned=0,
        points_spent=0,
        items=[_item("dairy", "30.00", "0.00")],
    ),
]
EXPECTED_SAME_CATEGORY_TOTAL = Decimal("50.00")

WEEK_BOUNDARY_CASES = [
    (0, "current"),
    (6, "current"),
    (7, "previous"),
    (8, "previous"),
    (13, "previous"),
    (14, "none"),
]
