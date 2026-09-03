from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from app import game_rules
from app.features.challenges.models import ChallengeDraft, RationaleFeatures
from app.features.user_features.models import UserFeaturesRow

BASELINE_PRECISION = Decimal("0.1")


def build(features: UserFeaturesRow) -> list[ChallengeDraft]:
    drafts: list[ChallengeDraft] = []
    frequency_draft = _frequency_candidate(features)
    if frequency_draft is not None:
        drafts.append(frequency_draft)
    drafts.extend(_category_candidates(features))
    return drafts if drafts else [_fallback_candidate(features)]


def compute_target(base: Decimal) -> Decimal:
    multiplier = Decimal(str(game_rules.TARGET_MULTIPLIER))
    min_delta_target = base + game_rules.TARGET_MIN_DELTA
    raw_target = _ceil(max(base * multiplier, min_delta_target))
    ceiling = _ceil(base + game_rules.TARGET_CEILING_DELTA)
    return min(raw_target, ceiling)


def _ceil(value: Decimal) -> Decimal:
    return value.to_integral_value(rounding=ROUND_CEILING)


def _frequency_candidate(features: UserFeaturesRow) -> ChallengeDraft | None:
    if not _has_frequency_headroom(features):
        return None
    baseline = _frequency_baseline(features.frequency_per_week)
    return ChallengeDraft(
        type="frequency",
        category=None,
        baseline=baseline,
        target=compute_target(baseline),
        priority=_frequency_priority(features.frequency_per_week),
        rationale_features=RationaleFeatures(
            frequency_per_week=float(features.frequency_per_week),
            recency_days=features.recency_days,
        ),
    )


def _has_frequency_headroom(features: UserFeaturesRow) -> bool:
    if features.frequency_per_week >= game_rules.FREQUENCY_HEADROOM_MAX:
        return False
    return features.recency_days is not None and (
        features.recency_days <= game_rules.CANDIDATE_RECENCY_MAX_DAYS
    )


def _category_candidates(features: UserFeaturesRow) -> list[ChallengeDraft]:
    drafts: list[ChallengeDraft] = []
    for category in sorted(features.category_affinity):
        affinity = features.category_affinity[category]
        if not _has_category_affinity(category, affinity.share, affinity.visits):
            continue
        weekly_visits = Decimal(affinity.visits) / Decimal(features.window_weeks)
        drafts.append(
            ChallengeDraft(
                type="category",
                category=category,
                baseline=weekly_visits,
                target=compute_target(weekly_visits),
                priority=game_rules.PRIORITY_CATEGORY_BASE + affinity.share,
                rationale_features=RationaleFeatures(share=affinity.share, visits=affinity.visits),
            )
        )
    return drafts


def _has_category_affinity(category: str, share: float, visits: int) -> bool:
    if category in game_rules.CHALLENGE_EXCLUDED_CATEGORIES:
        return False
    if share < game_rules.CANDIDATE_CATEGORY_MIN_SHARE:
        return False
    return visits >= game_rules.CANDIDATE_CATEGORY_MIN_VISITS


def _fallback_candidate(features: UserFeaturesRow) -> ChallengeDraft:
    baseline = Decimal(game_rules.CANDIDATE_DEFAULT_FREQUENCY_BASELINE)
    target = Decimal(game_rules.CANDIDATE_DEFAULT_FREQUENCY_TARGET)
    return ChallengeDraft(
        type="frequency",
        category=None,
        baseline=baseline,
        target=target,
        priority=_frequency_priority(features.frequency_per_week),
        rationale_features=RationaleFeatures(
            frequency_per_week=float(features.frequency_per_week),
            recency_days=features.recency_days,
        ),
    )


def _frequency_baseline(frequency_per_week: Decimal) -> Decimal:
    rounded = frequency_per_week.quantize(BASELINE_PRECISION, rounding=ROUND_HALF_UP)
    return max(rounded, Decimal(game_rules.FREQUENCY_BASELINE_MIN))


def _frequency_priority(frequency_per_week: Decimal) -> float:
    headroom_ratio = float(frequency_per_week) / game_rules.FREQUENCY_HEADROOM_MAX
    weighted_headroom = game_rules.PRIORITY_FREQUENCY_HEADROOM_WEIGHT * (1 - headroom_ratio)
    return game_rules.PRIORITY_FREQUENCY_BASE + weighted_headroom
