from fastapi import APIRouter

from app.core.db import Conn
from app.features.challenges import service
from app.features.challenges.dto import ChallengeDetail, ChallengeListResponse

router = APIRouter(tags=["challenges"])


@router.get("/users/{user_id}/challenges", response_model=ChallengeListResponse)
async def list_challenges(user_id: int, conn: Conn) -> ChallengeListResponse:
    result = await service.get_list(conn, user_id)
    return ChallengeListResponse.from_result(result)


@router.post("/users/{user_id}/challenges/refresh", response_model=ChallengeListResponse)
async def refresh_challenges(user_id: int, conn: Conn) -> ChallengeListResponse:
    result = await service.refresh_weekly(conn, user_id)
    return ChallengeListResponse.from_result(result)


@router.get("/users/{user_id}/challenges/{challenge_id}", response_model=ChallengeDetail)
async def get_challenge(user_id: int, challenge_id: int, conn: Conn) -> ChallengeDetail:
    row = await service.get_one(conn, user_id, challenge_id)
    return ChallengeDetail.model_validate(row)
