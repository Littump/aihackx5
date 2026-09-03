import random

from app.ml import config
from app.ml.schemas import SkuCatalogItem

_BRANDS_BY_CATEGORY: dict[str, tuple[str, ...]] = {
    "dairy": ("Простоквашино", "Домик в деревне", "Весёлый молочник", "Чабан"),
    "bakery": ("Хлебный дом", "Коломенское", "Fazer", "Черёмушки"),
    "fruits_veg": ("Дядя Ваня", "Global Village", "6 соток", "Bonduelle"),
    "meat_fish": ("Мираторг", "Останкино", "Черкизово", "Агама"),
    "grocery": ("Makfa", "Мистраль", "Heinz", "Барилла"),
    "snacks": ("Lays", "Чипсоны", "Barni", "Alpen Gold"),
    "drinks": ("Добрый", "BonAqua", "Rich", "Жокей"),
    "alcohol": ("Балтика", "Абрау-Дюрсо", "Жигули", "Три медведя"),
    "household": ("Fairy", "Tide", "Zewa", "Domestos"),
    "beauty": ("Nivea", "Palmolive", "Чистая линия", "Head&Shoulders"),
    "ready_food": ("ВкусВилл", "Мираторг", "Шеф Перекрёсток", "Индилайт"),
    "other": ("X5", "Global Village", "Красная цена", "Каждый день"),
}
_ITEM_NOUNS: dict[str, tuple[str, ...]] = {
    "dairy": ("Молоко 3.2%", "Кефир 2.5%", "Творог 5%", "Йогурт", "Сметана 15%", "Сыр"),
    "bakery": ("Хлеб бородинский", "Батон нарезной", "Булочка", "Лаваш", "Багет"),
    "fruits_veg": ("Бананы", "Яблоки", "Томаты", "Огурцы", "Морковь", "Картофель"),
    "meat_fish": ("Куриное филе", "Фарш говяжий", "Форель", "Свинина", "Сосиски"),
    "grocery": ("Макароны", "Рис", "Гречка", "Масло подсолнечное", "Соус", "Сахар"),
    "snacks": ("Чипсы", "Печенье", "Шоколад", "Орешки", "Батончик"),
    "drinks": ("Сок апельсиновый", "Вода 1.5л", "Чай чёрный", "Кофе", "Морс"),
    "alcohol": ("Пиво 0.5л", "Вино красное", "Сидр", "Игристое"),
    "household": (
        "Средство для мытья посуды",
        "Стиральный порошок",
        "Бумага туалетная",
        "Салфетки",
    ),
    "beauty": ("Крем для рук", "Гель для душа", "Шампунь", "Зубная паста"),
    "ready_food": ("Салат Цезарь", "Плов готовый", "Суп-пюре", "Сэндвич"),
    "other": ("Батарейки AA", "Пакет-майка", "Спички", "Зажигалка"),
}
_VOLUME_HINTS: tuple[str, ...] = ("500мл", "930мл", "1л", "250г", "400г", "1кг", "0.5л", "200г")
_BASE_PRICE_RUB: dict[str, tuple[int, int]] = {
    "dairy": (55, 260),
    "bakery": (30, 150),
    "fruits_veg": (40, 320),
    "meat_fish": (160, 720),
    "grocery": (45, 340),
    "snacks": (55, 300),
    "drinks": (40, 340),
    "alcohol": (90, 900),
    "household": (90, 520),
    "beauty": (110, 640),
    "ready_food": (120, 480),
    "other": (25, 300),
}


def build_catalog(seed: int) -> list[SkuCatalogItem]:
    rng = random.Random(seed)
    items: list[SkuCatalogItem] = []
    rank = 1
    for category in config.CATEGORIES:
        count = rng.randint(config.CATALOG_MIN_PER_CATEGORY, config.CATALOG_MAX_PER_CATEGORY)
        eligible = category not in config.EXCLUDED_CATEGORIES
        for local_index in range(count):
            items.append(_build_item(rng, category, eligible, local_index, rank))
            rank += 1
    items.sort(key=lambda item: (item.category, item.popularity_rank))
    return items


def _build_item(
    rng: random.Random, category: str, eligible: bool, local_index: int, rank: int
) -> SkuCatalogItem:
    brand = rng.choice(_BRANDS_BY_CATEGORY[category])
    noun = _ITEM_NOUNS[category][local_index % len(_ITEM_NOUNS[category])]
    volume = rng.choice(_VOLUME_HINTS)
    low, high = _BASE_PRICE_RUB[category]
    price = round(rng.uniform(low, high), 2)
    promo_depth = round(rng.uniform(0.05, 0.35), 3)
    sku_id = f"{category.upper()[:4]}-{rank:04d}"
    return SkuCatalogItem(
        sku_id=sku_id,
        name=f"{noun} {brand} {volume}",
        category=category,
        brand=brand,
        regular_price=price,
        typical_promo_depth=promo_depth,
        is_challenge_eligible=eligible,
        popularity_rank=local_index + 1,
    )


def eligible_catalog(catalog: list[SkuCatalogItem]) -> list[SkuCatalogItem]:
    eligible = [item for item in catalog if item.is_challenge_eligible]
    eligible.sort(key=lambda item: (item.popularity_rank, item.sku_id))
    return eligible
