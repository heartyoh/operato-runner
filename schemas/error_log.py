from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ErrorLogRead(BaseModel):
    id: int
    code: str
    message: str
    dev_message: Optional[str]
    url: Optional[str]
    stack: Optional[str]
    user: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True 