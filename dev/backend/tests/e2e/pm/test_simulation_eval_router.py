from decimal import Decimal

from httpx import AsyncClient
from psycopg import AsyncConnection

from app.features.pm.models import JsonValue, SimulationRunResults
from tests.e2e.pm.data import EVAL_RUN_FIELDS, SIMULATION_RESULTS_FIELDS, SIMULATION_RUN_FIELDS
from tests.factories import make_eval_run, make_simulation_run

FULL_SIMULATION_RESULTS = SimulationRunResults(
    purchases_per_user_control=1.1,
    purchases_per_user_treatment=1.4,
    share_above_n_control=0.2,
    share_above_n_treatment=0.3,
    frequency_uplift=0.15,
    incremental_revenue=12345.67,
    incremental_margin=2345.67,
    reward_cost=345.67,
    net_effect=2000.0,
    referral_conversion=0.08,
    fraud_precision=0.92,
    fraud_recall=0.87,
)
FULL_EVAL_DETAILS: list[dict[str, JsonValue]] = [
    {"challenge": "frequency", "verdict": "hit", "reason": "цель достигнута"},
    {"challenge": "category_focus", "verdict": "invalid", "reason": "нет affinity"},
]


async def test_get_latest_simulation_returns_404_when_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/pm/simulation/latest")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "simulation_not_found"


async def test_get_latest_eval_returns_404_when_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/pm/eval/latest")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "eval_not_found"


async def test_get_latest_simulation_matches_inserted_row(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    row = await make_simulation_run(
        conn, params={"users": 100, "weeks": 4}, results=FULL_SIMULATION_RESULTS
    )

    response = await client.get("/api/v1/pm/simulation/latest")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == SIMULATION_RUN_FIELDS
    assert set(body["results"].keys()) == SIMULATION_RESULTS_FIELDS
    assert body["id"] == row.id
    assert body["params"] == {"users": 100, "weeks": 4}
    assert body["results"] == FULL_SIMULATION_RESULTS.model_dump(mode="json")


async def test_get_latest_eval_matches_inserted_row(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    row = await make_eval_run(
        conn,
        profiles=42,
        hit_rate=Decimal("0.750"),
        invalid_rate=Decimal("0.100"),
        fallback_rate=Decimal("0.050"),
        economics_pass_rate=Decimal("0.900"),
        details=FULL_EVAL_DETAILS,
    )

    response = await client.get("/api/v1/pm/eval/latest")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == EVAL_RUN_FIELDS
    assert body["id"] == row.id
    assert body["profiles"] == 42
    assert body["hit_rate"] == 0.75
    assert body["invalid_rate"] == 0.1
    assert body["fallback_rate"] == 0.05
    assert body["economics_pass_rate"] == 0.9
    assert body["details"] == FULL_EVAL_DETAILS


async def test_get_latest_simulation_accepts_empty_params(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    await make_simulation_run(conn, params={})

    response = await client.get("/api/v1/pm/simulation/latest")

    assert response.status_code == 200
    assert response.json()["params"] == {}


async def test_get_latest_eval_accepts_empty_details(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    await make_eval_run(conn, details=[])

    response = await client.get("/api/v1/pm/eval/latest")

    assert response.status_code == 200
    assert response.json()["details"] == []


async def test_get_latest_simulation_returns_the_most_recently_inserted_row(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    await make_simulation_run(conn, params={"users": 100})
    second = await make_simulation_run(conn, params={"users": 200})

    response = await client.get("/api/v1/pm/simulation/latest")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == second.id
    assert body["params"] == {"users": 200}


async def test_get_latest_eval_returns_the_most_recently_inserted_row(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    await make_eval_run(conn, profiles=10)
    second = await make_eval_run(conn, profiles=20)

    response = await client.get("/api/v1/pm/eval/latest")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == second.id
    assert body["profiles"] == 20
