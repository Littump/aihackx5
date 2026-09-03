from typing import Literal

from psycopg import AsyncConnection
from psycopg.rows import class_row
from psycopg.types.json import Jsonb

from app.features.antifraud.models import FraudCheckRow, FraudDecision

FRAUD_CHECK_COLUMNS = "id, subject_type, subject_id, user_id, score, signals, decision, created_at"
FRAUD_CHECK_INSERT = (
    "INSERT INTO fraud_checks (subject_type, subject_id, user_id, score, signals, decision) "
    "VALUES (%(subject_type)s, %(subject_id)s, %(user_id)s, %(score)s, %(signals)s, %(decision)s) "
    f"RETURNING {FRAUD_CHECK_COLUMNS}"
)


async def insert_fraud_check(
    conn: AsyncConnection,
    *,
    subject_type: Literal["receipt", "referral"],
    subject_id: int,
    user_id: int,
    decision: FraudDecision,
) -> FraudCheckRow:
    params = {
        "subject_type": subject_type,
        "subject_id": subject_id,
        "user_id": user_id,
        "score": decision.score,
        "signals": Jsonb([signal.model_dump(mode="json") for signal in decision.signals]),
        "decision": decision.decision,
    }
    async with conn.cursor(row_factory=class_row(FraudCheckRow)) as cur:
        await cur.execute(FRAUD_CHECK_INSERT, params)
        row = await cur.fetchone()
        assert row is not None
        return row
