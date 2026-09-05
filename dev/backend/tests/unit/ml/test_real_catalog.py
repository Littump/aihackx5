from app.ml import catalog as catalog_module
from app.ml.schemas import SkuCatalogItem


def _has_cyrillic(text: str) -> bool:
    return any("\u0400" <= ch <= "\u04ff" for ch in text)


def test_catalog_source_is_real_perekrestok() -> None:
    scraped = catalog_module._load_scraped()
    assert scraped.source == "perekrestok.ru"
    assert scraped.count == len(scraped.items)


def test_sku_ids_are_real_and_unique() -> None:
    catalog = catalog_module.build_catalog(7)
    assert all(item.sku_id.startswith("PX-") for item in catalog)
    ids = [item.sku_id for item in catalog]
    assert len(ids) == len(set(ids))


def test_names_are_real_product_titles() -> None:
    catalog = catalog_module.build_catalog(7)
    cyrillic_share = sum(_has_cyrillic(item.name) for item in catalog) / len(catalog)
    assert cyrillic_share >= 0.9
    assert all(len(item.name) >= 4 for item in catalog)


def test_prices_and_promo_depth_in_range() -> None:
    catalog = catalog_module.build_catalog(7)
    assert all(item.regular_price > 0 for item in catalog)
    assert all(5.0 <= item.regular_price <= 20000.0 for item in catalog)
    assert all(0.0 <= item.typical_promo_depth <= 0.6 for item in catalog)


def test_eligible_catalog_excludes_alcohol_and_is_nonempty() -> None:
    catalog = catalog_module.build_catalog(7)
    eligible = catalog_module.eligible_catalog(catalog)
    assert eligible
    assert all(item.category != "alcohol" for item in eligible)


def test_every_category_has_minimum_depth() -> None:
    catalog = catalog_module.build_catalog(7)
    counts: dict[str, int] = {}
    for item in catalog:
        counts[item.category] = counts.get(item.category, 0) + 1
    assert all(count >= 18 for count in counts.values())


def test_sample_item_shape() -> None:
    catalog = catalog_module.build_catalog(7)
    item = catalog[0]
    assert isinstance(item, SkuCatalogItem)
    assert item.brand is None or isinstance(item.brand, str)
