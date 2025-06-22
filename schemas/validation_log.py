from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ModuleValidationLogRead(BaseModel):
    id: int
    filename: str
    status: str
    message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True 