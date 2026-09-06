from app.ml import marketing
from app.ml import product_knowledge as pk
from app.ml.schemas import ChallengeOffer, GoalDirection, ValidatedPlan

_XP_GROWTH: dict[str, str] = {
    "low": "питомец чуть подрастёт",
    "medium": "питомец заметно подрастёт",
    "high": "питомец здорово подрастёт",
}


def _times(count: int) -> str:
    tail = count % 10
    if tail == 1 and count % 100 != 11:
        return f"{count} раз"
    if tail in (2, 3, 4) and count % 100 not in (12, 13, 14):
        return f"{count} раза"
    return f"{count} раз"


def _condition(offer: ChallengeOffer) -> str:
    cat_acc = pk.category_ru_acc(offer.category)
    examples = pk.category_examples(offer.category)
    if offer.challenge_type == "frequency":
        return f"зайти в магазин {_times(offer.target)} за неделю"
    if offer.challenge_type == "basket":
        return f"собрать корзину крупнее обычного ({_times(offer.target)})"
    if offer.challenge_type == "replenishment":
        return f"пополнить {cat_acc} ({examples})"
    if offer.challenge_type == "collection":
        return f"добавить к покупке {cat_acc} ({examples})"
    return f"взять {cat_acc} ({examples}) — {_times(offer.target)}"


def _reward_line(offer: ChallengeOffer) -> str:
    growth = _XP_GROWTH[offer.reward.xp_level]
    if offer.reward.reward_points > 0:
        return f"{growth}, и до {offer.reward.reward_points} баллов X5 на карту"
    return f"{growth} (баллы за эту цель не начисляются)"


def push_notification(plan: ValidatedPlan) -> str:
    hero = _hero(plan)
    return marketing.public_pitch(hero, plan.goal.direction)


def _hero(plan: ValidatedPlan) -> ChallengeOffer:
    for offer in plan.offers:
        if offer.role == "hero":
            return offer
    return plan.offers[0]


def _sides(plan: ValidatedPlan) -> list[ChallengeOffer]:
    hero = _hero(plan)
    return [offer for offer in plan.offers if offer is not hero]


def render_app_view(plan: ValidatedPlan, level: int) -> str:
    hero = _hero(plan)
    direction: GoalDirection = plan.goal.direction
    tier = pk.reward_tier_for_level(level)
    next_tier = pk.reward_tier_for_level(level + 1)
    lines: list[str] = []
    lines.append("📱 PUSH-УВЕДОМЛЕНИЕ НА ТЕЛЕФОН:")
    lines.append(f"   «{marketing.public_pitch(hero, direction)}»")
    lines.append("")
    lines.append("Нажимаешь на уведомление → попадаешь в берлогу Домового:")
    lines.append("┌──────────────────────────────┐")
    lines.append(f"│  ДОМОВОЙ · уровень {level:<2}        │")
    lines.append("│      ʕ•ᴥ•ʔ  (твой питомец)    │")
    lines.append(f"│  XP: [▓▓▓▓▓░░░░] до ур. {level + 1:<2}   │")
    lines.append("│  копишь XP → питомец растёт   │")
    lines.append("└──────────────────────────────┘")
    lines.append("")
    lines.append("ЦЕЛИ НЕДЕЛИ (обновляются каждый понедельник, живут 7 дней):")
    lines.append("")
    lines.append("  ★ ГЛАВНАЯ ЦЕЛЬ")
    lines.append(f"     {marketing.public_pitch(hero, direction)}")
    lines.append(f"     Что сделать: {_condition(hero)}")
    lines.append("     Срок: до конца недели")
    lines.append(f"     Награда: {_reward_line(hero)}")
    lines.append(f"     Прогресс: 0/{hero.target}")
    sides = _sides(plan)
    if sides:
        lines.append("")
        lines.append(f"  Нажимаешь «Ещё цели» → открываются ещё {len(sides)}:")
        for side in sides:
            lines.append(f"  • {marketing.public_pitch(side, direction)}")
            lines.append(f"     Что сделать: {_condition(side)} · Награда: {_reward_line(side)}")
    lines.append("")
    lines.append(
        "Заходишь в «Лигу домов» → ты и ещё ~25 соседей-Домовых в одном дивизионе; "
        "за верхние места дают бонусные баллы, место растёт с каждой покупкой."
    )
    lines.append("")
    lines.append("КАК УСТРОЕНЫ НАГРАДЫ (правда, зашитая в приложение):")
    lines.append("  XP поднимает уровень Домового. Чем выше уровень — тем крупнее баллы за цель.")
    lines.append(
        f"  Сейчас ур. {level}: до {tier.max_points} баллов за цель; "
        f"поднимешь до ур. {level + 1}: до {next_tier.max_points} баллов."
    )
    return "\n".join(lines)
