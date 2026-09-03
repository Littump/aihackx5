import random
from collections.abc import Awaitable, Callable

from app.core.errors import AppError

PSEUDONYM_MAX_ATTEMPTS = 50

ADJECTIVES: tuple[str, ...] = (
    "Уютный",
    "Тёплый",
    "Добрый",
    "Ласковый",
    "Заботливый",
    "Весёлый",
    "Хитрый",
    "Мудрый",
    "Пушистый",
    "Домашний",
    "Гостеприимный",
    "Приветливый",
    "Бережливый",
    "Хозяйственный",
    "Проворный",
    "Шустрый",
    "Скромный",
    "Смекалистый",
    "Рукастый",
    "Незаметный",
    "Тихий",
    "Ворчливый",
    "Дружелюбный",
    "Отзывчивый",
    "Верный",
    "Надёжный",
    "Загадочный",
    "Сказочный",
    "Волшебный",
    "Игривый",
    "Бодрый",
    "Спокойный",
    "Радушный",
    "Милый",
    "Кудрявый",
    "Полосатый",
    "Пузатый",
    "Усатый",
    "Румяный",
    "Плюшевый",
)

NOUNS: tuple[str, ...] = (
    "Домовой",
    "Уголок",
    "Огонёк",
    "Чердак",
    "Половик",
    "Сундучок",
    "Веник",
    "Самовар",
    "Валенок",
    "Тапочек",
    "Ковшик",
    "Ставень",
    "Погребок",
    "Чуланчик",
    "Хозяин",
    "Соседушка",
    "Печник",
    "Дворник",
    "Ключник",
    "Сторож",
    "Хранитель",
    "Затейник",
    "Проказник",
    "Шалунишка",
    "Замочек",
    "Половичок",
    "Коврик",
    "Подсвечник",
    "Колокольчик",
    "Клубочек",
    "Пирожок",
    "Калачик",
    "Пряничек",
    "Огород",
    "Дворик",
    "Забор",
    "Порожек",
    "Балкончик",
    "Чердачок",
    "Домик",
)

IsPseudonymTaken = Callable[[str], Awaitable[bool]]


def random_pseudonym() -> str:
    return f"{random.choice(ADJECTIVES)} {random.choice(NOUNS)}"


async def generate_unique_pseudonym(is_taken: IsPseudonymTaken) -> str:
    for _ in range(PSEUDONYM_MAX_ATTEMPTS):
        candidate = random_pseudonym()
        if not await is_taken(candidate):
            return candidate
    raise AppError("pseudonym_generation_failed", "не удалось подобрать уникальный псевдоним", 500)
