from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal

from psycopg import AsyncConnection

from app import game_rules
from app.core.clock import day_end, day_start, now
from app.core.errors import AppError
from app.features.antifraud import database, scoring
from app.features.antifraud.models import (
    FraudCheckRow,
    FraudDecision,
    FraudDecisionKind,
    ReceiptFraudContext,
    ReferralFraudContext,
)
from app.features.challenges import service as challenges_service
from app.features.receipts import service as receipts_service
from app.features.receipts.models import ReceiptDetail, ReceiptRow
from app.features.referrals import service as referrals_service
from app.features.referrals.models import ReferralRow
from app.features.user_features import service as user_features_service
from app.features.users import service as users_service


async def check_receipt(conn: AsyncConnection, user_id: int, receipt: ReceiptRow) -> FraudDecision:
    ctx = await _build_receipt_context(conn, user_id, receipt)
    decision = scoring.score_receipt(ctx)
    await database.insert_fraud_check(
        conn, subject_type="receipt", subject_id=receipt.id, user_id=user_id, decision=decision
    )
    return decision


async def check_referral(conn: AsyncConnection, referral_id: int) -> FraudDecision:
    referral = await _get_referral_or_404(conn, referral_id)
    ctx = await _build_referral_context(conn, referral)
    decision = scoring.score_referral(ctx)
    await database.insert_fraud_check(
        conn,
        subject_type="referral",
        subject_id=referral.id,
        user_id=referral.referrer_user_id,
        decision=decision,
    )
    return decision


async def list_for_user(conn: AsyncConnection, user_id: int, limit: int) -> list[FraudCheckRow]:
    return await database.list_fraud_checks_for_user(conn, user_id=user_id, limit=limit)


async def list_all(
    conn: AsyncConnection, *, limit: int, decision: FraudDecisionKind | None
) -> list[FraudCheckRow]:
    return await database.list_fraud_checks(conn, limit=limit, decision=decision)


async def _get_referral_or_404(conn: AsyncConnection, referral_id: int) -> ReferralRow:
    referral = await referrals_service.get_referral_by_id(conn, referral_id)
    if referral is None:
        raise AppError("referral_not_found", "реферал не найден", 404)
    return referral


async def _build_receipt_context(
    conn: AsyncConnection, user_id: int, receipt: ReceiptRow
) -> ReceiptFraudContext:
    since = receipt.purchased_at - timedelta(days=game_rules.FRAUD_HISTORY_WINDOW_DAYS)
    history = await receipts_service.list_receipts_since(conn, user_id=user_id, since=since)
    window = timedelta(minutes=game_rules.FRAUD_BURST_WINDOW_MIN)
    burst = _count_in_window(
        history, store_id=receipt.store_id, anchor=receipt.purchased_at, window=window
    )
    today = _count_same_day(history, receipt.purchased_at)
    pos_share, pos_sample = _pos_share(history)
    features = await user_features_service.get(conn, user_id)
    basket_history = await receipts_service.list_receipts(
        conn, user_id=user_id, limit=game_rules.FRAUD_BASKET_MONOTONY_LOOKBACK_RECEIPTS
    )
    consecutive = _consecutive_matching_baskets(basket_history, receipt.id)
    completion_days = await _days_since_challenge_completion(conn, user_id, receipt)
    return ReceiptFraudContext(
        receipts_same_store_last_60min=burst,
        receipts_today=today,
        receipts_last_7d=len(history),
        max_pos_share_last_7d=pos_share,
        pos_receipts_sample_size=pos_sample,
        frequency_per_week=features.frequency_per_week,
        is_return=receipt.is_returned,
        days_since_challenge_completion_by_this_receipt=completion_days,
        consecutive_matching_baskets=consecutive,
    )


def _count_in_window(
    receipts: list[ReceiptRow], *, store_id: int, anchor: datetime, window: timedelta
) -> int:
    return sum(
        1
        for r in receipts
        if r.store_id == store_id and anchor - window <= r.purchased_at <= anchor
    )


def _count_same_day(receipts: list[ReceiptRow], anchor: datetime) -> int:
    start, end = day_start(anchor), day_end(anchor)
    return sum(1 for r in receipts if start <= r.purchased_at <= end)


def _pos_share(receipts: list[ReceiptRow]) -> tuple[Decimal, int]:
    with_pos = [r.pos_id for r in receipts if r.pos_id is not None]
    if not with_pos:
        return Decimal("0"), 0
    _, top_count = Counter(with_pos).most_common(1)[0]
    return Decimal(top_count) / Decimal(len(with_pos)), len(with_pos)


async def _days_since_challenge_completion(
    conn: AsyncConnection, user_id: int, receipt: ReceiptRow
) -> int | None:
    if not receipt.is_returned or receipt.returned_at is None:
        return None
    challenges = await challenges_service.get_list(conn, user_id)
    completions = [
        c.completed_at
        for c in challenges.history
        if c.status == "completed"
        and c.completed_at is not None
        and c.completed_at.date() == receipt.purchased_at.date()
    ]
    if not completions:
        return None
    closest = min(completions, key=lambda at: abs(at - receipt.purchased_at))
    return (receipt.returned_at.date() - closest.date()).days


def _consecutive_matching_baskets(receipts: list[ReceiptDetail], target_id: int) -> int:
    index = next((i for i, r in enumerate(receipts) if r.id == target_id), None)
    if index is None:
        return 0
    anchor = receipts[index]
    anchor_categories = {item.category for item in anchor.items}
    count = 0
    for candidate in receipts[index:]:
        if {item.category for item in candidate.items} != anchor_categories:
            break
        if not _within_tolerance(candidate.paid_total, anchor.paid_total):
            break
        count += 1
    return count


def _within_tolerance(amount: Decimal, anchor: Decimal) -> bool:
    if anchor == 0:
        return amount == 0
    tolerance = Decimal(str(game_rules.FRAUD_BASKET_MONOTONY_AMOUNT_TOLERANCE))
    return abs(amount - anchor) / anchor <= tolerance


async def _build_referral_context(
    conn: AsyncConnection, referral: ReferralRow
) -> ReferralFraudContext:
    referrer = await users_service.get_user(conn, referral.referrer_user_id)
    referee = await users_service.get_user(conn, referral.referee_user_id)
    referrer_invitees = await referrals_service.list_by_referrer(
        conn, referrer_user_id=referral.referrer_user_id
    )
    referee_invitees = await referrals_service.list_by_referrer(
        conn, referrer_user_id=referral.referee_user_id
    )
    shared_device = (
        referrer.device_fingerprint is not None
        and referrer.device_fingerprint == referee.device_fingerprint
    )
    all_single = await _all_invitees_single_purchase(conn, referrer_invitees)
    ring = _is_referral_ring(referee_invitees, referral.referrer_user_id, referrer_invitees)
    zero_activity_days = await _days_since_qualifying_zero_activity(conn, referral)
    return ReferralFraudContext(
        shared_device=shared_device,
        minutes_since_link_generated=_minutes_since(referrer.created_at, referral.created_at),
        invitees_count=len(referrer_invitees),
        invitees_all_single_purchase_500_550=all_single,
        invites_last_hour=_count_invite_burst(referrer_invitees, referral.created_at),
        is_referral_ring=ring,
        days_since_qualifying_with_no_activity=zero_activity_days,
    )


def _minutes_since(start: datetime, end: datetime) -> int:
    return int((end - start).total_seconds() // 60)


async def _all_invitees_single_purchase(conn: AsyncConnection, invitees: list[ReferralRow]) -> bool:
    if len(invitees) < game_rules.FRAUD_MIN_PURCHASE_PATTERN_MIN_INVITEES:
        return False
    for invitee in invitees:
        receipts = await receipts_service.list_receipts(
            conn,
            user_id=invitee.referee_user_id,
            limit=game_rules.FRAUD_MIN_PURCHASE_PATTERN_LOOKBACK_RECEIPTS,
        )
        if not _is_single_matching_purchase(receipts):
            return False
    return True


def _is_single_matching_purchase(receipts: list[ReceiptDetail]) -> bool:
    if len(receipts) != 1:
        return False
    amount = receipts[0].paid_total
    return (
        game_rules.FRAUD_MIN_PURCHASE_PATTERN_MIN_RUB
        <= amount
        <= game_rules.FRAUD_MIN_PURCHASE_PATTERN_MAX_RUB
    )


def _count_invite_burst(invitees: list[ReferralRow], anchor: datetime) -> int:
    window = timedelta(minutes=game_rules.FRAUD_INVITE_BURST_WINDOW_MIN)
    return sum(1 for r in invitees if anchor - window <= r.created_at <= anchor)


def _is_referral_ring(
    referee_invitees: list[ReferralRow],
    referrer_user_id: int,
    referrer_invitees: list[ReferralRow],
) -> bool:
    referrer_invitee_ids = {r.referee_user_id for r in referrer_invitees}
    return any(
        r.referee_user_id == referrer_user_id or r.referee_user_id in referrer_invitee_ids
        for r in referee_invitees
    )


async def _days_since_qualifying_zero_activity(
    conn: AsyncConnection, referral: ReferralRow
) -> int | None:
    if referral.second_purchase_at is None:
        return None
    since = referral.second_purchase_at + timedelta(seconds=1)
    receipts_after = await receipts_service.list_counted_receipts_with_items(
        conn, user_id=referral.referee_user_id, since=since
    )
    if receipts_after:
        return None
    return (now() - referral.second_purchase_at).days
