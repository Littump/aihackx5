from fastapi import APIRouter

from app.core.db import Conn
from app.features.health import service
from app.features.health.dto import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def get_health(conn: Conn) -> HealthResponse:
    return HealthResponse.model_validate(await service.check(conn))
