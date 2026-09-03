from decimal import Decimal

from psycopg import AsyncConnection

from app.features.pm import database as pm_db
from app.features.pm.models import EvalRunRow, JsonValue, SimulationRunResults, SimulationRunRow

DEFAULT_SIMULATION_DETAILS: list[dict[str, JsonValue]] = [
    {"challenge": "frequency", "verdict": "hit"}
]


def _default_simulation_results() -> SimulationRunResults:
    return SimulationRunResults(
        purchases_per_user_control=1.0,
        purchases_per_user_treatment=1.2,
        share_above_n_control=0.2,
        share_above_n_treatment=0.3,
        frequency_uplift=0.2,
        incremental_revenue=500.0,
        incremental_margin=80.0,
        reward_cost=20.0,
        net_effect=60.0,
        referral_conversion=0.05,
        fraud_precision=0.9,
        fraud_recall=0.85,
    )


async def make_simulation_run(
    conn: AsyncConnection,
    *,
    params: dict[str, JsonValue] | None = None,
    results: SimulationRunResults | None = None,
) -> SimulationRunRow:
    return await pm_db.insert_simulation_run(
        conn,
        params=params if params is not None else {"users": 100, "weeks": 4},
        results=results if results is not None else _default_simulation_results(),
    )


async def make_eval_run(
    conn: AsyncConnection,
    *,
    profiles: int = 30,
    hit_rate: Decimal = Decimal("0.800"),
    invalid_rate: Decimal = Decimal("0.050"),
    fallback_rate: Decimal = Decimal("0.100"),
    economics_pass_rate: Decimal = Decimal("0.900"),
    details: list[dict[str, JsonValue]] | None = None,
) -> EvalRunRow:
    return await pm_db.insert_eval_run(
        conn,
        profiles=profiles,
        hit_rate=hit_rate,
        invalid_rate=invalid_rate,
        fallback_rate=fallback_rate,
        economics_pass_rate=economics_pass_rate,
        details=details if details is not None else DEFAULT_SIMULATION_DETAILS,
    )
