from psycopg import AsyncConnection
from psycopg.rows import class_row
from psycopg.types.json import Jsonb

from app.features.pm.models import Mechanic, MechanicDecisionReasons, MechanicDecisionRow

MECHANIC_DECISION_INSERT = (
    "INSERT INTO mechanic_decisions (user_id, mechanic, reasons) "
    "VALUES (%(user_id)s, %(mechanic)s, %(reasons)s) "
    "RETURNING id, user_id, mechanic, reasons, created_at"
)
MECHANIC_DECISION_LATEST = (
    "SELECT id, user_id, mechanic, reasons, created_at FROM mechanic_decisions "
    "WHERE user_id = %(user_id)s ORDER BY created_at DESC, id DESC LIMIT 1"
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


async def get_latest_mechanic_decision(
    conn: AsyncConnection, user_id: int
) -> MechanicDecisionRow | None:
    async with conn.cursor(row_factory=class_row(MechanicDecisionRow)) as cur:
        await cur.execute(MECHANIC_DECISION_LATEST, {"user_id": user_id})
        return await cur.fetchone()
