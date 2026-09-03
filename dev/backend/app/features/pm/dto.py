from datetime import datetime
from typing import Literal

from app.core.models import AppModel
from app.features.challenges.dto import ChallengeDetail, RewardLedgerEntry
from app.features.pm.models import JsonValue, SimulationRunResults
from app.features.receipts.dto import FraudSignal
from app.features.users.dto import UserSummary


class CategoryAffinity(AppModel):
    share: float
    visits: int
    cadence_days: float


class UserFeatures(AppModel):
    computed_at: datetime
    window_weeks: int
    frequency_per_week: float
    recency_days: int
    avg_basket: float
    promo_sensitivity: float
    cadence_days: float
    category_affinity: dict[str, CategoryAffinity]
    realized_savings_30d: float
    favourite_store_id: int
    cross_chain_share: float


class RecommendedMechanic(AppModel):
    mechanic: Literal["challenge", "league", "referral"]
    reasons: list[str]


class FraudCheck(AppModel):
    id: int
    subject_type: Literal["receipt", "referral"]
    subject_id: int
    user_id: int
    score: float
    decision: Literal["approve", "hold", "block"]
    signals: list[FraudSignal]
    created_at: datetime


class FraudCheckListResponse(AppModel):
    items: list[FraudCheck]


class SimulationRun(AppModel):
    id: int
    created_at: datetime
    params: dict[str, JsonValue]
    results: SimulationRunResults


class EvalRun(AppModel):
    id: int
    created_at: datetime
    profiles: int
    hit_rate: float
    invalid_rate: float
    fallback_rate: float
    economics_pass_rate: float
    details: list[dict[str, JsonValue]]


class PmUserResponse(AppModel):
    user: UserSummary
    features: UserFeatures
    recommended_mechanic: RecommendedMechanic
    hero_challenge: ChallengeDetail | None
    rewards_total_points: int
    rewards_total_xp: int
    expected_incremental_margin_month: float
    fraud_checks: list[FraudCheck]
    ledger: list[RewardLedgerEntry]
