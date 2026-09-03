from fastapi import APIRouter, Query

from app.core.db import Conn
from app.features.users import service
from app.features.users.dto import UserListResponse, UserSummary

router = APIRouter(tags=["users"])


@router.get("/users", response_model=UserListResponse)
async def list_users(conn: Conn, limit: int = Query(default=50, ge=1, le=500)) -> UserListResponse:
    summaries = await service.list_users(conn, limit=limit)
    return UserListResponse(items=[UserSummary.model_validate(s) for s in summaries])
