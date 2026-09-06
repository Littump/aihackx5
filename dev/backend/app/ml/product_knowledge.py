from app.ml import config

CATEGORY_LABEL_RU: dict[str, str] = {
    "dairy": "молочка",
    "bakery": "выпечка и хлеб",
    "fruits_veg": "овощи и фрукты",
    "meat_fish": "мясо и рыба",
    "grocery": "бакалея",
    "snacks": "снеки и сладкое",
    "drinks": "напитки",
    "alcohol": "алкоголь",
    "household": "бытовая химия",
    "beauty": "косметика и уход",
    "ready_food": "готовая еда",
    "other": "разное",
}

CATEGORY_EXAMPLES_RU: dict[str, str] = {
    "dairy": "молоко, творог, сыр, йогурт, сметана",
    "bakery": "хлеб, батон, булочки, слойки",
    "fruits_veg": "бананы, огурцы, помидоры, яблоки, салат",
    "meat_fish": "курица, фарш, сосиски, рыба",
    "grocery": "гречка, макароны, подсолнечное масло, кофе, консервы",
    "snacks": "чипсы, шоколад, печенье, конфеты",
    "drinks": "вода, сок, кола, энергетики",
    "alcohol": "пиво, вино, водка",
    "household": "стиральный порошок, средство для посуды, салфетки",
    "beauty": "шампунь, гель для душа, дезодорант",
    "ready_food": "готовые салаты, онигири, роллы, супы — взял и поел, готовить не надо",
    "other": "батарейки, одноразовая посуда, мелочи для дома",
}


class RewardTier:
    def __init__(
        self, level_label: str, margin_pct: int, abs_cap_rub: int, max_points: int
    ) -> None:
        self.level_label = level_label
        self.margin_pct = margin_pct
        self.abs_cap_rub = abs_cap_rub
        self.max_points = max_points


REWARD_LADDER: tuple[RewardTier, ...] = (
    RewardTier("L1", 15, 10, 100),
    RewardTier("L2", 20, 15, 150),
    RewardTier("L3", 25, 20, 200),
    RewardTier("L4", 30, 25, 250),
    RewardTier("L5", 35, 30, 300),
    RewardTier("L6", 40, 40, 400),
    RewardTier("L7+", 45, 50, 500),
)


CATEGORY_LABEL_RU_ACC: dict[str, str] = {
    "dairy": "молочку",
    "bakery": "выпечку и хлеб",
    "fruits_veg": "овощи и фрукты",
    "meat_fish": "мясо и рыбу",
    "grocery": "бакалею",
    "snacks": "снеки и сладкое",
    "drinks": "напитки",
    "alcohol": "алкоголь",
    "household": "бытовую химию",
    "beauty": "косметику и уход",
    "ready_food": "готовую еду",
    "other": "разное",
}


def category_ru(category: str | None) -> str:
    if category is None:
        return "любимые продукты"
    return CATEGORY_LABEL_RU.get(category, category)


def category_ru_acc(category: str | None) -> str:
    if category is None:
        return "любимые продукты"
    return CATEGORY_LABEL_RU_ACC.get(category, category_ru(category))


def category_examples(category: str | None) -> str:
    if category is None:
        return "твои обычные продукты"
    return CATEGORY_EXAMPLES_RU.get(category, category_ru(category))


def reward_tier_for_level(level: int) -> RewardTier:
    index = min(max(level, 1), len(REWARD_LADDER)) - 1
    return REWARD_LADDER[index]


def category_glossary_lines() -> list[str]:
    lines: list[str] = []
    for category in config.CATEGORIES:
        if category in config.EXCLUDED_CATEGORIES:
            continue
        lines.append(f"- {category} ({category_ru(category)}): {category_examples(category)}")
    return lines
