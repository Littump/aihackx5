from httpx import AsyncClient
from psycopg import AsyncConnection

from app.features.antifraud import database as antifraud_db
from app.features.antifraud.models import FraudDecision
from app.features.challenges import database as challenges_db
from tests.factories import make_user

LEDGER_ENTRIES_COUNT = 25
FRAUD_CHECKS_COUNT = 12
LEDGER_LIMIT = 20
FRAUD_CHECKS_LIMIT = 10


async def test_rewards_total_counts_all_ledger_entries_but_list_is_capped(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)
    for _ in range(LEDGER_ENTRIES_COUNT):
        await challenges_db.insert_reward_ledger_entry(
            conn,
            user_id=user.id,
            kind="receipt_xp",
            xp_delta=1,
            points_delta=2,
            ref_type=None,
            ref_id=None,
        )

    response = await client.get(f"/api/v1/pm/users/{user.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["rewards_total_xp"] == LEDGER_ENTRIES_COUNT
    assert body["rewards_total_points"] == LEDGER_ENTRIES_COUNT * 2
    assert len(body["ledger"]) == LEDGER_LIMIT


async def test_fraud_checks_list_is_capped_at_10_most_recent(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)
    for index in range(FRAUD_CHECKS_COUNT):
        await antifraud_db.insert_fraud_check(
            conn,
            subject_type="receipt",
            subject_id=index,
            user_id=user.id,
            decision=FraudDecision(score=0.1, decision="approve", signals=[]),
        )

    response = await client.get(f"/api/v1/pm/users/{user.id}")

    assert response.status_code == 200
    assert len(response.json()["fraud_checks"]) == FRAUD_CHECKS_LIMIT
