import asyncio
import random
from pathlib import Path

from pydantic import BaseModel

from app.ml import config, llm_client, tool_schemas
from app.ml.llm_client import ChatClient
from app.ml.schemas import DealAttitude, Segment, UserProfile

_SCHEMA_NAME = "persona"


class Persona(BaseModel):
    full_name: str
    age: int
    occupation: str
    income_band: str
    household: str
    city_type: str
    neighborhood_context: str
    life_context: str
    money_mindset: str
    promo_attitude: str
    loyalty_app_habit: str
    store_relationship: str
    jobs_to_be_done: list[str]
    shopping_routine: str
    favorite_food_story: str
    quirks: list[str]
    what_makes_them_engage: str
    what_they_ignore: str
    voice: str


class PersonaRecord(BaseModel):
    profile_id: str
    segment: Segment
    deal_attitude: DealAttitude
    source: str
    persona: Persona


class PersonaBatch(BaseModel):
    seed: int
    count: int
    persona_model: str
    generated: int
    fallback: int
    records: list[PersonaRecord]


_CATEGORY_RU: dict[str, str] = {
    "dairy": "молочка",
    "bakery": "выпечка и хлеб",
    "fruits_veg": "овощи и фрукты",
    "meat_fish": "мясо и рыба",
    "grocery": "бакалея (крупы, макароны, консервы)",
    "snacks": "снеки и сладкое",
    "drinks": "напитки",
    "alcohol": "алкоголь",
    "household": "бытовая химия и хозтовары",
    "beauty": "косметика и уход",
    "ready_food": "готовая еда и кулинария",
    "other": "разное",
}

_ACTIVITY_HINT: dict[Segment, str] = {
    "regular_mid": "ходит стабильно, это его обычный магазин, примерно раз в неделю-полторы",
    "light": "заходит редко и коротко, по мелочи и по пути; магазин для него не главный",
    "heavy": "ходит часто и закупается основательно, планирует корзину заранее",
    "dormant": (
        "почти перестал ходить, ежедневная рутина ушла к другому магазину у дома, "
        "дрейфует к конкуренту"
    ),
}

_DEAL_HINT: dict[DealAttitude, str] = {
    "promo_skeptic": (
        "ценит время и не любит возню со скидками, берёт привычное на автомате; "
        "но очевидную выгоду без лишних движений не упустит"
    ),
    "selective": (
        "считает деньги с умом: включается, когда скидка реально попадает в его корзину и вовремя; "
        "за всем подряд не гоняется"
    ),
    "deal_seeker": (
        "осознанно управляет расходами: держит приложение под рукой, следит за баллами и кэшбэком "
        "и с удовольствием собирает выгодные предложения на нужное"
    ),
}
_MONEY_MINDSET: dict[DealAttitude, str] = {
    "promo_skeptic": "деньги считает, но возиться со скидками некогда — время дороже",
    "selective": "деньгами распоряжается с умом, тратит там, где выгода реальная",
    "deal_seeker": "управляет деньгами осознанно: планирует бюджет, ловит баллы и кэшбэк",
}
_LOYALTY_HABIT: dict[DealAttitude, str] = {
    "promo_skeptic": "карта есть, приложение открывает редко, баллы копятся сами по себе",
    "selective": "приложением пользуется по делу, купоны активирует, когда попадают в нужное",
    "deal_seeker": "приложение всегда под рукой, баллы и кэшбэк отслеживает и тратит с толком",
}
_ENGAGE_HINT: dict[DealAttitude, str] = {
    "promo_skeptic": "выгода на привычное без лишних движений и когда магазин по пути",
    "selective": "скидка точно на то, что и так берёт, вовремя и без беготни",
    "deal_seeker": "ощутимая выгода, баллы и кэшбэк на нужное — ради этого спланирует поход",
}
_VOICE_HINT: dict[DealAttitude, str] = {
    "promo_skeptic": (
        "За акциями особо не гоняюсь, беру привычное, чтобы не тратить время. "
        "Но если реально выгодно и по пути — почему нет."
    ),
    "selective": (
        "Скидки смотрю, но с головой: беру то, что и так нужно, просто дешевле. "
        "За всем подряд не бегаю."
    ),
    "deal_seeker": (
        "Люблю, когда всё продумано: баллы, кэшбэк, купоны — всё в дело. "
        "Ради хорошей выгоды могу и маршрут подстроить."
    ),
}


def _promo_clause(promo_sensitivity: float) -> str:
    if promo_sensitivity >= 0.6:
        return " если акция реально выгодна — берёт впрок"
    if promo_sensitivity < 0.33:
        return " легко проходит мимо большинства акций"
    return " на пару-тройку акций в месяц всё же клюёт"


def _routine_hint(routine_rigidity: float) -> str:
    if routine_rigidity >= 0.7:
        return "живёт по жёсткой рутине, один и тот же маршрут и набор, перемены даются тяжело"
    if routine_rigidity >= 0.45:
        return "есть привычный уклад, но при поводе может отступить от него"
    return "гибкий, легко меняет планы, магазины и набор покупок"


def _tenure_hint(tenure_weeks: int) -> str:
    if tenure_weeks >= 26:
        return "давно в программе лояльности, карта примелькалась"
    if tenure_weeks >= 10:
        return "уже не новичок в программе, но без фанатизма"
    return "относительно недавно завёл карту"


def _favorite_hint(favorite_categories: list[str]) -> str:
    words = [_CATEGORY_RU.get(category, category) for category in favorite_categories]
    return ", ".join(words) if words else "обычный продуктовый набор"


_DEMOGRAPHIC_ARCHETYPES: tuple[str, ...] = (
    "женщина 22–28, маркетолог или SMM-специалист, живёт в приложениях и ловит акции",
    "мужчина 24–30, разработчик или тестировщик в IT, привык к кэшбэку и подпискам",
    "женщина 26–33, продакт- или проджект-менеджер, планирует бюджет в приложении банка",
    "мужчина 21–26, студент старших курсов с подработкой, считает каждую тысячу",
    "женщина 19–24, студентка, живёт на стипендию и подработку, ловит студенческие скидки",
    "мужчина 27–34, фрилансер или самозанятый, доход плавает, оптимизирует расходы",
    "женщина 28–35, junior-руководитель или тимлид, времени мало, но выгоду не упускает",
    "мужчина 25–31, курьер или водитель, отслеживает промо и кэшбэк на еду",
    "женщина 24–30, медсестра или фельдшер, работает сменами, аккуратно ведёт бюджет",
    "мужчина 23–29, инженер или мастер на производстве, копит на крупные цели",
    "женщина 30–37, специалист в финансах или бухгалтерии, считает всё до копейки",
    "мужчина 29–36, менеджер по продажам, любит бонусные программы и баллы",
    "женщина 25–32, дизайнер или контент-мейкер на удалёнке, подписки и кэшбэк-карты",
    "мужчина 22–28, аспирант или молодой преподаватель, экономит осознанно",
    "женщина 27–34, молодая мама в декрете, оптимизирует семейный бюджет через приложения",
    "мужчина 26–33, специалист техподдержки или сервиса, следит за скидками на привычное",
    "женщина 20–25, бариста или продавец в ритейле, откладывает и ловит выгодное",
    "мужчина 31–38, семейный, в найме, считает расходы на семью с двумя детьми",
)


def _demographic_hint(profile_id: str) -> str:
    rng = random.Random(f"{profile_id}:demographics")
    return rng.choice(_DEMOGRAPHIC_ARCHETYPES)


def render_persona_prompt(profile: UserProfile) -> tuple[str, str]:
    system_prompt = llm_client.load_prompt("persona_system.md")
    template = llm_client.load_prompt("persona_user.md")
    deal_hint = _DEAL_HINT[profile.deal_attitude] + "," + _promo_clause(profile.promo_sensitivity)
    user_prompt = template.format(
        demographic_hint=_demographic_hint(profile.profile_id),
        activity_hint=_ACTIVITY_HINT[profile.segment],
        visits_hint=f"{profile.visits_per_week:.1f} визита в неделю",
        basket_hint=f"{profile.avg_basket:.0f}",
        deal_hint=deal_hint,
        routine_hint=_routine_hint(profile.routine_rigidity),
        tenure_hint=_tenure_hint(profile.tenure_weeks),
        favorite_hint=_favorite_hint(profile.favorite_categories),
    )
    return system_prompt, user_prompt


def parse_persona(payload: dict[str, object] | None) -> Persona | None:
    if payload is None:
        return None
    try:
        return Persona.model_validate(payload)
    except ValueError:
        return None


async def generate_persona(client: ChatClient, profile: UserProfile) -> Persona | None:
    system_prompt, user_prompt = render_persona_prompt(profile)
    schema = tool_schemas.persona_schema()
    for attempt in range(config.PERSONA_RETRY_MAX + 1):
        result = await client.emit_json(
            system_prompt,
            user_prompt,
            _SCHEMA_NAME,
            schema,
            temperature=config.PERSONA_TEMPERATURE,
            max_tokens=config.PERSONA_MAX_TOKENS,
            top_p=config.PERSONA_TOP_P,
            enable_thinking=config.PERSONA_ENABLE_THINKING,
        )
        persona = parse_persona(result.parsed)
        if persona is not None:
            return persona
        if attempt < config.PERSONA_RETRY_MAX:
            await asyncio.sleep(config.PERSONA_RETRY_BACKOFF_S * (attempt + 1))
    return None


async def generate_personas(
    client: ChatClient,
    profiles: list[UserProfile],
    seed: int,
    concurrency: int = config.PERSONA_MAX_CONCURRENCY,
) -> PersonaBatch:
    semaphore = asyncio.Semaphore(max(1, concurrency))

    async def _one(profile: UserProfile) -> PersonaRecord:
        async with semaphore:
            persona = await generate_persona(client, profile)
        if persona is None:
            return PersonaRecord(
                profile_id=profile.profile_id,
                segment=profile.segment,
                deal_attitude=profile.deal_attitude,
                source="fallback",
                persona=build_fallback_persona(profile),
            )
        return PersonaRecord(
            profile_id=profile.profile_id,
            segment=profile.segment,
            deal_attitude=profile.deal_attitude,
            source="llm",
            persona=persona,
        )

    records = await asyncio.gather(*[_one(profile) for profile in profiles])
    generated = sum(1 for record in records if record.source == "llm")
    return PersonaBatch(
        seed=seed,
        count=len(profiles),
        persona_model=client.model,
        generated=generated,
        fallback=len(profiles) - generated,
        records=list(records),
    )


def load_persona_batch(path: Path) -> PersonaBatch:
    return PersonaBatch.model_validate_json(path.read_text(encoding="utf-8"))


def persona_book(batch: PersonaBatch) -> dict[str, Persona]:
    return {record.profile_id: record.persona for record in batch.records}


_MALE_NAMES = ("Артём", "Сергей", "Дмитрий", "Николай", "Павел", "Игорь", "Роман", "Андрей")
_FEMALE_NAMES = ("Марина", "Ольга", "Наталья", "Елена", "Ирина", "Светлана", "Татьяна", "Юлия")
_SURNAMES = ("Соболев", "Гурьев", "Ковалёв", "Зимин", "Панов", "Лапин", "Ерохин", "Седов")
_CITIES = ("Самара", "Воронеж", "Пермь", "Тула", "Рязань", "Киров", "Пенза", "Курск")
_JOBS = (
    "маркетолог",
    "разработчик",
    "продакт-менеджер",
    "курьер",
    "фрилансер-дизайнер",
    "менеджер по продажам",
    "медсестра",
    "бариста",
    "тестировщик",
    "специалист техподдержки",
    "SMM-специалист",
    "студент с подработкой",
)


def build_fallback_persona(profile: UserProfile) -> Persona:
    rng = random.Random(f"{profile.profile_id}:persona-fallback")
    female = rng.random() < 0.5
    first = rng.choice(_FEMALE_NAMES if female else _MALE_NAMES)
    surname = rng.choice(_SURNAMES) + ("а" if female else "")
    city = rng.choice(_CITIES)
    job = rng.choice(_JOBS)
    base_age = 21 + profile.tenure_weeks // 8 + rng.randint(0, 8)
    if rng.random() < 0.18:
        base_age += rng.randint(4, 10)
    age = min(44, base_age)
    foods = _favorite_hint(profile.favorite_categories)
    deal_hint = _DEAL_HINT[profile.deal_attitude]
    activity = _ACTIVITY_HINT[profile.segment]
    basket = f"{profile.avg_basket:.0f}"
    visits = f"{profile.visits_per_week:.1f}"
    return Persona(
        full_name=f"{first} {surname}",
        age=age,
        occupation=job,
        income_band="доход средний по городу, деньгами распоряжается по плану",
        household=rng.choice(
            (
                "живёт с семьёй",
                "живёт один",
                "с женой и ребёнком-школьником",
                "снимает квартиру с партнёром",
            )
        ),
        city_type=f"{city}, спальный район, магазин недалеко от дома",
        neighborhood_context=(
            "рядом есть и другой продуктовый, выбор часто решает, что ближе по пути"
        ),
        life_context=f"обычная рабочая неделя, {activity}",
        money_mindset=_MONEY_MINDSET[profile.deal_attitude],
        promo_attitude=deal_hint,
        loyalty_app_habit=_LOYALTY_HABIT[profile.deal_attitude],
        store_relationship=activity,
        jobs_to_be_done=[
            "быстро закрыть еду на ближайшие дни",
            "не переплатить за привычный набор",
        ],
        shopping_routine=f"около {visits} визита в неделю, чек ~{basket} ₽",
        favorite_food_story=f"{foods}",
        quirks=[
            "берёт одни и те же марки, новое пробует неохотно",
            "если очередь длинная — раздражается и торопится",
        ],
        what_makes_them_engage=_ENGAGE_HINT[profile.deal_attitude],
        what_they_ignore="навязчивые предложения и всё, что не входит в привычный набор",
        voice=(
            f"Хожу в магазин под свой ритм, чек рублей на {basket}. "
            f"{_VOICE_HINT[profile.deal_attitude]}"
        ),
    )


def render_persona_block(persona: Persona) -> str:
    quirks = "; ".join(persona.quirks)
    jobs = "; ".join(persona.jobs_to_be_done)
    lines = [
        f"Ты — {persona.full_name}, {persona.age} лет, {persona.occupation}.",
        f"Деньги: {persona.income_band}. {persona.money_mindset}",
        f"Дом и быт: {persona.household}. {persona.city_type}. {persona.neighborhood_context}",
        f"Что сейчас с жизнью: {persona.life_context}",
        f"Зачем тебе вообще магазин: {jobs}",
        f"Как ходишь за продуктами: {persona.shopping_routine}",
        f"Что из продуктов любишь: {persona.favorite_food_story}",
        f"Отношения с этим магазином: {persona.store_relationship}",
        f"Про скидки и акции: {persona.promo_attitude}",
        f"Про карту, баллы и приложение: {persona.loyalty_app_habit}",
        f"Твои привычки и слабости: {quirks}",
        f"Что реально может тебя зацепить: {persona.what_makes_them_engage}",
        f"Мимо чего проходишь не глядя: {persona.what_they_ignore}",
        f"Как ты говоришь и думаешь: {persona.voice}",
    ]
    return "\n".join(lines)
