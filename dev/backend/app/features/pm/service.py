from psycopg import AsyncConnection

from app.features.pm import database
from app.features.pm.models import (
    Mechanic,
    MechanicDecisionContext,
    MechanicDecisionReasons,
    MechanicDecisionRow,
)


async def record_decision(
    conn: AsyncConnection,
    *,
    user_id: int,
    mechanic: Mechanic,
    reason: str,
    context: MechanicDecisionContext,
) -> MechanicDecisionRow:
    reasons = MechanicDecisionReasons(
        reason=reason,
        completed_challenges_count=context.completed_challenges_count,
        has_league=context.has_league,
        social_propensity=context.social_propensity,
    )
    return await database.insert_mechanic_decision(
        conn, user_id=user_id, mechanic=mechanic, reasons=reasons
    )
