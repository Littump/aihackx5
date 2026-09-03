from app.ml import catalog as catalog_module
from app.ml import profiles as profiles_module


def test_catalog_is_deterministic() -> None:
    first = catalog_module.build_catalog(7)
    second = catalog_module.build_catalog(7)
    assert [item.model_dump() for item in first] == [item.model_dump() for item in second]


def test_catalog_size_and_categories() -> None:
    catalog = catalog_module.build_catalog(7)
    assert 200 <= len(catalog) <= 500
    categories = {item.category for item in catalog}
    assert len(categories) == 12


def test_alcohol_not_eligible() -> None:
    catalog = catalog_module.build_catalog(7)
    alcohol = [item for item in catalog if item.category == "alcohol"]
    assert alcohol
    assert all(not item.is_challenge_eligible for item in alcohol)
    eligible = catalog_module.eligible_catalog(catalog)
    assert all(item.category != "alcohol" for item in eligible)


def test_profiles_are_deterministic() -> None:
    first = profiles_module.build_profiles(7, 50)
    second = profiles_module.build_profiles(7, 50)
    assert [p.model_dump() for p in first] == [p.model_dump() for p in second]


def test_regular_mid_is_majority_segment() -> None:
    people = profiles_module.build_profiles(7, 400)
    share = sum(p.segment == "regular_mid" for p in people) / len(people)
    assert 0.48 <= share <= 0.72
