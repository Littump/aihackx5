from collections.abc import Callable
from datetime import datetime
from decimal import Decimal

from httpx import AsyncClient
from psycopg import AsyncConnection

from tests.e2e.challenges.data import (
    CHALLENGE_DETAIL_FIELDS,
    CHALLENGE_ECONOMICS_FIELDS,
    CHALLENGE_FIELDS,
    MULTI_CATEGORY_AFFINITY,
    NOW,
)
from tests.factories import make_challenge, make_user, make_user_features


async def _seed_multi_candidate_user(conn: AsyncConnection) -> int:
    user = await make_user(conn)
    await make_user_features(
        conn,
        user.id,
        frequency_per_week=Decimal("2"),
        recency_days=5,
        avg_basket=Decimal("600"),
        category_affinity=MULTI_CATEGORY_AFFINITY,
    )
    return user.id


async def test_refresh_creates_exactly_one_hero_and_side_at_most_two(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user_id = await _seed_multi_candidate_user(conn)

    response = await client.post(f"/api/v1/users/{user_id}/challenges/refresh")

    assert response.status_code == 200
    body = response.json()
    assert body["hero"] is not None
    assert body["hero"]["is_hero"] is True
    assert body["hero"]["type"] == "frequency"
    assert body["hero"]["baseline"] == 2.0
    assert body["hero"]["target"] == 3.0
    assert body["hero"]["reward_points"] == 30
    assert body["hero"]["economics"]["max_reward_rub"] == 36.0
    assert 0 <= len(body["side"]) <= 2
    slots = [(body["hero"]["type"], body["hero"]["category"])]
    for item in body["side"]:
        assert item["is_hero"] is False
        slot = (item["type"], item["category"])
        assert slot not in slots
        slots.append(slot)


async def test_refresh_twice_does_not_duplicate_active_challenges(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user_id = await _seed_multi_candidate_user(conn)

    first = await client.post(f"/api/v1/users/{user_id}/challenges/refresh")
    second = await client.post(f"/api/v1/users/{user_id}/challenges/refresh")

    assert first.status_code == 200 and second.status_code == 200
    cursor = await conn.execute(
        "SELECT count(*) FROM challenges WHERE user_id = %s AND status = 'active'", (user_id,)
    )
    row = await cursor.fetchone()
    assert row is not None
    active_count = 1 + len(second.json()["side"])
    assert row[0] == active_count
    history_ids = {item["id"] for item in second.json()["history"]}
    assert history_ids


async def test_refresh_unknown_user_returns_404(client: AsyncClient) -> None:
    response = await client.post("/api/v1/users/999999/challenges/refresh")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "user_not_found"


async def test_list_challenges_unknown_user_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users/999999/challenges")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "user_not_found"


async def test_refresh_fallback_candidate_for_user_without_history(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)

    response = await client.post(f"/api/v1/users/{user.id}/challenges/refresh")

    assert response.status_code == 200
    body = response.json()
    assert body["hero"] is not None
    assert body["hero"]["is_hero"] is True
    assert body["hero"]["type"] == "frequency"
    assert body["hero"]["category"] is None
    assert body["hero"]["baseline"] == 1.0
    assert body["hero"]["target"] == 2.0
    assert body["hero"]["reward_points"] == 0
    assert body["hero"]["copy_source"] == "template"
    assert body["side"] == []


async def test_list_challenges_matches_refreshed_state(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user_id = await _seed_multi_candidate_user(conn)
    refreshed = await client.post(f"/api/v1/users/{user_id}/challenges/refresh")

    response = await client.get(f"/api/v1/users/{user_id}/challenges")

    assert response.status_code == 200
    assert response.json() == refreshed.json()
    assert set(response.json()["hero"].keys()) == CHALLENGE_DETAIL_FIELDS


async def test_history_items_expose_only_base_challenge_fields(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)
    await make_challenge(conn, user.id, status="expired", is_hero=True)

    response = await client.get(f"/api/v1/users/{user.id}/challenges")

    assert response.status_code == 200
    body = response.json()
    assert body["hero"] is None
    assert len(body["history"]) == 1
    assert set(body["history"][0].keys()) == CHALLENGE_FIELDS


async def test_get_challenge_returns_detail_for_owner(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)
    challenge = await make_challenge(conn, user.id)

    response = await client.get(f"/api/v1/users/{user.id}/challenges/{challenge.id}")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == CHALLENGE_DETAIL_FIELDS
    assert set(body["economics"].keys()) == CHALLENGE_ECONOMICS_FIELDS
    assert body["title"] == "Заголовок"
    assert body["body"] == "Текст"
    assert "copy_title" not in body


async def test_get_challenge_of_another_user_returns_404(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    owner = await make_user(conn)
    stranger = await make_user(conn)
    challenge = await make_challenge(conn, owner.id)

    response = await client.get(f"/api/v1/users/{stranger.id}/challenges/{challenge.id}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "challenge_not_found"


async def test_get_nonexistent_challenge_returns_404(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)

    response = await client.get(f"/api/v1/users/{user.id}/challenges/999999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "challenge_not_found"


async def test_get_challenge_for_unknown_user_returns_user_not_found(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/users/999999/challenges/1")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "user_not_found"
