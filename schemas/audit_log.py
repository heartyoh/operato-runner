from pydantic import BaseModel, field_serializer
from typing import Optional
from datetime import datetime, timezone

class AuditLogRead(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    detail: Optional[str]
    created_at: datetime

    @field_serializer('created_at')
    def serialize_dt(self, dt: datetime, _info):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc).isoformat()
        return dt.isoformat()

    model_config = {
        "from_attributes": True
    } 