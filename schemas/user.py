from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

try:
    from .role import RoleRead
except ImportError:
    RoleRead = None

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    roles: Optional[List[int]] = []

class UserRead(UserBase):
    id: int
    created_at: datetime
    roles: Optional[List[RoleRead]] = []

    class Config:
        orm_mode = True 