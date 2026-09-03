from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.core.models import AppModel

Mechanic = Literal["challenge", "league", "referral"]
type JsonValue = float | int | str | bool | list[JsonValue] | dict[str, JsonValue] | None


class MechanicDecisionContext(AppModel):
    completed_challenges_count: int
    has_league: bool
    social_propensity: Decimal


class MechanicDecisionReasons(AppModel):
    reason: str
    completed_challenges_count: int
    has_league: bool
    social_propensity: Decimal


class MechanicDecisionRow(AppModel):
    id: int
    user_id: int
    mechanic: Mechanic
    reasons: MechanicDecisionReasons
    created_at: datetime


class RecommendedMechanicCard(AppModel):
    mechanic: Mechanic
    reasons: list[str]


class SimulationRunResults(AppModel):
    purchases_per_user_control: float
    purchases_per_user_treatment: float
    share_above_n_control: float
    share_above_n_treatment: float
    frequency_uplift: float
    incremental_revenue: float
    incremental_margin: float
    reward_cost: float
    net_effect: float
    referral_conversion: float
    fraud_precision: float
    fraud_recall: float


class SimulationRunRow(AppModel):
    id: int
    created_at: datetime
    params: dict[str, JsonValue]
    results: SimulationRunResults


class EvalRunRow(AppModel):
    id: int
    created_at: datetime
    profiles: int
    hit_rate: Decimal
    invalid_rate: Decimal
    fallback_rate: Decimal
    economics_pass_rate: Decimal
    details: list[dict[str, JsonValue]]
