from datetime import datetime
from typing import Literal

from pydantic import Field

from app.core.models import AppModel


class SimulateReceiptInput(AppModel):
    scenario: Literal["typical", "category_boost", "fraud_burst"] = "typical"
    store_id: int | None = None


class ReceiptItemInput(AppModel):
    product_name: str
    category: str
    qty: float = Field(ge=0.001)
    regular_price: float = Field(ge=0)
    paid_price: float = Field(ge=0)
    is_promo: bool = False


class ReceiptInput(AppModel):
    user_id: int
    store_id: int
    purchased_at: datetime
    points_earned: int = 0
    points_spent: int = 0
    pos_id: str | None = None
    items: list[ReceiptItemInput] = Field(min_length=1)


class ReceiptItem(AppModel):
    product_name: str
    category: str
    qty: float
    regular_price: float
    paid_price: float
    is_promo: bool


class Receipt(AppModel):
    id: int
    store_id: int
    store_name: str
    purchased_at: datetime
    regular_total: float
    paid_total: float
    discount_total: float
    points_earned: int
    points_spent: int
    counted: bool
    is_returned: bool
    items: list[ReceiptItem]


class ReceiptListResponse(AppModel):
    items: list[Receipt]


class FraudSignal(AppModel):
    code: str
    weight: float
    strong: bool
    detail: str


class FraudDecision(AppModel):
    score: float
    decision: Literal["approve", "hold", "block"]
    signals: list[FraudSignal]


class DomovoyState(AppModel):
    xp: int
    level: int
    xp_to_next_level: int
    mood: Literal["cheerful", "cozy", "healthy", "bored", "sleepy"]
    mood_reason: str
    streak_weeks: int
    items: list[str]


class ChallengeProgressDelta(AppModel):
    challenge_id: int
    progress_before: float
    progress_after: float
    target: float
    completed: bool
    reward_points: int
    reward_xp: int


class ReceiptProcessingResult(AppModel):
    receipt: Receipt
    counted: bool
    counted_reason: str | None
    xp_delta: int
    domovoy: DomovoyState
    savings_delta: float
    challenges: list[ChallengeProgressDelta]
    league_rank_before: int | None
    league_rank_after: int | None
    referral_status: str | None
    fraud: FraudDecision
    achievements_unlocked: list[str]
