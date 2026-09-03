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
    expected_incremental_margin: float
    max_reward: float
    contribution_margin: float


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
