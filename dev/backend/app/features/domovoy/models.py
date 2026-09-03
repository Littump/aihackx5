from datetime import datetime
from typing import Literal

from app.core.models import AppModel


class DomovoyStateRow(AppModel):
    user_id: int
    xp: int
    level: int
    mood: Literal["cheerful", "cozy", "healthy", "bored", "sleepy"]
    mood_reason: str
    streak_weeks: int
    streak_freeze_available: bool
    items: list[str]
    last_fed_at: datetime | None
    updated_at: datetime


class DomovoyLevelRow(AppModel):
    user_id: int
    level: int
