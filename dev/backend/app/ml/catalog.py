from functools import lru_cache
from pathlib import Path

from app.ml import config
from app.ml.schemas import ScrapedCatalog, SkuCatalogItem

CATALOG_PATH = Path(__file__).parent / "data" / "perekrestok_catalog.json"


@lru_cache(maxsize=1)
def _load_scraped() -> ScrapedCatalog:
    if not CATALOG_PATH.exists():
        raise FileNotFoundError(
            f"real SKU catalog missing at {CATALOG_PATH}; "
            "run `uv run --with nodriver python scripts/scrape_x5_catalog.py`"
        )
    return ScrapedCatalog.model_validate_json(CATALOG_PATH.read_text(encoding="utf-8"))


def _with_eligibility(item: SkuCatalogItem) -> SkuCatalogItem:
    eligible = item.category not in config.EXCLUDED_CATEGORIES
    if eligible == item.is_challenge_eligible:
        return item
    return item.model_copy(update={"is_challenge_eligible": eligible})


def build_catalog(seed: int) -> list[SkuCatalogItem]:
    items = [_with_eligibility(item) for item in _load_scraped().items]
    items.sort(key=lambda item: (item.category, item.popularity_rank))
    return items


def eligible_catalog(catalog: list[SkuCatalogItem]) -> list[SkuCatalogItem]:
    eligible = [item for item in catalog if item.is_challenge_eligible]
    eligible.sort(key=lambda item: (item.popularity_rank, item.sku_id))
    return eligible
