from decimal import Decimal

import pytest

from app.features.challenges import economics
from app.features.challenges.models import ChallengeDraft, RationaleFeatures
from tests.unit.challenges.data import ECONOMICS_CASES, make_features


def _draft(baseline: Decimal, target: Decimal) -> ChallengeDraft:
    return ChallengeDraft(
        type="frequency",
        category=None,
        baseline=baseline,
        target=target,
        priority=1.0,
        rationale_features=RationaleFeatures(),
    )


@pytest.mark.parametrize(
    ("baseline", "target", "avg_basket", "expected_margin", "expected_max_reward", "_reward"),
    ECONOMICS_CASES,
)
def test_evaluate_matches_domain_rules_examples(
    baseline: Decimal,
    target: Decimal,
    avg_basket: Decimal,
    expected_margin: Decimal,
    expected_max_reward: Decimal,
    _reward: int,
) -> None:
    features = make_features(avg_basket=avg_basket)
    result = economics.evaluate(_draft(baseline, target), features)
    assert result.expected_incremental_margin == pytest.approx(float(expected_margin))
    assert result.max_reward_rub == pytest.approx(float(expected_max_reward))
    assert result.avg_basket == pytest.approx(float(avg_basket))
    assert result.contribution_margin == pytest.approx(0.15)


@pytest.mark.parametrize(
    ("_baseline", "_target", "_avg_basket", "_margin", "max_reward", "expected_reward"),
    ECONOMICS_CASES,
)
def test_max_reward_points_matches_domain_rules_examples(
    _baseline: Decimal,
    _target: Decimal,
    _avg_basket: Decimal,
    _margin: Decimal,
    max_reward: Decimal,
    expected_reward: int,
) -> None:
    assert economics.max_reward_points(max_reward) == expected_reward


def test_max_reward_points_never_exceeds_weekly_cap() -> None:
    assert economics.max_reward_points(Decimal("6000")) == 150


def test_challenge_economics_matches_contract_fields() -> None:
    features = make_features(avg_basket=Decimal("600"))
    result = economics.evaluate(_draft(Decimal("2"), Decimal("3")), features)
    # DEF-1: openapi.yaml ChallengeEconomics требует ещё max_reward_rub и reward_share_max
    contract_fields = {
        "avg_basket",
        "expected_incremental_purchases",
        "expected_incremental_margin",
        "max_reward_rub",
        "contribution_margin",
        "reward_share_max",
    }
    assert set(result.model_dump()) == contract_fields
