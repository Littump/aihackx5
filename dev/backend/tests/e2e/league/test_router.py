from collections.abc import Callable
from datetime import datetime

import pytest
from httpx import AsyncClient
from psycopg import AsyncConnection

from app.game_rules import DIVISION_NAMES
from tests.e2e.league.data import (
    HIGH_DISCOUNT_ITEM,
    LEAGUE_HOUSE_FIELDS,
    LEAGUE_MEMBER_FIELDS,
    LEAGUE_RESPONSE_FIELDS,
    LOW_DISCOUNT_ITEM,
    NOW,
)
from tests.factories import make_league, make_league_member, make_receipt, make_store, make_user

DIVISION_MIDDLE = 3


async def _seed_scored_league(
    conn: AsyncConnection, *, store_id: int, division: int, count: int
) -> list[int]:
    league = await make_league(conn, store_id=store_id, division=division)
    user_ids: list[int] = []
    for index in range(count):
        member = await make_user(conn)
        await make_league_member(conn, league.id, member.id, score=count - index)
        user_ids.append(member.id)
    return user_ids


async def test_get_league_happy_path_matches_contract_fields(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    store = await make_store(conn)
    user_ids = await _seed_scored_league(conn, store_id=store.id, division=DIVISION_MIDDLE, count=3)

    response = await client.get(f"/api/v1/users/{user_ids[0]}/league")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == LEAGUE_RESPONSE_FIELDS
    assert body["division"] == DIVISION_MIDDLE
    assert body["division_name"] == DIVISION_NAMES[DIVISION_MIDDLE]
    assert body["size"] == 3
    assert body["my_rank"] == 1
    assert body["my_score"] == 3
    assert body["my_zone"] == "promotion"
    for member in body["members"]:
        assert set(member.keys()) == LEAGUE_MEMBER_FIELDS
    assert set(body["house"].keys()) == LEAGUE_HOUSE_FIELDS


async def test_get_league_members_do_not_expose_other_users_identity(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    store = await make_store(conn)
    user_ids = await _seed_scored_league(conn, store_id=store.id, division=DIVISION_MIDDLE, count=5)

    response = await client.get(f"/api/v1/users/{user_ids[0]}/league")

    body = response.json()
    is_me_flags = [member["is_me"] for member in body["members"]]
    assert is_me_flags.count(True) == 1
    for member in body["members"]:
        assert "user_id" not in member
        assert set(member.keys()) == LEAGUE_MEMBER_FIELDS


async def test_get_league_zones_at_size_30(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    store = await make_store(conn)
    user_ids = await _seed_scored_league(
        conn, store_id=store.id, division=DIVISION_MIDDLE, count=30
    )

    top = (await client.get(f"/api/v1/users/{user_ids[6]}/league")).json()
    middle = (await client.get(f"/api/v1/users/{user_ids[7]}/league")).json()
    bottom = (await client.get(f"/api/v1/users/{user_ids[25]}/league")).json()

    assert top["my_rank"] == 7 and top["my_zone"] == "promotion"
    assert middle["my_rank"] == 8 and middle["my_zone"] == "safe"
    assert bottom["my_rank"] == 26 and bottom["my_zone"] == "demotion"
    assert top["promotion_cutoff"] == 7
    assert top["demotion_cutoff"] == 26


async def test_get_league_zones_demotion_bottom_five_at_size_12(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    store = await make_store(conn)
    user_ids = await _seed_scored_league(
        conn, store_id=store.id, division=DIVISION_MIDDLE, count=12
    )

    promoted = (await client.get(f"/api/v1/users/{user_ids[6]}/league")).json()
    demoted = (await client.get(f"/api/v1/users/{user_ids[7]}/league")).json()

    assert promoted["my_rank"] == 7 and promoted["my_zone"] == "promotion"
    assert demoted["my_rank"] == 8 and demoted["my_zone"] == "demotion"


async def test_get_league_division_1_never_demotes(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    store = await make_store(conn)
    user_ids = await _seed_scored_league(conn, store_id=store.id, division=1, count=30)

    last = (await client.get(f"/api/v1/users/{user_ids[29]}/league")).json()

    assert last["my_rank"] == 30
    assert last["my_zone"] == "safe"


async def test_get_league_division_5_never_promotes(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    store = await make_store(conn)
    user_ids = await _seed_scored_league(conn, store_id=store.id, division=5, count=30)

    first = (await client.get(f"/api/v1/users/{user_ids[0]}/league")).json()

    assert first["my_rank"] == 1
    assert first["my_zone"] == "safe"


async def test_get_league_house_aggregate_single_store_district(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    store = await make_store(conn)
    user_ids = await _seed_scored_league(conn, store_id=store.id, division=DIVISION_MIDDLE, count=2)

    response = await client.get(f"/api/v1/users/{user_ids[0]}/league")

    house = response.json()["house"]
    assert house["store_name"] == store.name
    assert house["district_rank"] == 1
    assert house["district_size"] == 1
    assert isinstance(house["avg_savings_rate"], float)


async def test_get_league_unknown_user_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users/999999/league")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "user_not_found"


async def test_get_league_house_aggregate_ranks_stores_within_district(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    store_a = await make_store(conn, district="Центр")
    store_b = await make_store(conn, district="Центр")
    store_c = await make_store(conn, district="Юг")
    league_a = await make_league(conn, store_id=store_a.id, division=DIVISION_MIDDLE)
    league_b = await make_league(conn, store_id=store_b.id, division=DIVISION_MIDDLE)
    league_c = await make_league(conn, store_id=store_c.id, division=DIVISION_MIDDLE)

    member_a = await make_user(conn)
    await make_league_member(conn, league_a.id, member_a.id)
    await make_receipt(
        conn, member_a.id, store_id=store_a.id, purchased_at=NOW, items=HIGH_DISCOUNT_ITEM
    )

    member_b = await make_user(conn)
    await make_league_member(conn, league_b.id, member_b.id)
    await make_receipt(
        conn, member_b.id, store_id=store_b.id, purchased_at=NOW, items=LOW_DISCOUNT_ITEM
    )
    member_b_no_history = await make_user(conn)
    await make_league_member(conn, league_b.id, member_b_no_history.id)

    member_c = await make_user(conn)
    await make_league_member(conn, league_c.id, member_c.id)
    await make_receipt(
        conn, member_c.id, store_id=store_c.id, purchased_at=NOW, items=HIGH_DISCOUNT_ITEM
    )

    house_a = (await client.get(f"/api/v1/users/{member_a.id}/league")).json()["house"]
    house_b = (await client.get(f"/api/v1/users/{member_b.id}/league")).json()["house"]

    assert house_a["avg_savings_rate"] == pytest.approx(0.75)
    assert house_a["district_rank"] == 1
    assert house_a["district_size"] == 2
    assert house_b["avg_savings_rate"] == pytest.approx(0.05)
    assert house_b["district_rank"] == 2
    assert house_b["district_size"] == 2


async def test_get_league_new_user_gets_solo_league_with_zero_score(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    await make_store(conn)
    user = await make_user(conn)

    response = await client.get(f"/api/v1/users/{user.id}/league")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == LEAGUE_RESPONSE_FIELDS
    assert body["division"] == 1
    assert body["size"] == 1
    assert body["my_rank"] == 1
    assert body["my_score"] == 0
    assert body["my_zone"] == "promotion"
    assert len(body["members"]) == 1
    assert set(body["members"][0].keys()) == LEAGUE_MEMBER_FIELDS
    assert body["members"][0]["is_me"] is True
    assert body["members"][0]["score"] == 0
