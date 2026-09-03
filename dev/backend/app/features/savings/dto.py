from typing import Literal

from app.core.models import AppModel


class SavingsCategory(AppModel):
    category: str
    amount: float


class SavingsSummary(AppModel):
    period: Literal["week", "month"]
    amount: float
    previous_amount: float
    delta: float
    discount_amount: float
    points_earned: int
    points_spent: int
    top_categories: list[SavingsCategory]
