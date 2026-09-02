from typing import Literal

from app.core.models import AppModel


class HealthStatus(AppModel):
    status: Literal["ok"]
    database: Literal["ok", "error"]
