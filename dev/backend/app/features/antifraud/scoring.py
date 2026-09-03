from decimal import Decimal

from app import game_rules
from app.features.antifraud.models import (
    FraudDecision,
    FraudDecisionKind,
    FraudSignal,
    ReceiptFraudContext,
    ReferralFraudContext,
)


def score_receipt(ctx: ReceiptFraudContext) -> FraudDecision:
    detectors = (
        _burst_same_store,
        _daily_volume,
        _same_pos_share,
        _frequency_spike,
        _return_after_reward,
        _basket_monotony,
    )
    signals = [signal for detect in detectors if (signal := detect(ctx)) is not None]
    return _decide(signals)


def score_referral(ctx: ReferralFraudContext) -> FraudDecision:
    detectors = (
        _shared_device,
        _instant_signup,
        _min_purchase_pattern,
        _invite_burst,
        _referral_ring,
        _same_store_zero_activity,
    )
    signals = [signal for detect in detectors if (signal := detect(ctx)) is not None]
    return _decide(signals)


def decide(score: float, strong_count: int) -> FraudDecisionKind:
    if score < game_rules.FRAUD_HOLD_THRESHOLD:
        return "approve"
    if score < game_rules.FRAUD_BLOCK_THRESHOLD:
        return "hold"
    if strong_count >= game_rules.FRAUD_BLOCK_MIN_STRONG:
        return "block"
    return "hold"


def _decide(signals: list[FraudSignal]) -> FraudDecision:
    score = round(min(1.0, sum(signal.weight for signal in signals)), 3)
    strong_count = sum(1 for signal in signals if signal.strong)
    return FraudDecision(score=score, decision=decide(score, strong_count), signals=signals)


def _receipt_signal(code: str, detail: str) -> FraudSignal:
    return _signal_from_spec(game_rules.RECEIPT_SIGNALS[code], code=code, detail=detail)


def _referral_signal(code: str, detail: str) -> FraudSignal:
    return _signal_from_spec(game_rules.REFERRAL_SIGNALS[code], code=code, detail=detail)


def _signal_from_spec(spec: dict[str, float | bool], *, code: str, detail: str) -> FraudSignal:
    return FraudSignal(
        code=code, weight=float(spec["weight"]), strong=bool(spec["strong"]), detail=detail
    )


def _burst_same_store(ctx: ReceiptFraudContext) -> FraudSignal | None:
    if ctx.receipts_same_store_last_60min < game_rules.FRAUD_BURST_SAME_STORE_MIN_RECEIPTS:
        return None
    detail = (
        f"{ctx.receipts_same_store_last_60min} чеков в одном магазине "
        f"за {game_rules.FRAUD_BURST_WINDOW_MIN} минут"
    )
    return _receipt_signal("burst_same_store", detail)


def _daily_volume(ctx: ReceiptFraudContext) -> FraudSignal | None:
    if ctx.receipts_today < game_rules.FRAUD_DAILY_VOLUME_MIN_RECEIPTS:
        return None
    return _receipt_signal("daily_volume", f"{ctx.receipts_today} чеков за сегодня")


def _same_pos_share(ctx: ReceiptFraudContext) -> FraudSignal | None:
    if ctx.pos_receipts_sample_size < game_rules.FRAUD_SAME_POS_MIN_SAMPLE:
        return None
    if ctx.max_pos_share_last_7d <= Decimal(str(game_rules.FRAUD_SAME_POS_SHARE_MIN)):
        return None
    same_pos_count = round(ctx.max_pos_share_last_7d * ctx.pos_receipts_sample_size)
    pct = round(ctx.max_pos_share_last_7d * 100)
    sample = ctx.pos_receipts_sample_size
    detail = f"{pct}% чеков через один pos_id ({same_pos_count} из {sample})"
    return _receipt_signal("same_pos_share", detail)


def _frequency_spike(ctx: ReceiptFraudContext) -> FraudSignal | None:
    if ctx.frequency_per_week < Decimal(str(game_rules.FREQUENCY_BASELINE_MIN)):
        return None
    threshold = ctx.frequency_per_week * game_rules.FRAUD_FREQUENCY_SPIKE_MULTIPLIER
    if Decimal(ctx.receipts_last_7d) < threshold:
        return None
    detail = f"{ctx.receipts_last_7d} чеков за 7 дней при обычных {ctx.frequency_per_week} в неделю"
    return _receipt_signal("frequency_spike", detail)


def _return_after_reward(ctx: ReceiptFraudContext) -> FraudSignal | None:
    days = ctx.days_since_challenge_completion_by_this_receipt
    if not ctx.is_return or days is None:
        return None
    if days > game_rules.FRAUD_RETURN_AFTER_REWARD_MAX_DAYS:
        return None
    detail = f"возврат через {days} дн. после закрытия челленджа"
    return _receipt_signal("return_after_reward", detail)


def _basket_monotony(ctx: ReceiptFraudContext) -> FraudSignal | None:
    if ctx.consecutive_matching_baskets < game_rules.FRAUD_BASKET_MONOTONY_MIN_CONSECUTIVE:
        return None
    detail = f"{ctx.consecutive_matching_baskets} чека подряд с одинаковым составом и суммой"
    return _receipt_signal("basket_monotony", detail)


def _shared_device(ctx: ReferralFraudContext) -> FraudSignal | None:
    if not ctx.shared_device:
        return None
    detail = "device_fingerprint совпадает у пригласившего и приглашённого (1 совпадение)"
    return _referral_signal("shared_device", detail)


def _instant_signup(ctx: ReferralFraudContext) -> FraudSignal | None:
    minutes = ctx.minutes_since_link_generated
    if minutes is None or minutes >= game_rules.FRAUD_INSTANT_SIGNUP_MAX_MINUTES:
        return None
    detail = f"приглашённый зарегистрирован через {minutes} минут после генерации ссылки"
    return _referral_signal("instant_signup", detail)


def _min_purchase_pattern(ctx: ReferralFraudContext) -> FraudSignal | None:
    if ctx.invitees_count < game_rules.FRAUD_MIN_PURCHASE_PATTERN_MIN_INVITEES:
        return None
    if not ctx.invitees_all_single_purchase_500_550:
        return None
    detail = (
        f"все {ctx.invitees_count} приглашённых сделали ровно 1 покупку "
        f"{game_rules.FRAUD_MIN_PURCHASE_PATTERN_MIN_RUB}-"
        f"{game_rules.FRAUD_MIN_PURCHASE_PATTERN_MAX_RUB} ₽"
    )
    return _referral_signal("min_purchase_pattern", detail)


def _invite_burst(ctx: ReferralFraudContext) -> FraudSignal | None:
    if ctx.invites_last_hour <= game_rules.FRAUD_INVITE_BURST_MAX_PER_HOUR:
        return None
    return _referral_signal("invite_burst", f"{ctx.invites_last_hour} приглашений за час")


def _referral_ring(ctx: ReferralFraudContext) -> FraudSignal | None:
    if not ctx.is_referral_ring:
        return None
    detail = "обнаружена 1 кольцевая связь между пригласившим и приглашённым"
    return _referral_signal("referral_ring", detail)


def _same_store_zero_activity(ctx: ReferralFraudContext) -> FraudSignal | None:
    days = ctx.days_since_qualifying_with_no_activity
    if days is None or days < game_rules.FRAUD_SAME_STORE_ZERO_ACTIVITY_DAYS:
        return None
    detail = f"нет чеков {days} дней после квалифицирующей покупки"
    return _referral_signal("same_store_zero_activity", detail)
