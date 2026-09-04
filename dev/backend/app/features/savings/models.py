from datetime import datetime
from decimal import Decimal
from typing import Literal, Protocol

from app.core.models import AppModel


class ReceiptSavingsLike(Protocol):
    regular_total: Decimal
    paid_total: Decimal
    points_earned: int
    points_spent: int


class SavingsPeriodRange(AppModel):
    start: datetime
    end: datetime
    previous_start: datetime
    previous_end: datetime


class SavingsCategory(AppModel):
    category: str
    amount: Decimal
    items_count: int
    top_products: list[str]


class SavingsSummary(AppModel):
    period: Literal["week", "month"]
    amount: Decimal
    previous_amount: Decimal
    delta: Decimal
    discount_amount: Decimal
    points_earned: int
    points_spent: int
    receipts_count: int
    top_categories: list[SavingsCategory]
