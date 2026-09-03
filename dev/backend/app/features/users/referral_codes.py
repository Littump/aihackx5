import secrets
import string
from collections.abc import Awaitable, Callable

from app.core.errors import AppError

REFERRAL_CODE_LENGTH = 8
REFERRAL_CODE_ALPHABET = string.ascii_uppercase + string.digits
REFERRAL_CODE_MAX_ATTEMPTS = 50

IsReferralCodeTaken = Callable[[str], Awaitable[bool]]


def random_referral_code() -> str:
    return "".join(secrets.choice(REFERRAL_CODE_ALPHABET) for _ in range(REFERRAL_CODE_LENGTH))


async def generate_unique_referral_code(is_taken: IsReferralCodeTaken) -> str:
    for _ in range(REFERRAL_CODE_MAX_ATTEMPTS):
        candidate = random_referral_code()
        if not await is_taken(candidate):
            return candidate
    raise AppError("referral_code_generation_failed", "не удалось подобрать код приглашения", 500)
