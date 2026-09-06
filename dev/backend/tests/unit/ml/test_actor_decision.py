from app.ml import tracing
from app.ml.schemas import OfferResponse, PromoDecision


def _response(promo_decision: PromoDecision, completed: bool) -> OfferResponse:
    return OfferResponse(
        thinking="t",
        promo_decision=promo_decision,
        extra_visits=0,
        completed_challenge=completed,
        rationale="r",
    )


def test_refused_challenge_is_not_completed() -> None:
    decision = tracing.actor_decision(_response("buy_as_usual", True), "actor_llm")
    assert decision.engaged is False
    assert decision.completed_challenge is False


def test_ignored_challenge_is_not_completed() -> None:
    decision = tracing.actor_decision(_response("ignore", True), "actor_llm")
    assert decision.completed_challenge is False


def test_engaged_completion_is_preserved() -> None:
    decision = tracing.actor_decision(_response("use_offer", True), "actor_llm")
    assert decision.engaged is True
    assert decision.completed_challenge is True
