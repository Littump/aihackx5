from fastapi import APIRouter, Query

from app.core.db import Conn
from app.features.rewards import service
from app.features.rewards.dto import RewardsResponse

router = APIRouter(tags=["rewards"])


@router.get("/users/{user_id}/rewards", response_model=RewardsResponse)
async def get_rewards(
    user_id: int, conn: Conn, limit: int = Query(default=50, ge=1, le=200)
) -> RewardsResponse:
    summary = await service.get_rewards(conn, user_id, limit=limit)
    return RewardsResponse.model_validate(summary)
