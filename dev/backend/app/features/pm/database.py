from decimal import Decimal

from psycopg import AsyncConnection
from psycopg.rows import class_row
from psycopg.types.json import Jsonb

from app.features.pm.models import (
    EvalRunRow,
    JsonValue,
    Mechanic,
    MechanicDecisionReasons,
    MechanicDecisionRow,
    SimulationRunResults,
    SimulationRunRow,
)

MECHANIC_DECISION_INSERT = (
    "INSERT INTO mechanic_decisions (user_id, mechanic, reasons) "
    "VALUES (%(user_id)s, %(mechanic)s, %(reasons)s) "
    "RETURNING id, user_id, mechanic, reasons, created_at"
)
MECHANIC_DECISION_LATEST = (
    "SELECT id, user_id, mechanic, reasons, created_at FROM mechanic_decisions "
    "WHERE user_id = %(user_id)s ORDER BY created_at DESC, id DESC LIMIT 1"
)
SIMULATION_RUN_INSERT = (
    "INSERT INTO simulation_runs (params, results) "
    "VALUES (%(params)s, %(results)s) "
    "RETURNING id, created_at, params, results"
)
SIMULATION_RUN_LATEST = (
    "SELECT id, created_at, params, results FROM simulation_runs "
    "ORDER BY created_at DESC, id DESC LIMIT 1"
)
EVAL_RUN_COLUMNS = (
    "id, created_at, profiles, hit_rate, invalid_rate, fallback_rate, economics_pass_rate, details"
)
EVAL_RUN_INSERT = (
    "INSERT INTO eval_runs (profiles, hit_rate, invalid_rate, fallback_rate, "
    "economics_pass_rate, details) "
    "VALUES (%(profiles)s, %(hit_rate)s, %(invalid_rate)s, %(fallback_rate)s, "
    "%(economics_pass_rate)s, %(details)s) "
    f"RETURNING {EVAL_RUN_COLUMNS}"
)
EVAL_RUN_LATEST = (
    f"SELECT {EVAL_RUN_COLUMNS} FROM eval_runs ORDER BY created_at DESC, id DESC LIMIT 1"
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


async def insert_simulation_run(
    conn: AsyncConnection,
    *,
    params: dict[str, JsonValue],
    results: SimulationRunResults,
) -> SimulationRunRow:
    query_params = {
        "params": Jsonb(params),
        "results": Jsonb(results.model_dump(mode="json")),
    }
    async with conn.cursor(row_factory=class_row(SimulationRunRow)) as cur:
        await cur.execute(SIMULATION_RUN_INSERT, query_params)
        row = await cur.fetchone()
        assert row is not None
        return row


async def get_latest_simulation_run(conn: AsyncConnection) -> SimulationRunRow | None:
    async with conn.cursor(row_factory=class_row(SimulationRunRow)) as cur:
        await cur.execute(SIMULATION_RUN_LATEST)
        return await cur.fetchone()


async def insert_eval_run(
    conn: AsyncConnection,
    *,
    profiles: int,
    hit_rate: Decimal,
    invalid_rate: Decimal,
    fallback_rate: Decimal,
    economics_pass_rate: Decimal,
    details: list[dict[str, JsonValue]],
) -> EvalRunRow:
    params = {
        "profiles": profiles,
        "hit_rate": hit_rate,
        "invalid_rate": invalid_rate,
        "fallback_rate": fallback_rate,
        "economics_pass_rate": economics_pass_rate,
        "details": Jsonb(details),
    }
    async with conn.cursor(row_factory=class_row(EvalRunRow)) as cur:
        await cur.execute(EVAL_RUN_INSERT, params)
        row = await cur.fetchone()
        assert row is not None
        return row


async def get_latest_eval_run(conn: AsyncConnection) -> EvalRunRow | None:
    async with conn.cursor(row_factory=class_row(EvalRunRow)) as cur:
        await cur.execute(EVAL_RUN_LATEST)
        return await cur.fetchone()
