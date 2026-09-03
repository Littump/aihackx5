from datetime import datetime
from typing import Literal

from app.core.models import AppModel

Mood = Literal["cheerful", "cozy", "healthy", "bored", "sleepy"]


class DomovoyStateRow(AppModel):
    user_id: int
    xp: int
    level: int
    mood: Mood
    mood_reason: str
    streak_weeks: int
    streak_freeze_available: bool
    items: list[str]
    last_fed_at: datetime | None
    updated_at: datetime


class DomovoyLevelRow(AppModel):
    user_id: int
    level: int


class DomovoyDelta(AppModel):
    xp_delta: int
    xp: int
    level: int
    mood: Mood
    mood_reason: str
    last_fed_at: datetime | None
