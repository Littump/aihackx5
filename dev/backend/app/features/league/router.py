from fastapi import APIRouter

from app.core.db import Conn
from app.features.league import service
from app.features.league.dto import LeagueResponse

router = APIRouter(tags=["league"])


@router.get("/users/{user_id}/league", response_model=LeagueResponse)
async def get_league(user_id: int, conn: Conn) -> LeagueResponse:
    view = await service.get_league_view(conn, user_id)
    return LeagueResponse.model_validate(view)
