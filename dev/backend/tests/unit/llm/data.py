from decimal import Decimal

from app.features.savings.models import SavingsSummary


def make_savings_summary(*, amount: Decimal = Decimal("450.00")) -> SavingsSummary:
    return SavingsSummary(
        period="week",
        amount=amount,
        previous_amount=Decimal("300.00"),
        delta=amount - Decimal("300.00"),
        discount_amount=Decimal("120.00"),
        points_earned=10,
        points_spent=0,
        top_categories=[],
    )
