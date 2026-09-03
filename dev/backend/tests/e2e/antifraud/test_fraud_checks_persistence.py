from psycopg import AsyncConnection

from app.features.antifraud import database as antifraud_db
from app.features.antifraud.models import FraudDecision, FraudSignal
from tests.factories import make_referral, make_user


async def test_insert_fraud_check_round_trips_signal_fields_with_correct_types(
    conn: AsyncConnection,
) -> None:
    user = await make_user(conn)
    decision = FraudDecision(
        score=0.6,
        decision="hold",
        signals=[
            FraudSignal(
                code="burst_same_store",
                weight=0.25,
                strong=True,
                detail="4 чеков в одном магазине за 60 минут",
            ),
            FraudSignal(
                code="basket_monotony",
                weight=0.15,
                strong=False,
                detail="3 чека подряд с одинаковым составом и суммой",
            ),
        ],
    )

    row = await antifraud_db.insert_fraud_check(
        conn, subject_type="receipt", subject_id=42, user_id=user.id, decision=decision
    )

    assert len(row.signals) == 2
    burst = next(s for s in row.signals if s.code == "burst_same_store")
    assert burst.weight == 0.25
    assert isinstance(burst.weight, float)
    assert burst.strong is True
    assert isinstance(burst.strong, bool)
    assert burst.detail == "4 чеков в одном магазине за 60 минут"
    assert row.score == 0.6
    assert row.decision == "hold"


async def test_insert_fraud_check_round_trips_empty_signals_for_approve(
    conn: AsyncConnection,
) -> None:
    user = await make_user(conn)
    decision = FraudDecision(score=0.0, decision="approve", signals=[])

    row = await antifraud_db.insert_fraud_check(
        conn, subject_type="receipt", subject_id=1, user_id=user.id, decision=decision
    )

    assert row.signals == []
    assert row.score == 0.0


async def test_insert_fraud_check_uses_referral_subject_and_referrer_as_user_id(
    conn: AsyncConnection,
) -> None:
    referrer = await make_user(conn)
    referee = await make_user(conn)
    referral = await make_referral(conn, referrer.id, referee.id)
    decision = FraudDecision(score=0.3, decision="approve", signals=[])

    row = await antifraud_db.insert_fraud_check(
        conn,
        subject_type="referral",
        subject_id=referral.id,
        user_id=referrer.id,
        decision=decision,
    )

    assert row.subject_type == "referral"
    assert row.subject_id == referral.id
    assert row.user_id == referrer.id
