from decimal import Decimal

from psycopg import AsyncConnection

from app.features.challenges import service as challenges_service
from app.features.challenges.models import ChallengeRow, RewardLedgerEntry
from app.features.domovoy import service as domovoy_service
from app.features.receipts import service as receipts_service
from app.features.receipts.models import ReceiptRow
from app.features.rewards import catalog
from app.features.rewards.models import RewardEvent, RewardsSummary
from app.features.users import service as users_service
from app.game_rules import level_for_xp, xp_to_next_level


async def get_rewards(conn: AsyncConnection, user_id: int, *, limit: int) -> RewardsSummary:
    await users_service.get_user(conn, user_id)
    state = await domovoy_service.get_state(conn, user_id)
    entries = await challenges_service.list_ledger_for_user(conn, user_id, limit)
    return RewardsSummary(
        points_balance=await points_balance(conn, user_id),
        xp=state.xp,
        level=level_for_xp(state.xp),
        xp_to_next_level=xp_to_next_level(state.xp),
        rules=catalog.earning_rules(),
        history=await _build_history(conn, entries),
    )


async def points_balance(conn: AsyncConnection, user_id: int) -> int:
    ledger_totals = await challenges_service.sum_ledger_for_user(conn, user_id)
    return ledger_totals.points + await _points_from_receipts(conn, user_id)


async def _points_from_receipts(conn: AsyncConnection, user_id: int) -> int:
    totals = await receipts_service.sum_points(conn, user_id=user_id)
    return totals.earned - totals.spent


async def _build_history(
    conn: AsyncConnection, entries: list[RewardLedgerEntry]
) -> list[RewardEvent]:
    challenges = await challenges_service.list_by_ids(conn, _ref_ids(entries, "challenge"))
    receipts = await receipts_service.list_receipts_by_ids(
        conn, receipt_ids=_ref_ids(entries, "receipt")
    )
    challenge_by_id = {row.id: row for row in challenges}
    receipt_by_id = {row.id: row for row in receipts}
    return [
        RewardEvent(
            id=entry.id,
            kind=entry.kind,
            title=catalog.EVENT_TITLES[entry.kind],
            detail=_detail(entry, challenge_by_id, receipt_by_id),
            xp_delta=entry.xp_delta,
            points_delta=entry.points_delta,
            created_at=entry.created_at,
        )
        for entry in entries
    ]


def _ref_ids(entries: list[RewardLedgerEntry], ref_type: str) -> list[int]:
    return [e.ref_id for e in entries if e.ref_type == ref_type and e.ref_id is not None]


def _detail(
    entry: RewardLedgerEntry,
    challenge_by_id: dict[int, ChallengeRow],
    receipt_by_id: dict[int, ReceiptRow],
) -> str | None:
    if entry.ref_id is None:
        return None
    if entry.ref_type == "challenge":
        challenge = challenge_by_id.get(entry.ref_id)
        return challenge.copy_title if challenge is not None else None
    if entry.ref_type == "receipt":
        receipt = receipt_by_id.get(entry.ref_id)
        return _receipt_detail(receipt) if receipt is not None else None
    return None


def _receipt_detail(receipt: ReceiptRow) -> str:
    return f"Чек на {receipt.paid_total.quantize(Decimal('1'))} ₽"
