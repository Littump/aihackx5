from fastapi import APIRouter, Query

from app.core.db import Conn
from app.features.users import home, service
from app.features.users.dto import (
    ChallengeDetail,
    DomovoyState,
    HomeResponse,
    RecommendedMechanic,
    ReferralTeaser,
    SavingsSummary,
    UserListResponse,
    UserSummary,
)

router = APIRouter(tags=["users"])


@router.get("/users", response_model=UserListResponse)
async def list_users(conn: Conn, limit: int = Query(default=50, ge=1, le=500)) -> UserListResponse:
    summaries = await service.list_users(conn, limit=limit)
    return UserListResponse(items=[UserSummary.model_validate(s) for s in summaries])


@router.get("/users/{user_id}/home", response_model=HomeResponse)
async def get_home(user_id: int, conn: Conn) -> HomeResponse:
    aggregate = await home.get_home(conn, user_id)
    hero = aggregate.hero_challenge
    return HomeResponse(
        user=UserSummary(
            id=aggregate.user.id,
            pseudonym=aggregate.user.pseudonym,
            segment=aggregate.user.segment,
            level=aggregate.domovoy.level,
        ),
        domovoy=DomovoyState.model_validate(aggregate.domovoy),
        savings=SavingsSummary.model_validate(aggregate.savings),
        points_balance=aggregate.points_balance,
        insight=aggregate.insight,
        hero_challenge=ChallengeDetail.model_validate(hero) if hero is not None else None,
        league=None,
        referral=ReferralTeaser.model_validate(aggregate.referral),
        recommended_mechanic=RecommendedMechanic.model_validate(aggregate.recommended_mechanic),
    )
