from datetime import datetime
from decimal import Decimal
from typing import Literal

from app.core.models import AppModel


class SavingsPeriodRange(AppModel):
    start: datetime
    end: datetime
    previous_start: datetime
    previous_end: datetime


class SavingsCategory(AppModel):
    category: str
    amount: Decimal


class SavingsSummary(AppModel):
    period: Literal["week", "month"]
    amount: Decimal
    previous_amount: Decimal
    delta: Decimal
    discount_amount: Decimal
    points_earned: int
    points_spent: int
    top_categories: list[SavingsCategory]
