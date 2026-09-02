from typing import Literal

from app.core.models import AppModel


class HealthResponse(AppModel):
    status: Literal["ok"]
    database: Literal["ok", "error"]
