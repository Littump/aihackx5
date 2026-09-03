import pytest
from httpx import AsyncClient

INVALID_QUERY_CASES: list[dict[str, int | str]] = [
    {"limit": 0},
    {"limit": 501},
    {"decision": "maybe"},
]


@pytest.mark.parametrize("params", INVALID_QUERY_CASES)
async def test_list_fraud_checks_rejects_invalid_query_params(
    client: AsyncClient, params: dict[str, int | str]
) -> None:
    response = await client.get("/api/v1/pm/fraud", params=params)

    assert response.status_code == 422


async def test_list_fraud_checks_accepts_max_limit_boundary(client: AsyncClient) -> None:
    response = await client.get("/api/v1/pm/fraud", params={"limit": 500})

    assert response.status_code == 200
    assert response.json()["items"] == []
