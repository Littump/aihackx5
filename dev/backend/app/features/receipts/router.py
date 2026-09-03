from fastapi import APIRouter, Query, status

from app.core.db import Conn
from app.features.receipts import service
from app.features.receipts.dto import (
    Receipt,
    ReceiptInput,
    ReceiptListResponse,
    ReceiptProcessingResult,
)

router = APIRouter(tags=["receipts"])


@router.post(
    "/receipts", response_model=ReceiptProcessingResult, status_code=status.HTTP_201_CREATED
)
async def create_receipt(payload: ReceiptInput, conn: Conn) -> ReceiptProcessingResult:
    outcome = await service.process_receipt(
        conn,
        user_id=payload.user_id,
        store_id=payload.store_id,
        purchased_at=payload.purchased_at,
        points_earned=payload.points_earned,
        points_spent=payload.points_spent,
        pos_id=payload.pos_id,
        items=payload.items,
    )
    return ReceiptProcessingResult.model_validate(outcome)


@router.get("/users/{user_id}/receipts", response_model=ReceiptListResponse)
async def list_receipts(
    user_id: int, conn: Conn, limit: int = Query(default=20, ge=1, le=200)
) -> ReceiptListResponse:
    receipts = await service.list_receipts(conn, user_id=user_id, limit=limit)
    return ReceiptListResponse(items=[Receipt.model_validate(r) for r in receipts])
