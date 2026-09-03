from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from psycopg import AsyncConnection

from app.game_rules import REFERRAL_PAID_PER_MONTH, XP_ACHIEVEMENT
from tests.factories import make_domovoy_state, make_referral, make_store, make_user

NOW = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)
ITEM_PAYLOAD = [
    {
        "product_name": "Молоко",
        "category": "dairy",
        "qty": 1,
        "regular_price": 100.0,
        "paid_price": 90.0,
    }
]


QUALIFYING_ITEM_PAYLOAD = [
    {
        "product_name": "Крупная покупка",
        "category": "grocery",
        "qty": 1,
        "regular_price": 600.0,
        "paid_price": 600.0,
    }
]


def _payload(user_id: int, store_id: int, purchased_at: datetime = NOW) -> dict[str, object]:
    return {
        "user_id": user_id,
        "store_id": store_id,
        "purchased_at": purchased_at.isoformat(),
        "items": ITEM_PAYLOAD,
    }


def _qualifying_payload(
    user_id: int, store_id: int, purchased_at: datetime = NOW
) -> dict[str, object]:
    return {
        "user_id": user_id,
        "store_id": store_id,
        "purchased_at": purchased_at.isoformat(),
        "items": QUALIFYING_ITEM_PAYLOAD,
    }


async def _achievement_count(conn: AsyncConnection, *, user_id: int, code: str) -> int:
    cursor = await conn.execute(
        "SELECT count(*) FROM achievements WHERE user_id = %s AND code = %s", (user_id, code)
    )
    row = await cursor.fetchone()
    assert row is not None
    return int(row[0])


async def test_first_counted_receipt_reports_unlocked_achievements_in_response(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    store = await make_store(conn)

    response = await client.post("/api/v1/receipts", json=_payload(user.id, store.id))

    assert response.status_code == 201
    body = response.json()
    assert body["achievements_unlocked"] != []
    assert "first_receipt" in body["achievements_unlocked"]

    cursor = await conn.execute("SELECT count(*) FROM achievements WHERE user_id = %s", (user.id,))
    row = await cursor.fetchone()
    assert row is not None
    assert row[0] == len(body["achievements_unlocked"])


async def test_league_top3_should_not_unlock_on_first_receipt_in_a_brand_new_solo_league(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    store = await make_store(conn)

    response = await client.post("/api/v1/receipts", json=_payload(user.id, store.id))

    assert response.status_code == 201
    body = response.json()
    # DEF-BE021-1: соло-лига даёт тривиальный rank=1 сразу, "Топ-3 недели" не должен так открываться
    assert "league_top3" not in body["achievements_unlocked"]


async def test_referral_redeem_then_two_purchases_unlocks_neighbour_for_referrer_only(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn)
    store = await make_store(conn)

    redeem_response = await client.post(
        "/api/v1/referrals/redeem", json={"code": referrer.referral_code}
    )
    assert redeem_response.status_code == 201
    referee_id = redeem_response.json()["referee_user_id"]

    first_response = await client.post(
        "/api/v1/receipts", json=_qualifying_payload(referee_id, store.id, NOW)
    )
    assert first_response.json()["referral_status"] == "first_purchase"

    second_at = NOW + timedelta(days=7)
    freeze_time(second_at)
    second_response = await client.post(
        "/api/v1/receipts", json=_qualifying_payload(referee_id, store.id, second_at)
    )
    assert second_response.status_code == 201
    assert second_response.json()["referral_status"] == "rewarded"

    referrer_achievements = await client.get(f"/api/v1/users/{referrer.id}/achievements")
    referee_achievements = await client.get(f"/api/v1/users/{referee_id}/achievements")
    assert "neighbour" in [item["code"] for item in referrer_achievements.json()["items"]]
    assert "neighbour" not in [item["code"] for item in referee_achievements.json()["items"]]
    assert await _achievement_count(conn, user_id=referrer.id, code="neighbour") == 1
    assert await _achievement_count(conn, user_id=referee_id, code="neighbour") == 0

    ledger_cursor = await conn.execute(
        "SELECT kind, xp_delta FROM reward_ledger WHERE user_id = %s ORDER BY created_at, id",
        (referrer.id,),
    )
    ledger = await ledger_cursor.fetchall()
    assert ("achievement", XP_ACHIEVEMENT) in [(row[0], row[1]) for row in ledger]


async def test_receipt_achievements_unlocked_should_not_leak_referrers_neighbour_code(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn)
    store = await make_store(conn)
    redeem_response = await client.post(
        "/api/v1/referrals/redeem", json={"code": referrer.referral_code}
    )
    referee_id = redeem_response.json()["referee_user_id"]
    await client.post("/api/v1/receipts", json=_qualifying_payload(referee_id, store.id, NOW))

    second_at = NOW + timedelta(days=7)
    freeze_time(second_at)
    second_response = await client.post(
        "/api/v1/receipts", json=_qualifying_payload(referee_id, store.id, second_at)
    )

    assert second_response.json()["referral_status"] == "rewarded"
    # DEF-BE021-2: neighbour достаётся рефереру, но код "утекает" в ответ чека реферала
    assert "neighbour" not in second_response.json()["achievements_unlocked"]


async def test_neighbour_does_not_unlock_when_referrer_hit_monthly_limit(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    referrer = await make_user(conn)
    store = await make_store(conn)
    for _i in range(REFERRAL_PAID_PER_MONTH):
        referee = await make_user(conn)
        await make_referral(
            conn,
            referrer.id,
            referee.id,
            status="rewarded",
            decided_at=NOW,
            referrer_reward_points=150,
        )
    limited_referee = await make_user(conn)
    await make_referral(
        conn, referrer.id, limited_referee.id, status="first_purchase", first_purchase_at=NOW
    )

    second_at = NOW + timedelta(days=7)
    freeze_time(second_at)
    response = await client.post(
        "/api/v1/receipts", json=_qualifying_payload(limited_referee.id, store.id, second_at)
    )

    assert response.status_code == 201
    assert response.json()["referral_status"] == "qualified"
    assert await _achievement_count(conn, user_id=referrer.id, code="neighbour") == 0


async def test_streak_4_double_trigger_via_real_receipts_does_not_duplicate(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await make_user(conn)
    store = await make_store(conn)
    await make_domovoy_state(conn, user.id, streak_weeks=4)

    first_response = await client.post("/api/v1/receipts", json=_payload(user.id, store.id))
    second_at = NOW + timedelta(hours=1)
    freeze_time(second_at)
    second_response = await client.post(
        "/api/v1/receipts", json=_payload(user.id, store.id, second_at)
    )

    assert "streak_4" in first_response.json()["achievements_unlocked"]
    assert "streak_4" not in second_response.json()["achievements_unlocked"]
    assert await _achievement_count(conn, user_id=user.id, code="streak_4") == 1

    ledger_cursor = await conn.execute(
        "SELECT count(*) FROM reward_ledger l JOIN achievements a ON a.id = l.ref_id "
        "WHERE l.user_id = %s AND l.kind = 'achievement' AND l.xp_delta = %s "
        "AND a.code = 'streak_4'",
        (user.id, XP_ACHIEVEMENT),
    )
    ledger_row = await ledger_cursor.fetchone()
    assert ledger_row is not None
    assert ledger_row[0] == 1
