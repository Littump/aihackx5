from app.ml import profiles as profiles_module


def test_profile_has_peaky_persona_fields() -> None:
    profile = profiles_module.build_profiles(7, 1)[0]
    assert profile.archetype
    assert profile.persona_brief
    assert profile.deal_attitude in {"promo_skeptic", "selective", "deal_seeker"}
    assert 0.0 <= profile.routine_rigidity <= 1.0
    assert len(profile.favorite_categories) == 3


def test_favorite_categories_are_top_weighted() -> None:
    profile = profiles_module.build_profiles(7, 1)[0]
    top = sorted(profile.category_weights.items(), key=lambda item: item[1], reverse=True)[:3]
    assert profile.favorite_categories == [category for category, _ in top]


def test_deal_attitude_tracks_promo_sensitivity_buckets() -> None:
    people = profiles_module.build_profiles(7, 200)
    for person in people:
        if person.promo_sensitivity < 0.35:
            assert person.deal_attitude == "promo_skeptic"
        elif person.promo_sensitivity < 0.62:
            assert person.deal_attitude == "selective"
        else:
            assert person.deal_attitude == "deal_seeker"


def test_population_is_a_balanced_smart_money_spread() -> None:
    people = profiles_module.build_profiles(7, 400)
    total = len(people)
    deal_seekers = sum(person.deal_attitude == "deal_seeker" for person in people) / total
    selective = sum(person.deal_attitude == "selective" for person in people) / total
    skeptics = sum(person.deal_attitude == "promo_skeptic" for person in people) / total
    assert deal_seekers >= 0.20
    assert selective >= 0.35
    assert 0.12 <= skeptics <= 0.32
    assert deal_seekers > 0.0 and selective > 0.0 and skeptics > 0.0


def test_profiles_remain_deterministic() -> None:
    first = profiles_module.build_profiles(7, 30)
    second = profiles_module.build_profiles(7, 30)
    assert [p.model_dump() for p in first] == [p.model_dump() for p in second]
