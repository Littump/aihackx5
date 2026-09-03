from psycopg import AsyncConnection
from psycopg.rows import class_row
from psycopg.types.json import Jsonb

from app.features.pm.models import Mechanic, MechanicDecisionReasons, MechanicDecisionRow

MECHANIC_DECISION_INSERT = (
    "INSERT INTO mechanic_decisions (user_id, mechanic, reasons) "
    "VALUES (%(user_id)s, %(mechanic)s, %(reasons)s) "
    "RETURNING id, user_id, mechanic, reasons, created_at"
)


async def insert_mechanic_decision(
    conn: AsyncConnection,
    *,
    user_id: int,
    mechanic: Mechanic,
    reasons: MechanicDecisionReasons,
) -> MechanicDecisionRow:
    params = {
        "user_id": user_id,
        "mechanic": mechanic,
        "reasons": Jsonb(reasons.model_dump(mode="json")),
    }
    async with conn.cursor(row_factory=class_row(MechanicDecisionRow)) as cur:
        await cur.execute(MECHANIC_DECISION_INSERT, params)
        row = await cur.fetchone()
        assert row is not None
        return row
