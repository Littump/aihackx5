from datetime import UTC, datetime
from decimal import Decimal

from app.features.domovoy.models import DomovoyStateRow, Mood
from app.features.receipts.models import ReceiptItemRow, ReceiptWithItems

PURCHASED_AT = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)


def make_domovoy_state_row(**overrides: object) -> DomovoyStateRow:
    base: dict[str, object] = {
        "user_id": 1,
        "xp": 0,
        "level": 1,
        "mood": "bored",
        "mood_reason": "",
        "streak_weeks": 0,
        "streak_freeze_available": True,
        "items": [],
        "last_fed_at": None,
        "updated_at": PURCHASED_AT,
    }
    base.update(overrides)
    return DomovoyStateRow.model_validate(base)


def _item(category: str, item_id: int) -> ReceiptItemRow:
    return ReceiptItemRow(
        id=item_id,
        receipt_id=1,
        product_name=category,
        category=category,
        qty=Decimal("1"),
        regular_price=Decimal("100.00"),
        paid_price=Decimal("100.00"),
        is_promo=False,
    )


def _receipt(receipt_id: int, categories: list[str]) -> ReceiptWithItems:
    return ReceiptWithItems(
        id=receipt_id,
        store_id=1,
        purchased_at=PURCHASED_AT,
        regular_total=Decimal("100.00"),
        paid_total=Decimal("100.00"),
        points_earned=0,
        points_spent=0,
        items=[_item(c, item_id=i) for i, c in enumerate(categories, start=1)],
    )


def _priced_receipt(receipt_id: int, category_prices: list[tuple[str, str]]) -> ReceiptWithItems:
    items = [
        ReceiptItemRow(
            id=i,
            receipt_id=receipt_id,
            product_name=category,
            category=category,
            qty=Decimal("1"),
            regular_price=Decimal(price),
            paid_price=Decimal(price),
            is_promo=False,
        )
        for i, (category, price) in enumerate(category_prices, start=1)
    ]
    total = sum((item.regular_price for item in items), Decimal("0"))
    return ReceiptWithItems(
        id=receipt_id,
        store_id=1,
        purchased_at=PURCHASED_AT,
        regular_total=total,
        paid_total=total,
        points_earned=0,
        points_spent=0,
        items=items,
    )


MOOD_CASES: list[tuple[str, list[ReceiptWithItems], Mood]] = [
    ("no receipts is sleepy", [], "sleepy"),
    (
        "dominant fruits_veg and dairy is healthy",
        [_receipt(1, ["dairy", "fruits_veg"])],
        "healthy",
    ),
    (
        "healthy wins over cozy when both match",
        [
            _receipt(1, ["dairy", "bakery", "drinks"]),
            _receipt(2, ["dairy", "bakery", "drinks"]),
        ],
        "healthy",
    ),
    (
        "cozy wins over cheerful when both match",
        [
            _receipt(1, ["bakery", "drinks", "meat_fish", "grocery", "snacks"]),
            _receipt(2, ["bakery", "drinks"]),
        ],
        "cozy",
    ),
    (
        "five distinct categories without healthy or cozy is cheerful",
        [
            _receipt(1, ["meat_fish", "grocery"]),
            _receipt(2, ["snacks", "household", "beauty"]),
        ],
        "cheerful",
    ),
    (
        "few categories without a pattern is bored",
        [_receipt(1, ["meat_fish", "grocery"])],
        "bored",
    ),
    (
        "healthy share exactly at 0.30 threshold is healthy",
        [_priced_receipt(1, [("dairy", "30"), ("other", "70")])],
        "healthy",
    ),
    (
        "healthy share just below 0.30 threshold is not healthy",
        [_priced_receipt(1, [("dairy", "29"), ("other", "71")])],
        "bored",
    ),
    (
        "exactly five distinct categories is the cheerful boundary",
        [_receipt(1, ["meat_fish", "grocery", "snacks", "household", "beauty"])],
        "cheerful",
    ),
    (
        "four distinct categories misses the cheerful boundary",
        [_receipt(1, ["meat_fish", "grocery", "snacks", "household"])],
        "bored",
    ),
    (
        "only one receipt with both cozy categories misses the min-two rule",
        [
            _receipt(1, ["bakery", "drinks"]),
            _receipt(2, ["meat_fish", "grocery"]),
        ],
        "bored",
    ),
    # documents the chosen reading of domain-rules §8: cozy needs both categories per receipt
    (
        "bakery and drinks split across two separate receipts is not cozy",
        [_receipt(1, ["bakery"]), _receipt(2, ["drinks"])],
        "bored",
    ),
]

STREAK_CASES: list[tuple[str, int, bool, bool, int, bool]] = [
    ("skip with freeze keeps streak and burns it", 3, False, True, 3, False),
    ("skip without freeze resets to zero", 3, False, False, 0, False),
    ("completed increments streak and freeze stays available", 3, True, True, 4, True),
    ("completed increments streak and freeze stays unavailable", 3, True, False, 4, False),
]
