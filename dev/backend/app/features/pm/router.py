from typing import Literal

from fastapi import APIRouter, Query

from app.core.db import Conn
from app.features.pm import service
from app.features.pm.dto import (
    ChallengeDetail,
    EvalRun,
    FraudCheck,
    FraudCheckListResponse,
    PmUserResponse,
    RecommendedMechanic,
    RewardLedgerEntry,
    SimulationRun,
    UserFeatures,
    UserSummary,
)

router = APIRouter(tags=["pm"])


@router.get("/pm/users/{user_id}", response_model=PmUserResponse)
async def get_pm_user(user_id: int, conn: Conn) -> PmUserResponse:
    card = await service.get_user_card(conn, user_id)
    hero = card.hero_challenge
    return PmUserResponse(
        user=UserSummary(
            id=card.user.id,
            pseudonym=card.user.pseudonym,
            segment=card.user.segment,
            level=card.level,
        ),
        features=UserFeatures.model_validate(card.features),
        recommended_mechanic=RecommendedMechanic.model_validate(card.recommended_mechanic),
        hero_challenge=ChallengeDetail.model_validate(hero) if hero is not None else None,
        rewards_total_points=card.rewards_total_points,
        rewards_total_xp=card.rewards_total_xp,
        expected_incremental_margin_month=float(card.expected_incremental_margin_month),
        fraud_checks=[FraudCheck.model_validate(row) for row in card.fraud_checks],
        ledger=[RewardLedgerEntry.model_validate(entry) for entry in card.ledger],
    )


@router.get("/pm/fraud", response_model=FraudCheckListResponse)
async def list_fraud_checks(
    conn: Conn,
    limit: int = Query(default=50, ge=1, le=500),
    decision: Literal["approve", "hold", "block"] | None = Query(default=None),
) -> FraudCheckListResponse:
    rows = await service.list_fraud_checks(conn, limit=limit, decision=decision)
    return FraudCheckListResponse(items=[FraudCheck.model_validate(row) for row in rows])


@router.get("/pm/simulation/latest", response_model=SimulationRun)
async def get_latest_simulation(conn: Conn) -> SimulationRun:
    row = await service.get_latest_simulation(conn)
    return SimulationRun.model_validate(row)


@router.get("/pm/eval/latest", response_model=EvalRun)
async def get_latest_eval(conn: Conn) -> EvalRun:
    row = await service.get_latest_eval(conn)
    return EvalRun.model_validate(row)
