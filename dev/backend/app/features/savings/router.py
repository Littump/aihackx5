from typing import Literal

from fastapi import APIRouter, Query

from app.core.db import Conn
from app.features.savings import service
from app.features.savings.dto import SavingsSummary

router = APIRouter(tags=["savings"])


@router.get("/users/{user_id}/savings", response_model=SavingsSummary)
async def get_savings(
    user_id: int, conn: Conn, period: Literal["week", "month"] = Query(default="month")
) -> SavingsSummary:
    result = await service.summary(conn, user_id, period)
    return SavingsSummary.model_validate(result)
