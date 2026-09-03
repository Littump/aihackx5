import pytest
from httpx import AsyncClient
from psycopg import AsyncConnection

from app.features.users import database, service
from tests.factories import make_domovoy_state, make_user

USER_SUMMARY_FIELDS = {"id", "pseudonym", "segment", "level"}
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
