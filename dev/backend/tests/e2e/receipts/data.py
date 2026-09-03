RECEIPT_PROCESSING_RESULT_FIELDS = {
    "receipt",
    "counted",
    "counted_reason",
    "xp_delta",
    "domovoy",
    "savings_delta",
    "challenges",
    "league_rank_before",
    "league_rank_after",
    "referral_status",
    "fraud",
    "achievements_unlocked",
}
RECEIPT_FIELDS = {
    "id",
    "store_id",
    "store_name",
    "purchased_at",
    "regular_total",
    "paid_total",
    "discount_total",
    "points_earned",
    "points_spent",
    "counted",
    "is_returned",
    "items",
}
DOMOVOY_STATE_FIELDS = {
    "xp",
    "level",
    "xp_to_next_level",
    "mood",
    "mood_reason",
    "streak_weeks",
    "items",
}
FRAUD_DECISION_FIELDS = {"score", "decision", "signals"}

TWO_ITEM_PAYLOAD = [
    {
        "product_name": "Молоко",
        "category": "dairy",
        "qty": 1,
        "regular_price": 89.90,
        "paid_price": 79.90,
    },
    {
        "product_name": "Багет",
        "category": "bakery",
        "qty": 2,
        "regular_price": 59.90,
        "paid_price": 49.90,
        "is_promo": True,
    },
]
TWO_ITEM_REGULAR_TOTAL = 209.70
TWO_ITEM_PAID_TOTAL = 179.70
TWO_ITEM_DISCOUNT_TOTAL = 30.00

ONE_ITEM_PAYLOAD = [
    {
        "product_name": "Йогурт",
        "category": "dairy",
        "qty": 1,
        "regular_price": 50.0,
        "paid_price": 45.0,
    }
]

LIMIT_CASES = [
    (1, 200),
    (200, 200),
    (0, 422),
    (201, 422),
]
