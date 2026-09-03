from collections.abc import Callable
from datetime import datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient
from psycopg import AsyncConnection
from psycopg.types.json import Jsonb

from app.features.antifraud import database as antifraud_db
from app.features.antifraud.models import FraudDecision, FraudSignal
from app.features.challenges import database as challenges_db
from app.features.pm import database as pm_db
from app.features.pm.models import MechanicDecisionReasons
from app.features.users.models import UserRow
from tests.e2e.pm.data import (
    FRAUD_CHECK_FIELDS,
    HERO_CHALLENGE_FIELDS,
    HERO_ECONOMICS,
    LEDGER_ENTRY_FIELDS,
    NOW,
    PM_USER_RESPONSE_FIELDS,
    USER_FEATURES_FIELDS,
)
from tests.factories import make_challenge, make_store, make_user, make_user_features


async def _seed_full_history(conn: AsyncConnection) -> UserRow:
    user = await make_user(conn)
    store = await make_store(conn)
    await make_user_features(
        conn,
        user.id,
        recency_days=5,
        cadence_days=Decimal("3.50"),
        favourite_store_id=store.id,
        category_affinity=Jsonb({"dairy": {"share": 0.3, "visits": 6, "cadence_days": 5.0}}),
    )
    hero = await make_challenge(
        conn, user.id, is_hero=True, status="active", economics=HERO_ECONOMICS, reward_points=30
    )
    await challenges_db.insert_reward_ledger_entry(
        conn,
        user_id=user.id,
        kind="challenge",
        xp_delta=50,
        points_delta=30,
        ref_type="challenge",
        ref_id=hero.id,
    )
    await challenges_db.insert_reward_ledger_entry(
        conn,
        user_id=user.id,
        kind="receipt_xp",
        xp_delta=5,
        points_delta=0,
        ref_type=None,
        ref_id=None,
    )
    await antifraud_db.insert_fraud_check(
        conn,
        subject_type="receipt",
        subject_id=1,
        user_id=user.id,
        decision=FraudDecision(
            score=0.6,
            decision="hold",
            signals=[FraudSignal(code="burst_same_store", weight=0.25, strong=True, detail="d")],
        ),
    )
    await pm_db.insert_mechanic_decision(
        conn,
        user_id=user.id,
        mechanic="league",
        reasons=MechanicDecisionReasons(
            reason="Ты уже опытный",
            completed_challenges_count=5,
            has_league=True,
            social_propensity=Decimal("0.900"),
        ),
    )
    return user


async def test_get_pm_user_with_full_history_matches_contract(
    client: AsyncClient, conn: AsyncConnection, freeze_time: Callable[[datetime], None]
) -> None:
    freeze_time(NOW)
    user = await _seed_full_history(conn)

    response = await client.get(f"/api/v1/pm/users/{user.id}")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == PM_USER_RESPONSE_FIELDS
    assert set(body["features"].keys()) == USER_FEATURES_FIELDS
    assert body["features"]["cadence_days"] == 3.5
    assert body["hero_challenge"] is not None
    assert set(body["hero_challenge"].keys()) == HERO_CHALLENGE_FIELDS
    assert body["hero_challenge"]["copy_source"] == "template"
    assert body["hero_challenge"]["economics"]["expected_incremental_margin"] == 90.0
    assert body["rewards_total_points"] == 30
    assert body["rewards_total_xp"] == 55
    assert body["expected_incremental_margin_month"] == 90.0
    assert body["recommended_mechanic"] == {
        "mechanic": "league",
        "reasons": [
            "Ты уже опытный",
            "выполнено челленджей: 5",
            "есть лига: True",
            "склонность делиться: 0.900",
        ],
    }
    assert len(body["fraud_checks"]) == 1
    assert set(body["fraud_checks"][0].keys()) == FRAUD_CHECK_FIELDS
    assert len(body["ledger"]) == 2
    assert set(body["ledger"][0].keys()) == LEDGER_ENTRY_FIELDS


async def test_get_pm_user_without_history_returns_zeroed_fields_not_500(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    user = await make_user(conn)

    response = await client.get(f"/api/v1/pm/users/{user.id}")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == PM_USER_RESPONSE_FIELDS
    assert set(body["features"].keys()) == USER_FEATURES_FIELDS
    assert body["features"]["cadence_days"] == 0
    assert body["features"]["favourite_store_id"] == 0
    assert body["features"]["recency_days"] == 999
    assert body["hero_challenge"] is None
    assert body["rewards_total_points"] == 0
    assert body["rewards_total_xp"] == 0
    assert body["expected_incremental_margin_month"] == 0
    assert body["fraud_checks"] == []
    assert body["ledger"] == []
    assert body["recommended_mechanic"] == {
        "mechanic": "challenge",
        "reasons": ["ещё не заходил на Home"],
    }


async def test_get_pm_user_for_unknown_user_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/pm/users/999999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "user_not_found"


async def _seed_fraud_checks(conn: AsyncConnection) -> tuple[UserRow, UserRow]:
    first = await make_user(conn)
    second = await make_user(conn)
    decisions: list[tuple[UserRow, str]] = [
        (first, "approve"),
        (first, "hold"),
        (second, "block"),
    ]
    for index, (user, decision) in enumerate(decisions):
        await antifraud_db.insert_fraud_check(
            conn,
            subject_type="receipt",
            subject_id=index,
            user_id=user.id,
            decision=FraudDecision(score=0.5, decision=decision, signals=[]),  # type: ignore[arg-type]
        )
    return first, second


async def test_list_fraud_checks_without_filter_returns_all(
    client: AsyncClient, conn: AsyncConnection
) -> None:
    await _seed_fraud_checks(conn)

    response = await client.get("/api/v1/pm/fraud")

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 3
    assert set(items[0].keys()) == FRAUD_CHECK_FIELDS


DECISION_FILTER_CASES: list[tuple[str, int]] = [("approve", 1), ("hold", 1), ("block", 1)]


@pytest.mark.parametrize(("decision", "expected_count"), DECISION_FILTER_CASES)
async def test_list_fraud_checks_filters_by_decision(
    client: AsyncClient, conn: AsyncConnection, decision: str, expected_count: int
) -> None:
    await _seed_fraud_checks(conn)

    response = await client.get("/api/v1/pm/fraud", params={"decision": decision})

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == expected_count
    assert all(item["decision"] == decision for item in items)


async def test_list_fraud_checks_respects_limit(client: AsyncClient, conn: AsyncConnection) -> None:
    await _seed_fraud_checks(conn)

    response = await client.get("/api/v1/pm/fraud", params={"limit": 1})

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
