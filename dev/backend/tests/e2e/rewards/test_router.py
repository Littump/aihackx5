from collections.abc import Callable
from datetime import datetime

from httpx import AsyncClient
from psycopg import AsyncConnection

from app.features.challenges import database as challenges_db
from app.features.users.models import UserRow
from tests.e2e.rewards.data import (
    NOW,
    REWARD_EVENT_FIELDS,
    REWARD_RULE_FIELDS,
    REWARDS_FIELDS,
)
from tests.factories import make_challenge, make_domovoy_state, make_receipt, make_user


async def _seed_rewards(conn: AsyncConnection) -> UserRow:
    user = await make_user(conn)
    await make_domovoy_state(conn, user.id, xp=160, level=2)
    challenge = await make_challenge(
        conn, user.id, status="completed", reward_points=30, copy_title="Молочный ритм"
    )
    receipt = await make_receipt(conn, user.id, purchased_at=NOW, points_earned=25, points_spent=5)
    await challenges_db.insert_reward_ledger_entry(
        conn,
        user_id=user.id,
        kind="receipt_xp",
        xp_delta=10,
        points_delta=0,
        ref_type="receipt",
        ref_id=receipt.id,
    )
    await challenges_db.insert_reward_ledger_entry(
        conn,
        user_id=user.id,
        kind="challenge",
        xp_delta=50,
        points_delta=30,
        ref_type="challenge",
        ref_id=challenge.id,
    )
    return user


async def test_get_rewards_returns_balance_history_and_rules(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await _seed_rewards(conn)

    response = await client.get(f"/api/v1/users/{user.id}/rewards")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == REWARDS_FIELDS
    assert body["points_from_rewards"] == 30
    assert body["points_from_receipts"] == 20
    assert body["points_balance"] == 50
    assert body["xp"] == 160
    assert body["level"] == 2
    for event in body["history"]:
        assert set(event.keys()) == REWARD_EVENT_FIELDS
    for rule in body["rules"]:
        assert set(rule.keys()) == REWARD_RULE_FIELDS


async def test_get_rewards_history_explains_each_entry(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await _seed_rewards(conn)

    response = await client.get(f"/api/v1/users/{user.id}/rewards")

    history = response.json()["history"]
    assert [event["kind"] for event in history] == ["challenge", "receipt_xp"]
    assert history[0]["title"] == "Цель недели выполнена"
    assert history[0]["detail"] == "Молочный ритм"
    assert history[0]["points_delta"] == 30
    assert history[1]["detail"] == "Чек на 350 ₽"


async def test_get_rewards_limit_caps_history(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await _seed_rewards(conn)

    response = await client.get(f"/api/v1/users/{user.id}/rewards", params={"limit": 1})

    assert response.status_code == 200
    assert len(response.json()["history"]) == 1


async def test_get_rewards_rejects_limit_out_of_range(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await _seed_rewards(conn)

    response = await client.get(f"/api/v1/users/{user.id}/rewards", params={"limit": 0})

    assert response.status_code == 422


async def test_get_rewards_unknown_user_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users/999999/rewards")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "user_not_found"


async def test_get_rewards_without_history_returns_zero_balance(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)

    response = await client.get(f"/api/v1/users/{user.id}/rewards")

    body = response.json()
    assert body["points_balance"] == 0
    assert body["history"] == []
    assert body["rules"] != []
