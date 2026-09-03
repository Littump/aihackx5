from datetime import UTC, datetime

from httpx import AsyncClient
from psycopg import AsyncConnection

from tests.factories import make_eval_run, make_simulation_run

TIED_CREATED_AT = datetime(2026, 9, 15, 12, 0, 0, tzinfo=UTC)


async def _pin_simulation_created_at(
    conn: AsyncConnection, row_id: int, created_at: datetime
) -> None:
    await conn.execute(
        "UPDATE simulation_runs SET created_at = %(created_at)s WHERE id = %(id)s",
        {"created_at": created_at, "id": row_id},
    )


async def _pin_eval_created_at(conn: AsyncConnection, row_id: int, created_at: datetime) -> None:
    await conn.execute(
        "UPDATE eval_runs SET created_at = %(created_at)s WHERE id = %(id)s",
        {"created_at": created_at, "id": row_id},
    )


async def test_get_latest_simulation_prefers_higher_id_on_tied_created_at(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    first = await make_simulation_run(conn, params={"tag": "first"})
    second = await make_simulation_run(conn, params={"tag": "second"})
    await _pin_simulation_created_at(conn, first.id, TIED_CREATED_AT)
    await _pin_simulation_created_at(conn, second.id, TIED_CREATED_AT)

    response = await client.get("/api/v1/pm/simulation/latest")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == second.id
    assert body["params"] == {"tag": "second"}


async def test_get_latest_eval_prefers_higher_id_on_tied_created_at(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    first = await make_eval_run(conn, profiles=10)
    second = await make_eval_run(conn, profiles=20)
    await _pin_eval_created_at(conn, first.id, TIED_CREATED_AT)
    await _pin_eval_created_at(conn, second.id, TIED_CREATED_AT)

    response = await client.get("/api/v1/pm/eval/latest")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == second.id
    assert body["profiles"] == 20
