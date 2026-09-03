from datetime import datetime
from decimal import Decimal

from app.core.models import AppModel


class AchievementRow(AppModel):
    id: int
    user_id: int
    code: str
    unlocked_at: datetime


class AchievementView(AppModel):
    code: str
    title: str
    unlocked_at: datetime


class AchievementContext(AppModel):
    is_first_receipt: bool
    streak_weeks: int
    savings_month: Decimal
    chains_last_30d: list[str]
