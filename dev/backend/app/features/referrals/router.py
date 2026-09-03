from fastapi import APIRouter

from app.core.db import Conn
from app.features.referrals import service
from app.features.referrals.dto import (
    RedeemReferralInput,
    RedeemReferralResponse,
    ReferralResponse,
)

router = APIRouter(tags=["referrals"])


@router.get("/users/{user_id}/referral", response_model=ReferralResponse)
async def get_referral(user_id: int, conn: Conn) -> ReferralResponse:
    page = await service.get_referral_page(conn, user_id)
    return ReferralResponse.model_validate(page)


@router.post("/referrals/redeem", response_model=RedeemReferralResponse, status_code=201)
async def redeem_referral(payload: RedeemReferralInput, conn: Conn) -> RedeemReferralResponse:
    result = await service.redeem(
        conn,
        code=payload.code,
        device_fingerprint=payload.device_fingerprint,
        pseudonym=payload.pseudonym,
    )
    return RedeemReferralResponse.model_validate(result)
