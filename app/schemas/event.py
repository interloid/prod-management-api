from datetime import datetime
from typing import Any

from app.core.constants import EventType
from app.schemas.common import BaseSchema


class EventEnvelope(BaseSchema):
    event: EventType
    request_id: str
    timestamp: datetime
    data: dict[str, Any]
