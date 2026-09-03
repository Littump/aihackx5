from psycopg import AsyncConnection

from app.features.referrals import database
from app.features.referrals.models import ReferralRow


async def get_referral_by_id(conn: AsyncConnection, referral_id: int) -> ReferralRow | None:
    return await database.get_referral_by_id(conn, referral_id=referral_id)


async def list_by_referrer(conn: AsyncConnection, *, referrer_user_id: int) -> list[ReferralRow]:
    return await database.list_by_referrer(conn, referrer_user_id=referrer_user_id)
