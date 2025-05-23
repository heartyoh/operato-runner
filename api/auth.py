from fastapi import HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from datetime import timedelta
from sqlalchemy.future import select
from models.user import User
from utils.jwt import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, decode_token
from utils.security import hash_password, verify_password, validate_password_policy
from core.db import SessionLocal as AsyncSessionLocal, get_db

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []

class UserOut(BaseModel):
    id: int
    username: str
    disabled: Optional[bool] = None
    scopes: List[str] = []

# Security
security = HTTPBearer()

# DB 기반 사용자 조회
async def get_user_by_username(username: str, db):
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security), db=Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = decode_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(username=username, scopes=token_scopes)
    except Exception:
        raise credentials_exception
    user = await get_user_by_username(token_data.username, db)
    if user is None:
        raise credentials_exception
    # scopes/disabled 필드는 User 모델에 맞게 확장 필요
    return UserOut(id=user.id, username=user.username, disabled=False, scopes=token_data.scopes)

async def get_current_active_user(current_user: UserOut = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def has_role(required_role: str):
    async def _has_role(current_user: UserOut = Depends(get_current_active_user)):
        user_roles = [r.name if hasattr(r, 'name') else r for r in getattr(current_user, 'roles', [])]
        if required_role not in user_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Not enough permissions. Required role: {required_role}"
            )
        return current_user
    return _has_role

def has_scope(required_scope: str):
    async def _has_scope(current_user: UserOut = Depends(get_current_active_user)):
        if required_scope not in current_user.scopes:
            raise HTTPException(
                status_code=403,
                detail=f"Not enough permissions. Required scope: {required_scope}"
            )
        return current_user
    return _has_scope

# 회원가입/비밀번호 변경 시 validate_password_policy, hash_password 사용
# 로그인 시 verify_password 사용 