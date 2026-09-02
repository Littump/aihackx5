from httpx import AsyncClient


async def test_health_reports_ok(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


async def test_unknown_path_is_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/nothing")
    assert response.status_code == 404
