from app.ml import persona
from app.ml import profiles as profiles_module

_JARGON = (
    "segment",
    "dormant",
    "regular_mid",
    "promo_skeptic",
    "deal_seeker",
    "selective",
    "promo_sensitivity",
    "routine_rigidity",
    "churn",
    "responsiveness",
    "сегмент",
    "отзывчивост",
    "рутинност",
)


def _has_jargon(text: str) -> bool:
    low = text.lower()
    return any(term in low for term in _JARGON)


def test_fallback_persona_is_deterministic() -> None:
    profile = profiles_module.build_profiles(7, 5)[2]
    first = persona.build_fallback_persona(profile)
    second = persona.build_fallback_persona(profile)
    assert first.model_dump() == second.model_dump()


def test_fallback_persona_has_no_machine_jargon() -> None:
    for profile in profiles_module.build_profiles(7, 12):
        text = persona.build_fallback_persona(profile).model_dump_json()
        assert not _has_jargon(text)


def test_render_persona_block_is_human_and_named() -> None:
    profile = profiles_module.build_profiles(7, 3)[0]
    persona_obj = persona.build_fallback_persona(profile)
    block = persona.render_persona_block(persona_obj)
    assert persona_obj.full_name in block
    assert not _has_jargon(block)
    assert profile.deal_attitude not in block


def test_parse_persona_rejects_garbage_and_accepts_valid() -> None:
    assert persona.parse_persona(None) is None
    assert persona.parse_persona({"full_name": "x"}) is None
    profile = profiles_module.build_profiles(7, 1)[0]
    valid = persona.build_fallback_persona(profile).model_dump()
    assert persona.parse_persona(valid) is not None


def test_persona_batch_round_trips_and_books_by_id() -> None:
    people = profiles_module.build_profiles(7, 4)
    records = [
        persona.PersonaRecord(
            profile_id=profile.profile_id,
            segment=profile.segment,
            deal_attitude=profile.deal_attitude,
            source="fallback",
            persona=persona.build_fallback_persona(profile),
        )
        for profile in people
    ]
    batch = persona.PersonaBatch(
        seed=7,
        count=len(people),
        persona_model="test",
        generated=0,
        fallback=len(people),
        records=records,
    )
    restored = persona.PersonaBatch.model_validate_json(batch.model_dump_json())
    book = persona.persona_book(restored)
    assert set(book) == {p.profile_id for p in people}
    assert book[people[0].profile_id].full_name == records[0].persona.full_name
