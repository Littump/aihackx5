TIMEZONE = "Europe/Moscow"

RECEIPT_DEDUP_WINDOW_MIN = 30
RECEIPTS_PER_DAY_MAX = 3
FEATURES_WINDOW_WEEKS = 10
USER_FEATURES_RECENCY_NO_HISTORY_DAYS = 999
REALIZED_SAVINGS_WINDOW_DAYS = 30

CATEGORIES: tuple[str, ...] = (
    "dairy",
    "bakery",
    "fruits_veg",
    "meat_fish",
    "grocery",
    "snacks",
    "drinks",
    "alcohol",
    "household",
    "beauty",
    "ready_food",
    "other",
)
CHALLENGE_EXCLUDED_CATEGORIES: frozenset[str] = frozenset({"alcohol"})
CHALLENGE_PROGRESS_STEP = 1

SAVINGS_WEEK_WINDOW_DAYS = 7
SAVINGS_TOP_CATEGORIES_LIMIT = 3

FREQUENCY_BASELINE_MIN = 1

FREQUENCY_HEADROOM_MAX = 6
CANDIDATE_RECENCY_MAX_DAYS = 21
CANDIDATE_CATEGORY_MIN_SHARE = 0.10
CANDIDATE_CATEGORY_MIN_VISITS = 3
CANDIDATE_DEFAULT_FREQUENCY_BASELINE = 1
CANDIDATE_DEFAULT_FREQUENCY_TARGET = 2

TARGET_MULTIPLIER = 1.2
TARGET_MIN_DELTA = 1
TARGET_CEILING_DELTA = 2

CONTRIBUTION_MARGIN = 0.15
REWARD_SHARE_MAX = 0.40
REWARD_POINTS_MIN = 30
REWARD_POINTS_MAX_WEEKLY = 150
REWARD_POINTS_ROUNDING_STEP = 10
POINT_COST_RUB = 0.75
SPONSOR_SHARE = 0.5

PRIORITY_FREQUENCY_BASE = 1.0
PRIORITY_FREQUENCY_HEADROOM_WEIGHT = 0.5
PRIORITY_CATEGORY_BASE = 0.8

CHALLENGE_SIDE_MAX = 2

XP_RECEIPT = 10
XP_CHALLENGE = 50
XP_STREAK_4W = 100
XP_LEAGUE_PROMOTION = 30
XP_LEAGUE_TOP3 = 80
XP_REFERRAL = 100
XP_ACHIEVEMENT = 25

LEVEL_XP_MULTIPLIER = 50
LEVEL_XP_THRESHOLDS: tuple[int, ...] = (0, 100, 300, 600, 1000, 1500, 2100, 2800, 3600, 4500)

MOOD_SLEEPY_INACTIVITY_DAYS = 7
MOOD_HEALTHY_SHARE_MIN = 0.30
MOOD_COZY_MIN_RECEIPTS = 2
MOOD_CHEERFUL_MIN_CATEGORIES = 5

LEAGUE_SIZE = 30
LEAGUE_PROMOTE_TOP = 7
LEAGUE_DEMOTE_BOTTOM = 5
LEAGUE_DIVISIONS_COUNT = 5
DIVISION_NAMES: dict[int, str] = {
    1: "бронза",
    2: "серебро",
    3: "золото",
    4: "платина",
    5: "алмаз",
}

LEAGUE_SCORE_SAVINGS_WEIGHT = 200
LEAGUE_SCORE_SAVINGS_RATE_CAP = 0.5
LEAGUE_SCORE_CHALLENGE_WEIGHT = 50
LEAGUE_SCORE_STREAK_WEIGHT = 10
LEAGUE_SCORE_STREAK_CAP = 5
LEAGUE_SCORE_RECEIPTS_WEIGHT = 5
LEAGUE_SCORE_RECEIPTS_CAP = 7

REFERRAL_MIN_FIRST_PURCHASE = 500
REFERRAL_SECOND_PURCHASE_MIN_DAYS = 7
REFERRAL_PAID_PER_MONTH = 5
REFERRAL_PAID_PER_YEAR = 20
REFERRAL_DORMANT_INACTIVITY_DAYS = 60
REFERRAL_HOLD_RECHECK_DAYS = 14

REFERRAL_REWARDS: dict[str, dict[str, int]] = {
    "new": {
        "referee_first_purchase_points": 200,
        "referrer_reward_points": 150,
        "referrer_reward_xp": 100,
    },
    "dormant": {
        "referee_first_purchase_points": 150,
        "referrer_reward_points": 150,
        "referrer_reward_xp": 100,
    },
    "active": {
        "referee_first_purchase_points": 0,
        "referrer_reward_points": 0,
        "referrer_reward_xp": 0,
    },
}

RECEIPT_SIGNALS: dict[str, dict[str, float | bool]] = {
    "burst_same_store": {"weight": 0.25, "strong": True},
    "daily_volume": {"weight": 0.35, "strong": True},
    "same_pos_share": {"weight": 0.30, "strong": True},
    "frequency_spike": {"weight": 0.20, "strong": False},
    "return_after_reward": {"weight": 0.25, "strong": True},
    "basket_monotony": {"weight": 0.15, "strong": False},
}

REFERRAL_SIGNALS: dict[str, dict[str, float | bool]] = {
    "shared_device": {"weight": 0.40, "strong": True},
    "instant_signup": {"weight": 0.15, "strong": False},
    "min_purchase_pattern": {"weight": 0.30, "strong": True},
    "invite_burst": {"weight": 0.20, "strong": False},
    "referral_ring": {"weight": 0.30, "strong": True},
    "same_store_zero_activity": {"weight": 0.15, "strong": False},
}

FRAUD_HOLD_THRESHOLD = 0.5
FRAUD_BLOCK_THRESHOLD = 0.8
FRAUD_BLOCK_MIN_STRONG = 2

ACHIEVEMENT_CODES: tuple[str, ...] = (
    "first_receipt",
    "first_challenge",
    "streak_4",
    "saver_1000",
    "explorer",
    "neighbour",
    "league_top3",
)
SAVER_1000_THRESHOLD_RUB = 1000
ACHIEVEMENT_EXPLORER_WINDOW_DAYS = 30

SIMULATION_DEFAULT_USERS = 5000
SIMULATION_DEFAULT_WEEKS = 8
SIMULATION_TREATMENT_SHARE = 0.30
SIMULATION_FREQUENCY_UPLIFT = 0.07
SIMULATION_UPLIFT_DECAY_MONTHLY = 0.10
SIMULATION_FRAUD_ACCOUNT_SHARE = 0.03
SIMULATION_FREQUENT_BUYER_THRESHOLD = 8

EVAL_HIT_RATE_TARGET = 0.70
EVAL_RELEVANCE_TOP_CATEGORIES = 5
TARGET_RATIO_MIN = 1.2
TARGET_RATIO_MAX = 2.0
TARGET_MAX_DELTA = 2


def level_for_xp(xp: int) -> int:
    level = 1
    while LEVEL_XP_MULTIPLIER * level * (level + 1) <= xp:
        level += 1
    return level


def xp_to_next_level(xp: int) -> int:
    level = level_for_xp(xp)
    if level >= len(LEVEL_XP_THRESHOLDS):
        return 0
    return LEVEL_XP_THRESHOLDS[level] - xp
