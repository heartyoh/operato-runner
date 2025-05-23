from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ModuleHistoryRead(BaseModel):
    id: int
    module_id: int
    version_id: int
    action: str
    operator: Optional[str]
    timestamp: datetime

    class Config:
        orm_mode = True 