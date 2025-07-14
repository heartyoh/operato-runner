from pydantic import BaseModel, EmailStr, field_serializer
from datetime import datetime, timezone
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
    roles: Optional[List[str]] = []
    is_active: Optional[bool] = True

class UserRead(UserBase):
    id: int
    created_at: datetime
    is_active: bool
    roles: Optional[List[RoleRead]] = []

    @field_serializer('created_at')
    def serialize_dt(self, dt: datetime, _info):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc).isoformat()
        return dt.isoformat()

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
            is_active=getattr(user, "is_active", True),
            roles=roles
        )

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None 