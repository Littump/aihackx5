from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.core.models import AppModel

RewardKind = Literal["receipt_xp", "challenge", "streak", "league", "referral", "achievement"]


class RewardLedgerEntry(AppModel):
    id: int
    user_id: int
    kind: RewardKind
    xp_delta: int
    points_delta: int
    ref_type: str | None
    ref_id: int | None
    created_at: datetime


class ChallengeEconomics(AppModel):
    avg_basket: float
    expected_incremental_purchases: float
    expected_incremental_margin: float
    max_reward_rub: float
    contribution_margin: float
    reward_share_max: float


class RationaleFeatures(AppModel):
    frequency_per_week: float | None = None
    recency_days: int | None = None
    share: float | None = None
    visits: int | None = None


class ChallengeDraft(AppModel):
    type: Literal["frequency", "category"]
    category: str | None
    baseline: Decimal
    target: Decimal
    priority: float
    rationale_features: RationaleFeatures


class ChallengeRow(AppModel):
    id: int
    user_id: int
    type: Literal["frequency", "category"]
    category: str | None
    status: Literal["active", "completed", "failed", "expired"]
    is_hero: bool
    baseline: Decimal
    target: Decimal
    progress: Decimal
    period_start: datetime
    period_end: datetime
    reward_xp: int
    reward_points: int
    economics: ChallengeEconomics
    # rationale_features keys vary by challenge type, contract keeps it an open object
    rationale_features: dict[str, float]
    copy_title: str
    copy_body: str
    copy_explanation: str
    copy_source: Literal["llm", "template"]
    created_at: datetime
    completed_at: datetime | None


class ChallengeListResult(AppModel):
    hero: ChallengeRow | None
    side: list[ChallengeRow]
    history: list[ChallengeRow]
