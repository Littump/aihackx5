from decimal import Decimal

import pytest

from app import game_rules
from app.features.challenges import candidate
from app.features.user_features.models import CategoryAffinity
from tests.unit.challenges.data import (
    BASELINE_FLOOR_CASES,
    CATEGORY_AFFINITY_CASES,
    FREQUENCY_DISABLED,
    FREQUENCY_HEADROOM_CASES,
    NO_HISTORY_FEATURES,
    RECENCY_BOUNDARY_CASES,
    TARGET_CASES,
    make_features,
)


@pytest.mark.parametrize(("baseline", "expected_target"), TARGET_CASES)
def test_compute_target_matches_prd_examples(baseline: Decimal, expected_target: Decimal) -> None:
    assert candidate.compute_target(baseline) == expected_target


def test_compute_target_of_default_baseline_matches_fallback_constant() -> None:
    default_baseline = Decimal(game_rules.CANDIDATE_DEFAULT_FREQUENCY_BASELINE)
    default_target = Decimal(game_rules.CANDIDATE_DEFAULT_FREQUENCY_TARGET)
    assert candidate.compute_target(default_baseline) == default_target


def test_compute_target_of_fractional_baseline_matches_economics_example() -> None:
    # DEF-2: domain-rules.md §6 подразумевает baseline 1.5 -> target 3, не 2.5
    assert candidate.compute_target(Decimal("1.5")) == Decimal("3")


@pytest.mark.parametrize(("frequency_per_week", "expected_included"), FREQUENCY_HEADROOM_CASES)
def test_build_frequency_headroom_boundary(
    frequency_per_week: Decimal, expected_included: bool
) -> None:
    features = make_features(frequency_per_week=frequency_per_week, recency_days=5)
    drafts = candidate.build(features)
    baseline = frequency_per_week.quantize(Decimal("0.1"))
    has_regular = any(d.type == "frequency" and d.baseline == baseline for d in drafts)
    assert has_regular is expected_included


@pytest.mark.parametrize(("recency_days", "expected_included"), RECENCY_BOUNDARY_CASES)
def test_build_frequency_recency_boundary(recency_days: int, expected_included: bool) -> None:
    features = make_features(frequency_per_week=Decimal("2"), recency_days=recency_days)
    drafts = candidate.build(features)
    has_regular = any(d.type == "frequency" and d.baseline == Decimal("2") for d in drafts)
    assert has_regular is expected_included


def test_build_frequency_candidate_matches_prd_example() -> None:
    features = make_features(frequency_per_week=Decimal("2"), recency_days=5)
    drafts = candidate.build(features)
    assert len(drafts) == 1
    draft = drafts[0]
    assert draft.type == "frequency"
    assert draft.category is None
    assert draft.baseline == Decimal("2")
    assert draft.target == Decimal("3")
    assert draft.rationale_features.frequency_per_week == 2.0
    assert draft.rationale_features.recency_days == 5


@pytest.mark.parametrize(
    ("category", "share", "visits", "expected_included"), CATEGORY_AFFINITY_CASES
)
def test_build_category_affinity_boundary(
    category: str, share: float, visits: int, expected_included: bool
) -> None:
    affinity = CategoryAffinity(share=share, visits=visits, cadence_days=7.0)
    features = make_features(
        frequency_per_week=FREQUENCY_DISABLED,
        recency_days=5,
        category_affinity={category: affinity},
    )
    drafts = candidate.build(features)
    has_category = any(d.type == "category" and d.category == category for d in drafts)
    assert has_category is expected_included


def test_build_multiple_category_candidates_one_per_category() -> None:
    features = make_features(
        frequency_per_week=FREQUENCY_DISABLED,
        recency_days=5,
        category_affinity={
            "dairy": CategoryAffinity(share=0.30, visits=6, cadence_days=5.0),
            "bakery": CategoryAffinity(share=0.15, visits=4, cadence_days=8.0),
        },
    )
    drafts = candidate.build(features)
    categories = sorted(d.category for d in drafts if d.type == "category" and d.category)
    assert categories == ["bakery", "dairy"]
    assert len(drafts) == 2


def test_build_fallback_for_new_user_without_history() -> None:
    drafts = candidate.build(NO_HISTORY_FEATURES)
    assert len(drafts) == 1
    draft = drafts[0]
    assert draft.type == "frequency"
    assert draft.category is None
    assert draft.baseline == Decimal("1")
    assert draft.target == Decimal("2")


@pytest.mark.parametrize(("frequency_per_week", "expected_baseline"), BASELINE_FLOOR_CASES)
def test_build_frequency_baseline_floors_at_minimum(
    frequency_per_week: Decimal, expected_baseline: Decimal
) -> None:
    features = make_features(frequency_per_week=frequency_per_week, recency_days=5)
    drafts = candidate.build(features)
    draft = next(d for d in drafts if d.type == "frequency")
    assert draft.baseline == expected_baseline


def test_build_frequency_priority_matches_formula() -> None:
    features = make_features(frequency_per_week=Decimal("3"), recency_days=5)
    drafts = candidate.build(features)
    draft = next(d for d in drafts if d.type == "frequency")
    assert draft.priority == pytest.approx(1.25)


def test_build_frequency_priority_at_zero_frequency() -> None:
    features = make_features(frequency_per_week=Decimal("0"), recency_days=5)
    drafts = candidate.build(features)
    draft = next(d for d in drafts if d.type == "frequency")
    assert draft.priority == pytest.approx(1.5)


def test_build_category_priority_matches_formula() -> None:
    affinity = CategoryAffinity(share=0.30, visits=6, cadence_days=5.0)
    features = make_features(
        frequency_per_week=FREQUENCY_DISABLED,
        recency_days=5,
        category_affinity={"dairy": affinity},
    )
    drafts = candidate.build(features)
    draft = next(d for d in drafts if d.type == "category")
    assert draft.priority == pytest.approx(1.1)
