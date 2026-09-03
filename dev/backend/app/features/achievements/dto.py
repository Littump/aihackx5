from datetime import datetime

from app.core.models import AppModel


class Achievement(AppModel):
    code: str
    title: str
    unlocked_at: datetime


class AchievementListResponse(AppModel):
    items: list[Achievement]
