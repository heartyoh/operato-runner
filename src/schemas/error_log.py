from pydantic import BaseModel, field_serializer
from typing import Optional
from datetime import datetime, timezone

class ErrorLogRead(BaseModel):
    id: int
    code: str
    message: str
    dev_message: Optional[str]
    url: Optional[str]
    stack: Optional[str]
    user: Optional[str]
    created_at: datetime

    @field_serializer('created_at')
    def serialize_dt(self, dt: datetime, _info):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc).isoformat()
        return dt.isoformat()

    model_config = {
        "from_attributes": True
    } 