from decimal import Decimal

from app.features.antifraud.models import ReceiptFraudContext, ReferralFraudContext

RECEIPT_CTX_DEFAULTS: dict[str, object] = {
    "receipts_same_store_last_60min": 0,
    "receipts_today": 0,
    "receipts_last_7d": 0,
    "max_pos_share_last_7d": Decimal("0"),
    "pos_receipts_sample_size": 0,
    "frequency_per_week": Decimal("0"),
    "is_return": False,
    "days_since_challenge_completion_by_this_receipt": None,
    "consecutive_matching_baskets": 0,
}

REFERRAL_CTX_DEFAULTS: dict[str, object] = {
    "shared_device": False,
    "minutes_since_link_generated": None,
    "invitees_count": 0,
    "invitees_all_single_purchase_500_550": False,
    "invites_last_hour": 0,
    "is_referral_ring": False,
    "days_since_qualifying_with_no_activity": None,
}


def receipt_ctx(**overrides: object) -> ReceiptFraudContext:
    params = dict(RECEIPT_CTX_DEFAULTS)
    params.update(overrides)
    return ReceiptFraudContext.model_validate(params)


def referral_ctx(**overrides: object) -> ReferralFraudContext:
    params = dict(REFERRAL_CTX_DEFAULTS)
    params.update(overrides)
    return ReferralFraudContext.model_validate(params)


RECEIPT_SIGNAL_CASES: list[tuple[str, dict[str, object], bool]] = [
    ("burst_same_store", {"receipts_same_store_last_60min": 4}, True),
    ("burst_same_store", {"receipts_same_store_last_60min": 3}, False),
    ("daily_volume", {"receipts_today": 6}, True),
    ("daily_volume", {"receipts_today": 5}, False),
    (
        "same_pos_share",
        {"pos_receipts_sample_size": 10, "max_pos_share_last_7d": Decimal("0.8")},
        True,
    ),
    (
        "same_pos_share",
        {"pos_receipts_sample_size": 10, "max_pos_share_last_7d": Decimal("0.70")},
        False,
    ),
    (
        "same_pos_share",
        {"pos_receipts_sample_size": 4, "max_pos_share_last_7d": Decimal("0.9")},
        False,
    ),
    (
        "frequency_spike",
        {"frequency_per_week": Decimal("2"), "receipts_last_7d": 8},
        True,
    ),
    (
        "frequency_spike",
        {"frequency_per_week": Decimal("2"), "receipts_last_7d": 7},
        False,
    ),
    (
        "frequency_spike",
        {"frequency_per_week": Decimal("0.5"), "receipts_last_7d": 100},
        False,
    ),
    (
        "return_after_reward",
        {"is_return": True, "days_since_challenge_completion_by_this_receipt": 3},
        True,
    ),
    (
        "return_after_reward",
        {"is_return": True, "days_since_challenge_completion_by_this_receipt": 4},
        False,
    ),
    (
        "return_after_reward",
        {"is_return": False, "days_since_challenge_completion_by_this_receipt": 1},
        False,
    ),
    ("basket_monotony", {"consecutive_matching_baskets": 3}, True),
    ("basket_monotony", {"consecutive_matching_baskets": 2}, False),
]

REFERRAL_SIGNAL_CASES: list[tuple[str, dict[str, object], bool]] = [
    ("shared_device", {"shared_device": True}, True),
    ("shared_device", {"shared_device": False}, False),
    ("instant_signup", {"minutes_since_link_generated": 9}, True),
    ("instant_signup", {"minutes_since_link_generated": 10}, False),
    ("instant_signup", {"minutes_since_link_generated": None}, False),
    (
        "min_purchase_pattern",
        {"invitees_count": 3, "invitees_all_single_purchase_500_550": True},
        True,
    ),
    (
        "min_purchase_pattern",
        {"invitees_count": 2, "invitees_all_single_purchase_500_550": True},
        False,
    ),
    (
        "min_purchase_pattern",
        {"invitees_count": 3, "invitees_all_single_purchase_500_550": False},
        False,
    ),
    ("invite_burst", {"invites_last_hour": 6}, True),
    ("invite_burst", {"invites_last_hour": 5}, False),
    ("referral_ring", {"is_referral_ring": True}, True),
    ("referral_ring", {"is_referral_ring": False}, False),
    ("same_store_zero_activity", {"days_since_qualifying_with_no_activity": 14}, True),
    ("same_store_zero_activity", {"days_since_qualifying_with_no_activity": 13}, False),
    ("same_store_zero_activity", {"days_since_qualifying_with_no_activity": None}, False),
]
