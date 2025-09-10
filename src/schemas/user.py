from pydantic import BaseModel, EmailStr, field_serializer
from datetime import datetime, timezone
from typing import List, Optional

try:
    from schemas.role import RoleRead
except ImportError:
    from typing import Dict, Any
    RoleRead = Dict[str, Any]

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
    roles: Optional[List[RoleRead]] = None

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
        roles = None
        if hasattr(user, "roles") and user.roles is not None:
            try:
                if RoleRead != dict:  # RoleRead가 실제 클래스인 경우만
                    roles = [RoleRead.model_validate(r) for r in list(user.roles)]
                else:
                    roles = [{"name": r.name, "id": r.id} for r in list(user.roles)]
            except Exception:
                roles = None
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