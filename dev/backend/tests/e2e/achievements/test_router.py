from datetime import UTC, datetime

from httpx import AsyncClient
from psycopg import AsyncConnection

from app.features.achievements.service import ACHIEVEMENT_TITLES
from tests.e2e.achievements.data import ACHIEVEMENT_FIELDS
from tests.factories import make_achievement, make_user


async def test_list_achievements_returns_unlocked_with_russian_titles(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)
    await make_achievement(conn, user.id, "first_receipt")
    await make_achievement(conn, user.id, "streak_4")

    response = await client.get(f"/api/v1/users/{user.id}/achievements")

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 2
    for item in items:
        assert set(item.keys()) == ACHIEVEMENT_FIELDS
        assert item["title"] == ACHIEVEMENT_TITLES[item["code"]]
    assert [item["code"] for item in items] == ["first_receipt", "streak_4"]


async def test_list_achievements_returns_empty_list_when_none_unlocked(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)

    response = await client.get(f"/api/v1/users/{user.id}/achievements")

    assert response.status_code == 200
    assert response.json() == {"items": []}


async def test_list_achievements_unknown_user_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users/999999/achievements")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "user_not_found"


async def test_list_achievements_sorts_by_unlocked_at_not_insertion_order(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)
    earlier = datetime(2026, 1, 1, tzinfo=UTC)
    later = datetime(2026, 6, 1, tzinfo=UTC)
    await conn.execute(
        "INSERT INTO achievements (user_id, code, unlocked_at) VALUES (%s, %s, %s)",
        (user.id, "streak_4", later),
    )
    await conn.execute(
        "INSERT INTO achievements (user_id, code, unlocked_at) VALUES (%s, %s, %s)",
        (user.id, "first_receipt", earlier),
    )

    response = await client.get(f"/api/v1/users/{user.id}/achievements")

    assert response.status_code == 200
    codes = [item["code"] for item in response.json()["items"]]
    assert codes == ["first_receipt", "streak_4"]
