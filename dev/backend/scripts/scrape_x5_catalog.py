import argparse
import json
import sys
from pathlib import Path
from typing import Any

import nodriver as driver
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.clock import now
from app.game_rules import CATEGORIES, CHALLENGE_EXCLUDED_CATEGORIES
from app.ml.schemas import SkuCatalogItem

CHROME_CANDIDATES: tuple[str, ...] = (
    "/nix/store/gj9a479g6hqba4wr8w0fgr7ncicrk84q-chromium-148.0.7778.167/bin/chromium",
    "/run/current-system/sw/bin/chromium",
    "/usr/bin/chromium",
    "/usr/bin/google-chrome-stable",
)
BASE_URL = "https://www.perekrestok.ru"

CATEGORY_MAP: dict[str, tuple[tuple[int, str], ...]] = {
    "dairy": (
        (114, "moloko"),
        (122, "syr"),
        (119, "jogurty"),
        (117, "tvorog"),
        (118, "smetana"),
        (121, "maslo"),
    ),
    "bakery": (
        (243, "hleb"),
        (246, "hlebobulocnye-izdelia"),
        (198, "pirogi-sdoba-keksy-rulety"),
        (244, "lavas-i-lepeski"),
    ),
    "fruits_veg": ((153, "frukty"), (150, "ovosi"), (151, "zelen-i-salaty"), (154, "agody")),
    "meat_fish": (
        (133, "kolbasa"),
        (134, "sosiski"),
        (138, "maso-pticy"),
        (139, "svinina"),
        (176, "ohlazdennaa-ryba"),
        (57, "ryba"),
    ),
    "grocery": (
        (105, "makarony"),
        (107, "krupy"),
        (104, "rastitelnoe-maslo"),
        (80, "kofe"),
        (82, "caj"),
        (221, "majonez"),
    ),
    "snacks": ((202, "cipsy"), (195, "sokolad"), (193, "konfety"), (197, "pecene"), (709, "sneki")),
    "drinks": (
        (208, "voda"),
        (211, "soki"),
        (209, "gazirovannye-napitki"),
        (206, "energeticeskie-napitki"),
    ),
    "alcohol": ((2, "vino"), (9, "pivo"), (6, "vodka"), (5, "viski")),
    "household": (
        (259, "dla-myta-posudy"),
        (237, "dla-stirki-i-uhoda-za-vesami"),
        (97, "bumaznaa-i-vatnaa-produkcia"),
        (241, "predmety-dla-uborki"),
    ),
    "beauty": (
        (86, "geli-dla-dusa"),
        (91, "uhod-dla-volos"),
        (89, "uhod-za-licom"),
        (92, "dezodoranty"),
    ),
    "ready_food": ((298, "susi-i-rolly"), (32, "salaty"), (169, "supy"), (306, "sendvici")),
    "other": (
        (37, "lampocki-i-batarejki"),
        (53, "kancelaria"),
        (165, "odnorazovaa-posuda"),
        (42, "vse-dla-prazdnika"),
    ),
}

EXTRACT_JS = r"""
(async () => {
  function num(el){
    if (!el) return null;
    const t = el.textContent.replace(/[^0-9,]/g, '').replace(',', '.');
    const v = parseFloat(t);
    return isFinite(v) ? v : null;
  }
  const cards = Array.from(document.querySelectorAll('.product-card'));
  const out = [];
  for (const c of cards){
    const link = c.querySelector('a.product-card__link');
    const href = link ? link.getAttribute('href') : '';
    const m = href.match(/-(\d+)$/);
    const pid = m ? parseInt(m[1]) : null;
    const titleEl = c.querySelector('.product-card__title')
      || c.querySelector('[class*="title" i]');
    let name = titleEl ? titleEl.textContent.trim() : '';
    if (!name || name === '18+') {
      const img = c.querySelector('img');
      name = img ? (img.getAttribute('alt') || img.getAttribute('title') || '') : '';
    }
    out.push({
      pid: pid,
      name: name.trim(),
      price_new: num(c.querySelector('.price-new')),
      price_old: num(c.querySelector('.price-old')),
    });
  }
  return JSON.stringify(out);
})()
"""

MIN_PRICE_RUB = 5.0
MAX_PRICE_RUB = 20000.0
PROMO_DEPTH_MIN = 0.05
PROMO_DEPTH_MAX = 0.6
PROMO_DEPTH_DEFAULT = 0.1
PER_CATEGORY_TARGET = 30
PER_CATEGORY_MIN = 18


class ScrapedProduct(BaseModel):
    source_id: int
    name: str
    price_new: float
    price_old: float | None
    internal_category: str


def _pick_chrome() -> str:
    for path in CHROME_CANDIDATES:
        if Path(path).exists():
            return path
    raise RuntimeError("chromium binary not found; edit CHROME_CANDIDATES")


def _looks_real(name: str) -> bool:
    letters = sum(1 for ch in name if ch.isalpha())
    return len(name) >= 4 and letters >= 3


def _regular_price(product: ScrapedProduct) -> float:
    if product.price_old and product.price_old > product.price_new:
        return product.price_old
    return product.price_new


def _promo_depth(product: ScrapedProduct) -> float:
    if product.price_old and product.price_old > product.price_new:
        depth = (product.price_old - product.price_new) / product.price_old
        return round(min(max(depth, PROMO_DEPTH_MIN), PROMO_DEPTH_MAX), 3)
    return PROMO_DEPTH_DEFAULT


async def _scrape_leaf(page: Any, cat_id: int, slug: str, internal: str) -> list[ScrapedProduct]:
    url = f"{BASE_URL}/cat/c/{cat_id}/{slug}"
    await page.get(url)
    await page.sleep(6)
    raw = await page.evaluate(EXTRACT_JS, await_promise=True)
    records = json.loads(raw)
    products: list[ScrapedProduct] = []
    for record in records:
        pid = record.get("pid")
        name = (record.get("name") or "").strip()
        price_new = record.get("price_new")
        if not isinstance(pid, int) or not price_new or not _looks_real(name):
            continue
        products.append(
            ScrapedProduct(
                source_id=pid,
                name=name,
                price_new=float(price_new),
                price_old=float(record["price_old"]) if record.get("price_old") else None,
                internal_category=internal,
            )
        )
    return products


def _dedupe_roundrobin(per_leaf: list[list[ScrapedProduct]], target: int) -> list[ScrapedProduct]:
    seen: set[int] = set()
    chosen: list[ScrapedProduct] = []
    index = 0
    while len(chosen) < target and any(index < len(leaf) for leaf in per_leaf):
        for leaf in per_leaf:
            if index < len(leaf):
                product = leaf[index]
                if product.source_id not in seen:
                    seen.add(product.source_id)
                    chosen.append(product)
                    if len(chosen) >= target:
                        break
        index += 1
    return chosen


def _to_catalog_item(product: ScrapedProduct, rank: int) -> SkuCatalogItem:
    eligible = product.internal_category not in CHALLENGE_EXCLUDED_CATEGORIES
    return SkuCatalogItem(
        sku_id=f"PX-{product.source_id}",
        name=product.name,
        category=product.internal_category,
        brand=None,
        regular_price=round(_regular_price(product), 2),
        typical_promo_depth=_promo_depth(product),
        is_challenge_eligible=eligible,
        popularity_rank=rank,
    )


def _validate(items: list[SkuCatalogItem]) -> None:
    if not 200 <= len(items) <= 500:
        raise ValueError(f"catalog size {len(items)} outside [200, 500]")
    categories = {item.category for item in items}
    if categories != set(CATEGORIES):
        raise ValueError(f"category coverage mismatch: {sorted(categories)}")
    ids = [item.sku_id for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate sku_id in catalog")
    for item in items:
        if not _looks_real(item.name):
            raise ValueError(f"implausible name: {item.name!r}")
        if not MIN_PRICE_RUB <= item.regular_price <= MAX_PRICE_RUB:
            raise ValueError(f"price out of range for {item.sku_id}: {item.regular_price}")
        if not 0.0 <= item.typical_promo_depth <= PROMO_DEPTH_MAX:
            raise ValueError(f"promo depth out of range for {item.sku_id}")
    alcohol = [item for item in items if item.category == "alcohol"]
    if not alcohol or any(item.is_challenge_eligible for item in alcohol):
        raise ValueError("alcohol must exist and be ineligible")
    for category in CATEGORIES:
        count = sum(1 for item in items if item.category == category)
        if count < PER_CATEGORY_MIN:
            raise ValueError(f"category {category} has only {count} items (min {PER_CATEGORY_MIN})")


async def scrape(target: int) -> list[SkuCatalogItem]:
    browser = await driver.start(browser_executable_path=_pick_chrome(), headless=False)
    items: list[SkuCatalogItem] = []
    try:
        page = await browser.get(BASE_URL)
        await page.sleep(6)
        for category in CATEGORIES:
            per_leaf: list[list[ScrapedProduct]] = []
            for cat_id, slug in CATEGORY_MAP[category]:
                leaf = await _scrape_leaf(page, cat_id, slug, category)
                print(f"  {category} <- /cat/c/{cat_id}/{slug}: {len(leaf)} products", flush=True)
                per_leaf.append(leaf)
            chosen = _dedupe_roundrobin(per_leaf, target)
            for local_rank, product in enumerate(chosen, start=1):
                items.append(_to_catalog_item(product, local_rank))
            print(f"{category}: kept {len(chosen)}", flush=True)
    finally:
        browser.stop()
    items.sort(key=lambda item: (item.category, item.popularity_rank))
    return items


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape real X5 Perekrestok SKUs into the ML catalog"
    )
    parser.add_argument("--out", type=Path, default=Path("app/ml/data/perekrestok_catalog.json"))
    parser.add_argument("--target-per-category", type=int, default=PER_CATEGORY_TARGET)
    args = parser.parse_args()

    items = driver.loop().run_until_complete(scrape(args.target_per_category))
    _validate(items)

    payload = {
        "source": "perekrestok.ru",
        "scraped_at": now().isoformat(),
        "count": len(items),
        "items": [item.model_dump() for item in items],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(items)} SKUs -> {args.out}")


if __name__ == "__main__":
    main()
