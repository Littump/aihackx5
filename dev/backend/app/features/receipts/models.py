from datetime import datetime
from decimal import Decimal
from typing import Literal, Protocol

from app.core.models import AppModel


class ReceiptRow(AppModel):
    id: int
    user_id: int
    store_id: int
    purchased_at: datetime
    regular_total: Decimal
    paid_total: Decimal
    discount_total: Decimal
    points_earned: int
    points_spent: int
    counted: bool
    is_returned: bool
    returned_at: datetime | None
    source: Literal["synthetic", "simulated", "api"]
    pos_id: str | None
    created_at: datetime


class ReceiptItemRow(AppModel):
    id: int
    receipt_id: int
    product_name: str
    category: str
    qty: Decimal
    regular_price: Decimal
    paid_price: Decimal
    is_promo: bool


class ReceiptItemDraft(AppModel):
    product_name: str
    category: str
    qty: Decimal
    regular_price: Decimal
    paid_price: Decimal
    is_promo: bool = False


class ReceiptItemInputLike(Protocol):
    product_name: str
    category: str
    qty: float
    regular_price: float
    paid_price: float
    is_promo: bool


class ReceiptTotals(AppModel):
    regular_total: Decimal
    paid_total: Decimal
    discount_total: Decimal


class CountedDecision(AppModel):
    counted: bool
    counted_reason: Literal["dedup_window", "daily_limit"] | None


class ReceiptDetail(AppModel):
    id: int
    store_id: int
    store_name: str
    purchased_at: datetime
    regular_total: Decimal
    paid_total: Decimal
    discount_total: Decimal
    points_earned: int
    points_spent: int
    counted: bool
    is_returned: bool
    items: list[ReceiptItemRow]


class FraudSignalStub(AppModel):
    code: str
    weight: float
    strong: bool
    detail: str


class FraudDecisionStub(AppModel):
    score: float
    decision: Literal["approve", "hold", "block"]
    signals: list[FraudSignalStub]


class DomovoyStateStub(AppModel):
    xp: int
    level: int
    xp_to_next_level: int
    mood: Literal["cheerful", "cozy", "healthy", "bored", "sleepy"]
    mood_reason: str
    streak_weeks: int
    items: list[str]


class ChallengeProgressDeltaStub(AppModel):
    challenge_id: int
    progress_before: Decimal
    progress_after: Decimal
    target: Decimal
    completed: bool
    reward_points: int
    reward_xp: int


class ReceiptProcessingOutcome(AppModel):
    receipt: ReceiptDetail
    counted: bool
    counted_reason: Literal["dedup_window", "daily_limit"] | None
    xp_delta: int
    domovoy: DomovoyStateStub
    savings_delta: Decimal
    challenges: list[ChallengeProgressDeltaStub]
    league_rank_before: int | None
    league_rank_after: int | None
    referral_status: str | None
    fraud: FraudDecisionStub
    achievements_unlocked: list[str]
