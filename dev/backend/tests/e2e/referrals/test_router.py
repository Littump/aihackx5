from collections.abc import Callable
from datetime import datetime, timedelta

from httpx import AsyncClient
from psycopg import AsyncConnection

from app.game_rules import REFERRAL_PAID_PER_MONTH, REFERRAL_REWARDS
from tests.e2e.referrals.data import (
    NOW,
    REFERRAL_INVITEE_FIELDS,
    REFERRAL_RESPONSE_FIELDS,
    REFERRER_CREATED_AT,
)
from tests.factories import make_referral, make_user

NEW_REWARD = REFERRAL_REWARDS["new"]
DORMANT_REWARD = REFERRAL_REWARDS["dormant"]


async def test_get_referral_happy_path_matches_contract_fields(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn, created_at=REFERRER_CREATED_AT)

    response = await client.get(f"/api/v1/users/{referrer.id}/referral")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == REFERRAL_RESPONSE_FIELDS
    assert body["code"] == referrer.referral_code
    assert body["link"].endswith(referrer.referral_code)
    assert body["referrer_reward_points"] == NEW_REWARD["referrer_reward_points"]
    assert body["referee_reward_points_new"] == NEW_REWARD["referee_first_purchase_points"]
    assert body["referee_reward_points_dormant"] == DORMANT_REWARD["referee_first_purchase_points"]
    assert body["invitees"] == []
    assert body["paid_this_month"] == 0
    assert body["paid_limit_month"] == REFERRAL_PAID_PER_MONTH


async def test_get_referral_invitees_are_labelled_in_order_without_identity(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn, created_at=REFERRER_CREATED_AT)
    first_invitee = await make_user(conn, created_at=REFERRER_CREATED_AT)
    second_invitee = await make_user(conn, created_at=REFERRER_CREATED_AT)
    await make_referral(
        conn, referrer.id, first_invitee.id, created_at=NOW - timedelta(days=2), status="pending"
    )
    await make_referral(
        conn,
        referrer.id,
        second_invitee.id,
        created_at=NOW - timedelta(days=1),
        status="rewarded",
        referrer_reward_points=NEW_REWARD["referrer_reward_points"],
        decided_at=NOW,
    )

    response = await client.get(f"/api/v1/users/{referrer.id}/referral")

    body = response.json()
    assert len(body["invitees"]) == 2
    for invitee in body["invitees"]:
        assert set(invitee.keys()) == REFERRAL_INVITEE_FIELDS
        assert "id" not in invitee
        assert "pseudonym" not in invitee
    assert body["invitees"][0]["label"] == "Сосед №1"
    assert body["invitees"][1]["label"] == "Сосед №2"
    assert body["invitees"][0]["status"] == "pending"
    assert body["invitees"][0]["reward_points"] == 0
    assert body["invitees"][1]["status"] == "rewarded"
    assert body["invitees"][1]["reward_points"] == NEW_REWARD["referrer_reward_points"]
    assert body["paid_this_month"] == 1


async def test_get_referral_unknown_user_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users/999999/referral")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "user_not_found"
