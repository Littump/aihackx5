from decimal import Decimal
from typing import Literal

from app.features.savings.models import SavingsSummary


def make_savings_summary(
    *, amount: Decimal = Decimal("450.00"), period: Literal["week", "month"] = "week"
) -> SavingsSummary:
    return SavingsSummary(
        period=period,
        amount=amount,
        previous_amount=Decimal("300.00"),
        delta=amount - Decimal("300.00"),
        discount_amount=Decimal("120.00"),
        points_earned=10,
        points_spent=0,
        receipts_count=2,
        top_categories=[],
    )
