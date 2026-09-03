from app import game_rules
from app.core.errors import AppError
from app.features.challenges.models import ChallengeDraft


def rank(drafts: list[ChallengeDraft]) -> tuple[ChallengeDraft, list[ChallengeDraft]]:
    if not drafts:
        raise AppError("no_challenge_candidates", "нет кандидатов на челлендж", 500)
    ordered = sorted(drafts, key=lambda draft: draft.priority, reverse=True)
    hero = ordered[0]
    return hero, _pick_side(ordered[1:], hero)


def _pick_side(candidates: list[ChallengeDraft], hero: ChallengeDraft) -> list[ChallengeDraft]:
    chosen: list[ChallengeDraft] = []
    for draft in candidates:
        if _same_slot(draft, hero) or any(_same_slot(draft, s) for s in chosen):
            continue
        chosen.append(draft)
        if len(chosen) >= game_rules.CHALLENGE_SIDE_MAX:
            break
    return chosen


def _same_slot(a: ChallengeDraft, b: ChallengeDraft) -> bool:
    return a.type == b.type and a.category == b.category
