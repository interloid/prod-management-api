from datetime import datetime
from typing import Any

from app.schemas.common import BaseSchema


class EventEnvelope(BaseSchema):
    event: str
    request_id: str
    timestamp: datetime
    data: dict[str, Any]
