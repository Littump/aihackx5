from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.core.models import AppModel

Mechanic = Literal["challenge", "league", "referral"]


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
