from datetime import datetime

from app.core.models import AppModel
from app.features.challenges.models import RewardKind


class RewardEvent(AppModel):
    id: int
    kind: RewardKind
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


class RewardsSummary(AppModel):
    points_balance: int
    xp: int
    level: int
    xp_to_next_level: int
    rules: list[RewardRule]
    history: list[RewardEvent]
