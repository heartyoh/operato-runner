from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VersionBase(BaseModel):
    module_id: int
    version: str
    changelog: Optional[str] = None

class VersionCreate(VersionBase):
    pass

class VersionRead(VersionBase):
    id: int
    created_at: datetime
    class Config:
        orm_mode = True 