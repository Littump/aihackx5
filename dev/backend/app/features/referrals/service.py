from datetime import timedelta
from decimal import Decimal

from psycopg import AsyncConnection

from app import game_rules
from app.core.clock import now
from app.core.errors import AppError
from app.features.antifraud.models import FraudDecision
from app.features.challenges import service as challenges_service
from app.features.domovoy import service as domovoy_service
from app.features.receipts.models import ReceiptDetail
from app.features.referrals import database, rewards
from app.features.referrals.models import (
    RedeemReferralResult,
    ReferralPageView,
    ReferralProgressDelta,
    ReferralRow,
    ReferralStatus,
)
from app.features.users import service as users_service


async def get_referral_by_id(conn: AsyncConnection, referral_id: int) -> ReferralRow | None:
    return await database.get_referral_by_id(conn, referral_id=referral_id)


async def list_by_referrer(conn: AsyncConnection, *, referrer_user_id: int) -> list[ReferralRow]:
    return await database.list_by_referrer(conn, referrer_user_id=referrer_user_id)


async def redeem(
    conn: AsyncConnection, *, code: str, device_fingerprint: str | None, pseudonym: str | None
) -> RedeemReferralResult:
    referrer = await users_service.get_user_by_referral_code(conn, code)
    if referrer is None:
        raise AppError("referrer_not_found", "код приглашения не найден", 404)
    await _check_redeem_limit(conn, referrer.id)
    referee = await users_service.create_user(
        conn,
        segment="dormant",
        pseudonym=pseudonym,
        referred_by_user_id=referrer.id,
        device_fingerprint=device_fingerprint,
    )
    referral = await database.insert_referral(
        conn,
        referrer_user_id=referrer.id,
        referee_user_id=referee.id,
        referee_kind="new",
        status="pending",
    )
    return RedeemReferralResult(
        referee_user_id=referee.id,
        referrer_user_id=referrer.id,
        referee_kind=referral.referee_kind,
        status=referral.status,
    )


async def _check_redeem_limit(conn: AsyncConnection, referrer_user_id: int) -> None:
    year_start, year_end = rewards.year_bounds(now())
    rewarded = await database.count_rewarded_in_range(
        conn, referrer_user_id=referrer_user_id, start=year_start, end=year_end
    )
    if rewarded >= game_rules.REFERRAL_PAID_PER_YEAR:
        message = "годовой лимит наград за рефералов исчерпан"
        raise AppError("referral_limit_reached", message, 409)


async def on_receipt(
    conn: AsyncConnection, referee_user_id: int, receipt: ReceiptDetail
) -> ReferralProgressDelta | None:
    if not receipt.counted:
        return None
    referral = await database.get_referral_by_referee(conn, referee_user_id=referee_user_id)
    if referral is None:
        return None
    if referral.status == "pending":
        return await _handle_first_purchase(conn, referral, receipt)
    if referral.status == "first_purchase":
        return await _handle_second_purchase(conn, referral, receipt)
    return None


async def _handle_first_purchase(
    conn: AsyncConnection, referral: ReferralRow, receipt: ReceiptDetail
) -> ReferralProgressDelta | None:
    if receipt.paid_total < game_rules.REFERRAL_MIN_FIRST_PURCHASE:
        return None
    reward = rewards.rewards_for(referral.referee_kind)
    updated = await database.mark_first_purchase(
        conn,
        referral_id=referral.id,
        first_purchase_at=receipt.purchased_at,
        referee_reward_points=reward["referee_first_purchase_points"],
    )
    await challenges_service.record_reward(
        conn,
        user_id=referral.referee_user_id,
        kind="referral",
        xp_delta=0,
        points_delta=reward["referee_first_purchase_points"],
        ref_type="referral",
        ref_id=referral.id,
    )
    return ReferralProgressDelta(referral_id=updated.id, status=updated.status)


async def _handle_second_purchase(
    conn: AsyncConnection, referral: ReferralRow, receipt: ReceiptDetail
) -> ReferralProgressDelta | None:
    assert referral.first_purchase_at is not None
    min_gap = timedelta(days=game_rules.REFERRAL_SECOND_PURCHASE_MIN_DAYS)
    if receipt.purchased_at - referral.first_purchase_at < min_gap:
        return None
    qualified = await database.mark_qualified(
        conn, referral_id=referral.id, second_purchase_at=receipt.purchased_at
    )
    return await _decide_reward(conn, qualified)


async def _decide_reward(conn: AsyncConnection, referral: ReferralRow) -> ReferralProgressDelta:
    # отложенный импорт разрывает цикл: antifraud.service тянет нас
    from app.features.antifraud import service as antifraud_service

    decision = await antifraud_service.check_referral(conn, referral.id)
    if decision.decision == "approve":
        updated = await _reward_referrer_if_within_limit(conn, referral, decision)
        return ReferralProgressDelta(referral_id=updated.id, status=updated.status)
    status: ReferralStatus = "blocked" if decision.decision == "block" else "on_review"
    updated = await _apply_decision(
        conn, referral, status=status, decision=decision, reward_points=0
    )
    return ReferralProgressDelta(referral_id=updated.id, status=updated.status)


async def _reward_referrer_if_within_limit(
    conn: AsyncConnection, referral: ReferralRow, decision: FraudDecision
) -> ReferralRow:
    month_start, month_end = rewards.month_bounds(now())
    rewarded_this_month = await database.count_rewarded_in_range(
        conn, referrer_user_id=referral.referrer_user_id, start=month_start, end=month_end
    )
    if rewarded_this_month >= game_rules.REFERRAL_PAID_PER_MONTH:
        return referral
    reward = rewards.rewards_for(referral.referee_kind)
    updated = await _apply_decision(
        conn,
        referral,
        status="rewarded",
        decision=decision,
        reward_points=reward["referrer_reward_points"],
    )
    await domovoy_service.add_xp(
        conn,
        referral.referrer_user_id,
        reward["referrer_reward_xp"],
        kind="referral",
        ref_type="referral",
        ref_id=referral.id,
        points_delta=reward["referrer_reward_points"],
    )
    return updated


async def _apply_decision(
    conn: AsyncConnection,
    referral: ReferralRow,
    *,
    status: ReferralStatus,
    decision: FraudDecision,
    reward_points: int,
) -> ReferralRow:
    return await database.mark_decision(
        conn,
        referral_id=referral.id,
        status=status,
        decided_at=now(),
        fraud_score=Decimal(str(decision.score)),
        fraud_reasons=[signal.detail for signal in decision.signals],
        referrer_reward_points=reward_points,
    )


async def get_referral_page(conn: AsyncConnection, user_id: int) -> ReferralPageView:
    user = await users_service.get_user(conn, user_id)
    rows = await database.list_by_referrer(conn, referrer_user_id=user_id)
    month_start, month_end = rewards.month_bounds(now())
    paid_this_month = await database.count_rewarded_in_range(
        conn, referrer_user_id=user_id, start=month_start, end=month_end
    )
    new_reward = rewards.rewards_for("new")
    dormant_reward = rewards.rewards_for("dormant")
    return ReferralPageView(
        code=user.referral_code,
        link=rewards.referral_link(user.referral_code),
        rules=rewards.rules_text(),
        referrer_reward_points=new_reward["referrer_reward_points"],
        referee_reward_points_new=new_reward["referee_first_purchase_points"],
        referee_reward_points_dormant=dormant_reward["referee_first_purchase_points"],
        invitees=[rewards.to_invitee_view(row, i) for i, row in enumerate(rows, start=1)],
        paid_this_month=paid_this_month,
        paid_limit_month=game_rules.REFERRAL_PAID_PER_MONTH,
    )
