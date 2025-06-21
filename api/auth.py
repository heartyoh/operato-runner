from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, ValidationError
from typing import Optional, List, Dict, Any
import os
from datetime import timedelta
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from utils.jwt import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, decode_token
from utils.security import hash_password, verify_password, validate_password_policy
from core.db import SessionLocal as AsyncSessionLocal, get_db
from jose import JWTError, jwt
from passlib.context import CryptContext

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Define both security schemes, auto_error=False allows handling them manually
bearer_scheme = HTTPBearer(bearerFormat="JWT", auto_error=False)
basic_scheme = HTTPBasic(auto_error=False)

# DB 기반 사용자 조회
async def get_user_by_username(username: str, db: AsyncSession):
    result = await db.execute(
        select(User).options(selectinload(User.roles)).where(User.username == username)
    )
    return result.scalars().first()

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    bearer_credentials: Optional[HTTPBearer] = Depends(bearer_scheme),
    basic_credentials: Optional[HTTPBasicCredentials] = Depends(basic_scheme),
):
    if bearer_credentials:
        try:
            token = bearer_credentials.credentials
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials (sub missing)",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except (JWTError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = await get_user_by_username(username, db)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    if basic_credentials:
        user = await get_user_by_username(basic_credentials.username, db)
        if not user or not verify_password(
            basic_credentials.password, user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Basic"},
            )
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer, Basic"},
    )

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user

def has_role(role_name: str):
    async def wrapper(
        current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
    ):
        # Refresh the user object to load the roles relationship
        await db.refresh(current_user, attribute_names=["roles"])
        if not any(role.name == role_name for role in current_user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have the required '{role_name}' role",
            )
        return current_user

    return wrapper

# 회원가입/비밀번호 변경 시 validate_password_policy, hash_password 사용
# 로그인 시 verify_password 사용 