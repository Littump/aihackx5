from fastapi import APIRouter

from app.core.db import Conn
from app.features.achievements import service
from app.features.achievements.dto import Achievement, AchievementListResponse

router = APIRouter(tags=["achievements"])


@router.get("/users/{user_id}/achievements", response_model=AchievementListResponse)
async def list_achievements(user_id: int, conn: Conn) -> AchievementListResponse:
    items = await service.list_for_user(conn, user_id)
    return AchievementListResponse(items=[Achievement.model_validate(item) for item in items])
