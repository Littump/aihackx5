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
    assert "Молочное" in copy.title
    assert "dairy" not in copy.title
    assert "dairy" not in copy.body
    assert "dairy" not in copy.explanation


async def test_render_challenge_category_label_falls_back_to_raw_key_for_unknown_category() -> None:
    draft = make_draft(type="category", category="new_category", target=Decimal("2"), share=0.5)
    features = make_features()

    copy = await domovoy_copy.render_challenge(challenge=draft, features=features)

    assert "new_category" in copy.title


async def test_render_insight_contains_savings_amount_and_russian_period() -> None:
    features = make_features()
    savings = make_savings_summary(amount=Decimal("450.00"), period="month")

    text = await domovoy_copy.render_insight(features=features, savings=savings)

    assert "450" in text
    assert "месяц" in text
    assert "month" not in text
