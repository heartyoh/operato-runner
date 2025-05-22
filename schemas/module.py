from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ModuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    code: Optional[str] = None
    path: Optional[str] = None
    version: Optional[str] = "0.1.0"
    tags: Optional[List[str]] = []
    owner_id: Optional[int] = None

class ModuleCreate(ModuleBase):
    pass

class ModuleRead(ModuleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        orm_mode = True 