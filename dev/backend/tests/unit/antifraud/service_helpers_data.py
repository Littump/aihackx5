from datetime import datetime
from decimal import Decimal

from app.core.clock import TZ
from app.features.receipts.models import ReceiptDetail, ReceiptItemRow, ReceiptRow
from app.features.referrals.models import ReferralRow

ANCHOR = datetime(2026, 9, 2, 12, 0, tzinfo=TZ)


def receipt_row(*, id: int = 1, store_id: int = 1, purchased_at: datetime = ANCHOR) -> ReceiptRow:
    return ReceiptRow(
        id=id,
        user_id=1,
        store_id=store_id,
        purchased_at=purchased_at,
        regular_total=Decimal("100"),
        paid_total=Decimal("100"),
        discount_total=Decimal("0"),
        points_earned=0,
        points_spent=0,
        counted=True,
        is_returned=False,
        returned_at=None,
        source="api",
        pos_id=None,
        created_at=purchased_at,
    )


def receipt_row_with_pos(*, id: int, pos_id: str | None) -> ReceiptRow:
    return receipt_row(id=id).model_copy(update={"pos_id": pos_id})


def receipt_item(category: str) -> ReceiptItemRow:
    return ReceiptItemRow(
        id=1,
        receipt_id=1,
        product_name="Товар",
        category=category,
        qty=Decimal("1"),
        regular_price=Decimal("100"),
        paid_price=Decimal("100"),
        is_promo=False,
    )


def receipt_detail(
    *, id: int, paid_total: Decimal, categories: tuple[str, ...] = ("dairy",)
) -> ReceiptDetail:
    return ReceiptDetail(
        id=id,
        store_id=1,
        store_name="Магазин",
        purchased_at=ANCHOR,
        regular_total=paid_total,
        paid_total=paid_total,
        discount_total=Decimal("0"),
        points_earned=0,
        points_spent=0,
        counted=True,
        is_returned=False,
        items=[receipt_item(c) for c in categories],
    )


def referral_row(
    *, id: int = 1, referrer_user_id: int = 1, referee_user_id: int = 2, created_at: datetime
) -> ReferralRow:
    return ReferralRow(
        id=id,
        referrer_user_id=referrer_user_id,
        referee_user_id=referee_user_id,
        referee_kind="new",
        status="pending",
        first_purchase_at=None,
        second_purchase_at=None,
        fraud_score=None,
        fraud_reasons=[],
        referrer_reward_points=0,
        referee_reward_points=0,
        created_at=created_at,
        decided_at=None,
    )
