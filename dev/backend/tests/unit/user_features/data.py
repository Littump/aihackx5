from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.features.receipts.models import ReceiptItemRow, ReceiptWithItems
from app.features.users.models import StoreRow
from app.game_rules import TIMEZONE

TZ = ZoneInfo(TIMEZONE)
BASE_TIME = datetime(2026, 1, 5, 12, 0, tzinfo=TZ)
NOW = BASE_TIME + timedelta(days=23)
WINDOW_WEEKS = 4

STORE_PYATEROCHKA = StoreRow(
    id=1, name="Пятёрочка", chain="pyaterochka", district="Центр", city="Москва"
)
STORE_PEREKRESTOK = StoreRow(
    id=2, name="Перекрёсток", chain="perekrestok", district="Центр", city="Москва"
)
STORE_CHAINS = [STORE_PYATEROCHKA, STORE_PEREKRESTOK]


def _item(category: str, regular: str, paid: str, *, is_promo: bool = False) -> ReceiptItemRow:
    return ReceiptItemRow(
        id=1,
        receipt_id=1,
        product_name="товар",
        category=category,
        qty=Decimal("1"),
        regular_price=Decimal(regular),
        paid_price=Decimal(paid),
        is_promo=is_promo,
    )


def _receipt(
    receipt_id: int,
    offset_days: int,
    store: StoreRow,
    category: str,
    regular: str,
    paid: str,
    *,
    is_promo: bool = False,
) -> ReceiptWithItems:
    return ReceiptWithItems(
        id=receipt_id,
        store_id=store.id,
        purchased_at=BASE_TIME + timedelta(days=offset_days),
        regular_total=Decimal(regular),
        paid_total=Decimal(paid),
        points_earned=5,
        points_spent=0,
        items=[_item(category, regular, paid, is_promo=is_promo)],
    )


SIX_RECEIPTS: list[ReceiptWithItems] = [
    _receipt(1, 0, STORE_PYATEROCHKA, "dairy", "100.00", "80.00", is_promo=True),
    _receipt(2, 3, STORE_PYATEROCHKA, "dairy", "200.00", "200.00"),
    _receipt(3, 7, STORE_PEREKRESTOK, "bakery", "100.00", "90.00"),
    _receipt(4, 10, STORE_PYATEROCHKA, "fruits_veg", "200.00", "180.00"),
    _receipt(5, 14, STORE_PYATEROCHKA, "dairy", "200.00", "200.00"),
    _receipt(6, 18, STORE_PEREKRESTOK, "bakery", "200.00", "150.00", is_promo=True),
]

EXPECTED_FREQUENCY_PER_WEEK = Decimal("1.500")
EXPECTED_RECENCY_DAYS = 5
EXPECTED_AVG_BASKET = Decimal("150.00")
EXPECTED_PROMO_SENSITIVITY = Decimal("0.300")
EXPECTED_CADENCE_DAYS = Decimal("3.60")
EXPECTED_FAVOURITE_STORE_ID = STORE_PYATEROCHKA.id
EXPECTED_CROSS_CHAIN_SHARE = Decimal("0.333")
EXPECTED_REALIZED_SAVINGS_30D = Decimal("130.00")
EXPECTED_CATEGORY_SHARE = {"dairy": 0.5, "bakery": 0.3, "fruits_veg": 0.2}
EXPECTED_CATEGORY_VISITS = {"dairy": 3, "bakery": 2, "fruits_veg": 1}
EXPECTED_CATEGORY_CADENCE = {"dairy": 7.0, "bakery": 11.0, "fruits_veg": 0.0}
EXPECTED_WEEKDAY_PATTERN = [3 / 6, 0.0, 0.0, 2 / 6, 1 / 6, 0.0, 0.0]

TIE_RECEIPTS: list[ReceiptWithItems] = [
    _receipt(1, 0, STORE_PYATEROCHKA, "dairy", "100.00", "100.00"),
    _receipt(2, 5, STORE_PEREKRESTOK, "dairy", "100.00", "100.00"),
]

STORE_MAGNIT = StoreRow(id=3, name="Магнит", chain="perekrestok", district="Центр", city="Москва")

TIE_WITH_NON_MAX_LATEST_RECEIPTS: list[ReceiptWithItems] = [
    _receipt(1, 0, STORE_PYATEROCHKA, "dairy", "100.00", "100.00"),
    _receipt(2, 2, STORE_PYATEROCHKA, "dairy", "100.00", "100.00"),
    _receipt(3, 4, STORE_PEREKRESTOK, "dairy", "100.00", "100.00"),
    _receipt(4, 6, STORE_PEREKRESTOK, "dairy", "100.00", "100.00"),
    _receipt(5, 8, STORE_MAGNIT, "dairy", "100.00", "100.00"),
]


def _receipt_with_items(
    receipt_id: int, offset_days: int, store: StoreRow, items: list[ReceiptItemRow]
) -> ReceiptWithItems:
    paid_total = sum((item.paid_price * item.qty for item in items), Decimal("0"))
    regular_total = sum((item.regular_price * item.qty for item in items), Decimal("0"))
    return ReceiptWithItems(
        id=receipt_id,
        store_id=store.id,
        purchased_at=BASE_TIME + timedelta(days=offset_days),
        regular_total=regular_total,
        paid_total=paid_total,
        points_earned=0,
        points_spent=0,
        items=items,
    )


MULTI_CATEGORY_RECEIPT: list[ReceiptWithItems] = [
    _receipt_with_items(
        1,
        0,
        STORE_PYATEROCHKA,
        [
            _item("dairy", "60.00", "50.00"),
            _item("bakery", "40.00", "40.00", is_promo=True),
        ],
    )
]
EXPECTED_MULTI_CATEGORY_SHARE = {"dairy": 0.6, "bakery": 0.4}
EXPECTED_MULTI_CATEGORY_PROMO_SENSITIVITY = Decimal("0.400")

SAME_CATEGORY_RECEIPT: list[ReceiptWithItems] = [
    _receipt_with_items(
        1,
        0,
        STORE_PYATEROCHKA,
        [_item("dairy", "30.00", "30.00"), _item("dairy", "20.00", "20.00")],
    )
]

POINTS_SPENT_RECEIPT: list[ReceiptWithItems] = [
    ReceiptWithItems(
        id=1,
        store_id=STORE_PYATEROCHKA.id,
        purchased_at=BASE_TIME,
        regular_total=Decimal("1000.00"),
        paid_total=Decimal("850.00"),
        points_earned=10,
        points_spent=50,
        items=[],
    )
]
EXPECTED_POINTS_SPENT_SAVINGS = Decimal("210.00")
