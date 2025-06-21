from pydantic import BaseModel, field_serializer
from typing import Optional
from datetime import datetime, timezone

class ModuleHistoryRead(BaseModel):
    id: int
    module_id: int
    version_id: int
    action: str
    operator: Optional[str]
    timestamp: datetime

    @field_serializer('timestamp')
    def serialize_dt(self, dt: datetime, _info):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc).isoformat()
        return dt.isoformat()

    model_config = {
        "from_attributes": True
    } 