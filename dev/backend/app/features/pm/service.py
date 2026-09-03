from decimal import Decimal

from psycopg import AsyncConnection

from app.core.errors import AppError
from app.core.models import AppModel
from app.features.antifraud import service as antifraud_service
from app.features.antifraud.models import FraudCheckRow, FraudDecisionKind
from app.features.challenges import service as challenges_service
from app.features.challenges.models import ChallengeRow, RewardLedgerEntry
from app.features.domovoy import service as domovoy_service
from app.features.pm import database
from app.features.pm.models import (
    EvalRunRow,
    JsonValue,
    Mechanic,
    MechanicDecisionContext,
    MechanicDecisionReasons,
    MechanicDecisionRow,
    RecommendedMechanicCard,
    SimulationRunResults,
    SimulationRunRow,
)
from app.features.user_features import service as user_features_service
from app.features.user_features.models import UserFeaturesRow
from app.features.users import service as users_service
from app.features.users.models import UserRow
from app.game_rules import level_for_xp

FRAUD_CHECKS_LIMIT = 10
LEDGER_LIMIT = 20
NO_HISTORY_REASON = "ещё не заходил на Home"


class PmUserCard(AppModel):
    user: UserRow
    level: int
    features: UserFeaturesRow
    recommended_mechanic: RecommendedMechanicCard
    hero_challenge: ChallengeRow | None
    rewards_total_points: int
    rewards_total_xp: int
    expected_incremental_margin_month: Decimal
    fraud_checks: list[FraudCheckRow]
    ledger: list[RewardLedgerEntry]


async def record_decision(
    conn: AsyncConnection,
    *,
    user_id: int,
    mechanic: Mechanic,
    reason: str,
    context: MechanicDecisionContext,
) -> MechanicDecisionRow:
    reasons = MechanicDecisionReasons(
        reason=reason,
        completed_challenges_count=context.completed_challenges_count,
        has_league=context.has_league,
        social_propensity=context.social_propensity,
    )
    return await database.insert_mechanic_decision(
        conn, user_id=user_id, mechanic=mechanic, reasons=reasons
    )


async def get_user_card(conn: AsyncConnection, user_id: int) -> PmUserCard:
    user = await users_service.get_user(conn, user_id)
    domovoy_state = await domovoy_service.get_state(conn, user_id)
    features = await user_features_service.get(conn, user_id)
    hero_challenge = (await challenges_service.get_list(conn, user_id)).hero
    totals = await challenges_service.sum_ledger_for_user(conn, user_id)
    expected_margin = await challenges_service.sum_expected_margin_for_month(conn, user_id)
    fraud_checks = await antifraud_service.list_for_user(conn, user_id, limit=FRAUD_CHECKS_LIMIT)
    ledger = await challenges_service.list_ledger_for_user(conn, user_id, limit=LEDGER_LIMIT)
    return PmUserCard(
        user=user,
        level=level_for_xp(domovoy_state.xp),
        features=_features_with_defaults(features),
        recommended_mechanic=await _recommended_mechanic(conn, user_id),
        hero_challenge=hero_challenge,
        rewards_total_points=totals.points,
        rewards_total_xp=totals.xp,
        expected_incremental_margin_month=expected_margin,
        fraud_checks=fraud_checks,
        ledger=ledger,
    )


async def list_fraud_checks(
    conn: AsyncConnection, *, limit: int, decision: FraudDecisionKind | None
) -> list[FraudCheckRow]:
    return await antifraud_service.list_all(conn, limit=limit, decision=decision)


async def get_latest_simulation(conn: AsyncConnection) -> SimulationRunRow:
    row = await database.get_latest_simulation_run(conn)
    if row is None:
        raise AppError("simulation_not_found", "симуляция ещё не запускалась", 404)
    return row


async def get_latest_eval(conn: AsyncConnection) -> EvalRunRow:
    row = await database.get_latest_eval_run(conn)
    if row is None:
        raise AppError("eval_not_found", "eval ещё не запускался", 404)
    return row


async def record_simulation_run(
    conn: AsyncConnection,
    *,
    params: dict[str, JsonValue],
    results: SimulationRunResults,
) -> SimulationRunRow:
    return await database.insert_simulation_run(conn, params=params, results=results)


async def record_eval_run(
    conn: AsyncConnection,
    *,
    profiles: int,
    hit_rate: Decimal,
    invalid_rate: Decimal,
    fallback_rate: Decimal,
    economics_pass_rate: Decimal,
    details: list[dict[str, JsonValue]],
) -> EvalRunRow:
    return await database.insert_eval_run(
        conn,
        profiles=profiles,
        hit_rate=hit_rate,
        invalid_rate=invalid_rate,
        fallback_rate=fallback_rate,
        economics_pass_rate=economics_pass_rate,
        details=details,
    )


def _features_with_defaults(features: UserFeaturesRow) -> UserFeaturesRow:
    cadence = features.cadence_days if features.cadence_days is not None else Decimal("0")
    store_id = features.favourite_store_id if features.favourite_store_id is not None else 0
    return features.model_copy(update={"cadence_days": cadence, "favourite_store_id": store_id})


async def _recommended_mechanic(conn: AsyncConnection, user_id: int) -> RecommendedMechanicCard:
    row = await database.get_latest_mechanic_decision(conn, user_id)
    if row is None:
        return RecommendedMechanicCard(mechanic="challenge", reasons=[NO_HISTORY_REASON])
    return RecommendedMechanicCard(mechanic=row.mechanic, reasons=_reasons_from_row(row))


def _reasons_from_row(row: MechanicDecisionRow) -> list[str]:
    reasons = row.reasons
    return [
        reasons.reason,
        f"выполнено челленджей: {reasons.completed_challenges_count}",
        f"есть лига: {reasons.has_league}",
        f"склонность делиться: {reasons.social_propensity}",
    ]
