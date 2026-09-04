from datetime import datetime
from typing import Literal

from app.core.models import AppModel


class RewardEvent(AppModel):
    id: int
    kind: Literal["receipt_xp", "challenge", "streak", "league", "referral", "achievement"]
    title: str
    detail: str | None
    xp_delta: int
    points_delta: int
    created_at: datetime


class RewardRule(AppModel):
    code: str
    title: str
    xp: int
    points_min: int
    points_max: int


class RewardsResponse(AppModel):
    points_balance: int
    points_from_rewards: int
    points_from_receipts: int
    xp: int
    level: int
    xp_to_next_level: int
    rules: list[RewardRule]
    history: list[RewardEvent]
