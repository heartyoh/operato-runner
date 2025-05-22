from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AuditLogRead(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    detail: Optional[str]
    created_at: datetime
    class Config:
        orm_mode = True 