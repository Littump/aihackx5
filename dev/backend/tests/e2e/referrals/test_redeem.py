from collections.abc import Callable
from datetime import datetime

from httpx import AsyncClient
from psycopg import AsyncConnection

from app.features.referrals import database as referrals_db
from app.game_rules import REFERRAL_PAID_PER_MONTH, REFERRAL_PAID_PER_YEAR
from tests.e2e.referrals.data import NOW, REDEEM_RESPONSE_FIELDS, REFERRER_CREATED_AT
from tests.factories import make_referral, make_user


async def test_redeem_happy_path_creates_referee_and_links_referral(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn, created_at=REFERRER_CREATED_AT)

    response = await client.post("/api/v1/referrals/redeem", json={"code": referrer.referral_code})

    assert response.status_code == 201
    body = response.json()
    assert set(body.keys()) == REDEEM_RESPONSE_FIELDS
    assert body["referrer_user_id"] == referrer.id
    assert body["referee_kind"] == "new"
    assert body["status"] == "pending"
    referee_id = body["referee_user_id"]
    referral = await referrals_db.get_referral_by_referee(conn, referee_user_id=referee_id)
    assert referral is not None
    assert referral.referrer_user_id == referrer.id
    assert referral.referee_kind == "new"
    assert referral.status == "pending"


async def test_redeem_unknown_code_returns_404(client: AsyncClient) -> None:
    response = await client.post("/api/v1/referrals/redeem", json={"code": "UNKNOWN"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "referrer_not_found"


async def test_redeem_empty_body_returns_422(client: AsyncClient) -> None:
    response = await client.post("/api/v1/referrals/redeem", json={})

    assert response.status_code == 422


async def test_redeem_year_limit_reached_returns_409(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn, created_at=REFERRER_CREATED_AT)
    for _ in range(REFERRAL_PAID_PER_YEAR):
        filler = await make_user(conn, created_at=REFERRER_CREATED_AT)
        await make_referral(
            conn,
            referrer.id,
            filler.id,
            created_at=REFERRER_CREATED_AT,
            status="rewarded",
            decided_at=NOW,
        )

    response = await client.post("/api/v1/referrals/redeem", json={"code": referrer.referral_code})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "referral_limit_reached"


async def test_redeem_month_limit_reached_does_not_block_redeem(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn, created_at=REFERRER_CREATED_AT)
    for _ in range(REFERRAL_PAID_PER_MONTH):
        filler = await make_user(conn, created_at=REFERRER_CREATED_AT)
        await make_referral(
            conn,
            referrer.id,
            filler.id,
            created_at=REFERRER_CREATED_AT,
            status="rewarded",
            decided_at=NOW,
        )

    response = await client.post("/api/v1/referrals/redeem", json={"code": referrer.referral_code})

    assert response.status_code == 201


async def test_redeem_with_colliding_pseudonym_returns_structured_error(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    referrer = await make_user(conn)
    existing = await make_user(conn, pseudonym="Существующий Домовой")

    response = await client.post(
        "/api/v1/referrals/redeem",
        json={"code": referrer.referral_code, "pseudonym": existing.pseudonym},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "pseudonym_taken"
