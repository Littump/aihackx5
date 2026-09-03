from collections.abc import Callable
from datetime import datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient
from psycopg import AsyncConnection

from app.features.users import database, recommend, service
from tests.e2e.challenges.data import CHALLENGE_DETAIL_FIELDS
from tests.e2e.savings.data import SAVINGS_FIELDS
from tests.e2e.users.data import (
    DOMOVOY_FIELDS,
    HOME_FIELDS,
    NOW,
    RECOMMENDED_MECHANIC_FIELDS,
    REFERRAL_FIELDS,
    USER_SUMMARY_FIELDS,
)
from tests.factories import make_challenge, make_domovoy_state, make_receipt, make_user

VALID_SEGMENTS = {"regular_mid", "light", "heavy", "dormant"}
LIMIT_CASES = [
    (1, 200),
    (500, 200),
    (0, 422),
    (501, 422),
    (-1, 422),
]


async def test_list_users_sorted_by_id_with_level_from_domovoy_or_default(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    first = await make_user(conn, pseudonym="Уютный Домовой")
    second = await make_user(conn, pseudonym="Тёплый Огонёк")
    await make_domovoy_state(conn, second.id, level=7)

    response = await client.get("/api/v1/users")

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["id"] for item in items] == [first.id, second.id]
    assert {key for item in items for key in item} == USER_SUMMARY_FIELDS
    assert items[0]["level"] == 1
    assert items[1]["level"] == 7


async def test_list_users_respects_limit(client: AsyncClient, conn: AsyncConnection) -> None:
    users = [await make_user(conn) for _ in range(3)]

    response = await client.get("/api/v1/users", params={"limit": 2})

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["id"] for item in items] == [u.id for u in users[:2]]


async def test_list_users_returns_empty_items_when_no_users(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users")

    assert response.status_code == 200
    assert response.json() == {"items": []}


@pytest.mark.parametrize(("limit", "expected_status"), LIMIT_CASES)
async def test_list_users_limit_boundaries(
    client: AsyncClient, conn: AsyncConnection, limit: int, expected_status: int
) -> None:
    await make_user(conn)

    response = await client.get("/api/v1/users", params={"limit": limit})

    assert response.status_code == expected_status
    body = response.json()
    if expected_status == 422:
        assert set(body.keys()) == {"error"}
        assert set(body["error"].keys()) == {"code", "message"}
        assert isinstance(body["error"]["code"], str) and body["error"]["code"]
        assert isinstance(body["error"]["message"], str) and body["error"]["message"]
    else:
        assert body["items"]


async def test_list_users_item_types_match_contract(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    await make_user(conn, segment="heavy")

    response = await client.get("/api/v1/users")

    item = response.json()["items"][0]
    assert isinstance(item["id"], int)
    assert isinstance(item["pseudonym"], str) and item["pseudonym"]
    assert item["segment"] in VALID_SEGMENTS
    assert isinstance(item["level"], int)


async def test_pseudonym_exists_reflects_real_users_table(conn: AsyncConnection) -> None:
    user = await make_user(conn, pseudonym="Уютный Домовой")

    assert await database.pseudonym_exists(conn, pseudonym=user.pseudonym) is True
    missing = "Точно Не Существующий Псевдоним"
    assert await database.pseudonym_exists(conn, pseudonym=missing) is False


async def test_generate_pseudonym_does_not_collide_with_seeded_user(conn: AsyncConnection) -> None:
    await make_user(conn, pseudonym="Уютный Домовой")

    result = await service.generate_pseudonym(conn)

    assert result != "Уютный Домовой"
    assert await database.pseudonym_exists(conn, pseudonym=result) is False


async def test_get_home_happy_path_generates_hero_and_matches_contract(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn, social_propensity=Decimal("0"))

    response = await client.get(f"/api/v1/users/{user.id}/home")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == HOME_FIELDS
    assert set(body["user"].keys()) == USER_SUMMARY_FIELDS
    assert body["user"]["id"] == user.id
    assert set(body["domovoy"].keys()) == DOMOVOY_FIELDS
    assert set(body["savings"].keys()) == SAVINGS_FIELDS
    assert body["savings"]["period"] == "month"
    assert body["hero_challenge"] is not None
    assert set(body["hero_challenge"].keys()) == CHALLENGE_DETAIL_FIELDS
    assert body["hero_challenge"]["is_hero"] is True
    assert body["league"] is None
    assert set(body["referral"].keys()) == REFERRAL_FIELDS
    assert body["referral"]["code"] == user.referral_code
    assert body["referral"]["invited_count"] == 0
    assert body["referral"]["rewarded_count"] == 0
    assert set(body["recommended_mechanic"].keys()) == RECOMMENDED_MECHANIC_FIELDS
    assert body["recommended_mechanic"]["mechanic"] == "challenge"
    assert isinstance(body["insight"], str) and body["insight"]

    active_count = await conn.execute(
        "SELECT count(*) FROM challenges WHERE user_id = %s AND status = 'active'", (user.id,)
    )
    row = await active_count.fetchone()
    assert row is not None
    assert row[0] >= 1


async def test_get_home_reuses_existing_active_hero(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    hero = await make_challenge(conn, user.id, is_hero=True, status="active")

    response = await client.get(f"/api/v1/users/{user.id}/home")

    assert response.status_code == 200
    assert response.json()["hero_challenge"]["id"] == hero.id
    count_cursor = await conn.execute(
        "SELECT count(*) FROM challenges WHERE user_id = %s", (user.id,)
    )
    row = await count_cursor.fetchone()
    assert row is not None
    assert row[0] == 1


async def test_get_home_unknown_user_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users/999999/home")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "user_not_found"


async def test_get_home_writes_mechanic_decision_row_on_each_call(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)

    first = await client.get(f"/api/v1/users/{user.id}/home")
    second = await client.get(f"/api/v1/users/{user.id}/home")

    assert first.status_code == 200
    assert second.status_code == 200
    cursor = await conn.execute(
        "SELECT mechanic, reasons FROM mechanic_decisions WHERE user_id = %s ORDER BY id",
        (user.id,),
    )
    rows = await cursor.fetchall()
    assert len(rows) == 2
    for mechanic, reasons in rows:
        assert mechanic == "challenge"
        assert reasons["reason"]
        assert reasons["completed_challenges_count"] == 0
        assert reasons["has_league"] is False


async def test_get_home_with_receipt_history_computes_real_savings_and_insight(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn, social_propensity=Decimal("0"))
    await make_receipt(conn, user.id, purchased_at=NOW)
    await make_receipt(conn, user.id, purchased_at=NOW, points_earned=20)

    response = await client.get(f"/api/v1/users/{user.id}/home")

    assert response.status_code == 200
    body = response.json()
    savings = body["savings"]
    assert savings["amount"] == 100.0
    assert savings["previous_amount"] == 0.0
    assert savings["delta"] == 100.0
    assert savings["discount_amount"] == 80.0
    assert savings["points_earned"] == 20
    assert savings["points_spent"] == 0
    assert savings["top_categories"][0] == {"category": "dairy", "amount": 60.0}
    assert body["insight"] == "За month ты сэкономил 100 ₽ — Домовой доволен!"


async def _active_challenge_count(conn: AsyncConnection, user_id: int) -> int:
    cursor = await conn.execute(
        "SELECT count(*) FROM challenges WHERE user_id = %s AND status = 'active'", (user_id,)
    )
    row = await cursor.fetchone()
    assert row is not None
    return int(row[0])


async def test_get_home_consecutive_calls_from_scratch_do_not_duplicate_active_challenges(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)

    first = await client.get(f"/api/v1/users/{user.id}/home")
    count_after_first = await _active_challenge_count(conn, user.id)
    second = await client.get(f"/api/v1/users/{user.id}/home")
    count_after_second = await _active_challenge_count(conn, user.id)

    assert count_after_first >= 1
    assert count_after_second == count_after_first
    assert first.json()["hero_challenge"]["id"] == second.json()["hero_challenge"]["id"]


async def test_get_home_recommended_mechanic_reflects_state_across_calls(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn, social_propensity=Decimal("0"))
    await make_challenge(conn, user.id, is_hero=True, status="active")
    await make_challenge(conn, user.id, is_hero=False, status="completed")
    await make_challenge(conn, user.id, is_hero=False, status="completed")

    first = await client.get(f"/api/v1/users/{user.id}/home")

    assert first.json()["recommended_mechanic"] == {
        "mechanic": "challenge",
        "reason": recommend.REASON_DEFAULT,
    }

    await conn.execute(
        "UPDATE users SET social_propensity = %s WHERE id = %s", (Decimal("0.7"), user.id)
    )
    second = await client.get(f"/api/v1/users/{user.id}/home")

    assert second.json()["recommended_mechanic"] == {
        "mechanic": "referral",
        "reason": recommend.REASON_REFERRAL,
    }
    cursor = await conn.execute(
        "SELECT mechanic FROM mechanic_decisions WHERE user_id = %s ORDER BY id", (user.id,)
    )
    rows = await cursor.fetchall()
    assert [row[0] for row in rows] == ["challenge", "referral"]


async def test_get_home_does_not_expire_active_side_when_only_hero_completed_early(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    # DEF-3: _ensure_hero_challenge triggers full refresh_weekly on hero-only absence
    freeze_time(NOW)
    user = await make_user(conn)
    await make_challenge(conn, user.id, is_hero=True, status="completed", completed_at=NOW)
    side = await make_challenge(
        conn, user.id, is_hero=False, status="active", progress=Decimal("2"), target=Decimal("3")
    )

    await client.get(f"/api/v1/users/{user.id}/home")

    cursor = await conn.execute("SELECT status, progress FROM challenges WHERE id = %s", (side.id,))
    row = await cursor.fetchone()
    assert row is not None
    assert row[0] == "active"
    assert row[1] == Decimal("2")
