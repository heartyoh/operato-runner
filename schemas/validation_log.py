from pydantic import BaseModel, field_serializer
from datetime import datetime, timezone
from typing import Optional

class ModuleValidationLogRead(BaseModel):
    id: int
    filename: str
    status: str
    message: Optional[str] = None
    created_at: datetime

    @field_serializer('created_at')
    def serialize_dt(self, dt: datetime, _info):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc).isoformat()
        return dt.isoformat()

    class Config:
        from_attributes = True 