from pydantic import BaseModel, field_serializer
from typing import Optional
from datetime import datetime, timezone

class VersionBase(BaseModel):
    module_id: int
    version: str
    changelog: Optional[str] = None

class VersionCreate(VersionBase):
    pass

class VersionRead(VersionBase):
    id: int
    created_at: datetime
    
    @field_serializer('created_at')
    def serialize_dt(self, dt: datetime, _info):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc).isoformat()
        return dt.isoformat()
    
    class Config:
        orm_mode = True 