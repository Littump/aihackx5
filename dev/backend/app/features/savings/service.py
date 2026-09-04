from typing import Literal

from psycopg import AsyncConnection

from app.core.clock import now as clock_now
from app.features.receipts import service as receipts_service
from app.features.savings import calc
from app.features.savings.models import SavingsSummary
from app.features.users import service as users_service


async def summary(
    conn: AsyncConnection, user_id: int, period: Literal["week", "month"]
) -> SavingsSummary:
    await users_service.get_user(conn, user_id)
    period_range = calc.period_range(period, clock_now())
    current = await receipts_service.list_counted_receipts_with_items(
        conn, user_id=user_id, since=period_range.start, until=period_range.end
    )
    previous = await receipts_service.list_counted_receipts_with_items(
        conn,
        user_id=user_id,
        since=period_range.previous_start,
        until=period_range.previous_end,
    )
    amount = calc.total_savings(current)
    previous_amount = calc.total_savings(previous)
    return SavingsSummary(
        period=period,
        amount=amount,
        previous_amount=previous_amount,
        delta=amount - previous_amount,
        discount_amount=calc.total_discount(current),
        points_earned=calc.total_points_earned(current),
        points_spent=calc.total_points_spent(current),
        receipts_count=len(current),
        top_categories=calc.top_categories(current),
    )
