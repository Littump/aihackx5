from datetime import UTC, datetime
from decimal import Decimal

from app.features.receipts.models import ReceiptDetail
from app.features.referrals.models import ReferralRow

PURCHASED_AT = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)


def make_referral_row(**overrides: object) -> ReferralRow:
    base: dict[str, object] = {
        "id": 1,
        "referrer_user_id": 10,
        "referee_user_id": 20,
        "referee_kind": "new",
        "status": "pending",
        "first_purchase_at": None,
        "second_purchase_at": None,
        "fraud_score": None,
        "fraud_reasons": [],
        "referrer_reward_points": 0,
        "referee_reward_points": 0,
        "created_at": PURCHASED_AT,
        "decided_at": None,
    }
    base.update(overrides)
    return ReferralRow.model_validate(base)


def make_receipt_detail(
    *,
    paid_total: Decimal = Decimal("600"),
    purchased_at: datetime = PURCHASED_AT,
    counted: bool = True,
) -> ReceiptDetail:
    return ReceiptDetail(
        id=1,
        store_id=1,
        store_name="Тестовый магазин",
        purchased_at=purchased_at,
        regular_total=paid_total,
        paid_total=paid_total,
        discount_total=Decimal("0"),
        points_earned=0,
        points_spent=0,
        counted=counted,
        is_returned=False,
        items=[],
    )
