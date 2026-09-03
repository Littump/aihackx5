from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.core.models import AppModel

FraudSubjectType = Literal["receipt", "referral"]
FraudDecisionKind = Literal["approve", "hold", "block"]


class ReceiptFraudContext(AppModel):
    receipts_same_store_last_60min: int
    receipts_today: int
    receipts_last_7d: int
    max_pos_share_last_7d: Decimal
    pos_receipts_sample_size: int
    frequency_per_week: Decimal
    is_return: bool
    days_since_challenge_completion_by_this_receipt: int | None
    consecutive_matching_baskets: int


class ReferralFraudContext(AppModel):
    shared_device: bool
    minutes_since_link_generated: int | None
    invitees_count: int
    invitees_all_single_purchase_500_550: bool
    invites_last_hour: int
    is_referral_ring: bool
    days_since_qualifying_with_no_activity: int | None


class FraudSignal(AppModel):
    code: str
    weight: float
    strong: bool
    detail: str


class FraudDecision(AppModel):
    score: float
    decision: FraudDecisionKind
    signals: list[FraudSignal]


class FraudCheckRow(AppModel):
    id: int
    subject_type: FraudSubjectType
    subject_id: int
    user_id: int
    score: float
    signals: list[FraudSignal]
    decision: FraudDecisionKind
    created_at: datetime
