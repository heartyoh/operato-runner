from pydantic import BaseModel
from typing import Optional, List

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleRead(RoleBase):
    id: int
    users: Optional[List[int]] = []

    class Config:
        orm_mode = True 