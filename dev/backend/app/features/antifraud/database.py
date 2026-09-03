from typing import Literal

from psycopg import AsyncConnection
from psycopg.rows import class_row
from psycopg.types.json import Jsonb

from app.features.antifraud.models import FraudCheckRow, FraudDecision, FraudDecisionKind

FRAUD_CHECK_COLUMNS = "id, subject_type, subject_id, user_id, score, signals, decision, created_at"
FRAUD_CHECK_INSERT = (
    "INSERT INTO fraud_checks (subject_type, subject_id, user_id, score, signals, decision) "
    "VALUES (%(subject_type)s, %(subject_id)s, %(user_id)s, %(score)s, %(signals)s, %(decision)s) "
    f"RETURNING {FRAUD_CHECK_COLUMNS}"
)
FRAUD_CHECK_LIST_FOR_USER = (
    f"SELECT {FRAUD_CHECK_COLUMNS} FROM fraud_checks "
    "WHERE user_id = %(user_id)s ORDER BY created_at DESC, id DESC LIMIT %(limit)s"
)
FRAUD_CHECK_LIST = (
    f"SELECT {FRAUD_CHECK_COLUMNS} FROM fraud_checks "
    "ORDER BY created_at DESC, id DESC LIMIT %(limit)s"
)
FRAUD_CHECK_LIST_BY_DECISION = (
    f"SELECT {FRAUD_CHECK_COLUMNS} FROM fraud_checks "
    "WHERE decision = %(decision)s ORDER BY created_at DESC, id DESC LIMIT %(limit)s"
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


async def list_fraud_checks_for_user(
    conn: AsyncConnection, *, user_id: int, limit: int
) -> list[FraudCheckRow]:
    async with conn.cursor(row_factory=class_row(FraudCheckRow)) as cur:
        await cur.execute(FRAUD_CHECK_LIST_FOR_USER, {"user_id": user_id, "limit": limit})
        return await cur.fetchall()


async def list_fraud_checks(
    conn: AsyncConnection, *, limit: int, decision: FraudDecisionKind | None
) -> list[FraudCheckRow]:
    query = FRAUD_CHECK_LIST_BY_DECISION if decision is not None else FRAUD_CHECK_LIST
    params: dict[str, object] = {"limit": limit}
    if decision is not None:
        params["decision"] = decision
    async with conn.cursor(row_factory=class_row(FraudCheckRow)) as cur:
        await cur.execute(query, params)
        return await cur.fetchall()
