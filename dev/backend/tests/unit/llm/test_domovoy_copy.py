from decimal import Decimal

from app.llm import domovoy_copy
from tests.unit.challenges.data import make_draft, make_features
from tests.unit.llm.data import make_savings_summary


async def test_render_challenge_frequency_explanation_has_rationale_number() -> None:
    draft = make_draft(
        type="frequency", baseline=Decimal("2"), target=Decimal("3"), frequency_per_week=2.0
    )
    features = make_features(frequency_per_week=Decimal("2"))

    copy = await domovoy_copy.render_challenge(challenge=draft, features=features)

    assert copy.source == "template"
    assert "2.0" in copy.explanation
    assert copy.title and copy.body


async def test_render_challenge_category_explanation_has_rationale_number() -> None:
    draft = make_draft(type="category", category="dairy", target=Decimal("4"), share=0.30, visits=6)
    features = make_features()

    copy = await domovoy_copy.render_challenge(challenge=draft, features=features)

    assert copy.source == "template"
    assert "30" in copy.explanation
    assert "dairy" in copy.title


async def test_render_insight_contains_savings_amount() -> None:
    features = make_features()
    savings = make_savings_summary(amount=Decimal("450.00"))

    text = await domovoy_copy.render_insight(features=features, savings=savings)

    assert "450" in text
