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

    model_config = {
        "from_attributes": True
    }

    @classmethod
    def from_orm_safe(cls, user):
        roles = []
        if hasattr(user, "roles") and user.roles is not None:
            try:
                roles = [RoleRead.model_validate(r) for r in list(user.roles)]
            except Exception:
                roles = []
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            roles=roles
        )

class UserLogin(BaseModel):
    username: str
    password: str 