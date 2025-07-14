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
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="비활성화된 계정입니다. 관리자에게 문의하세요.",
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
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="비활성화된 계정입니다. 관리자에게 문의하세요.",
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

def has_execute_permission():
    """사용자가 모듈을 실행할 수 있는 권한이 있는지 확인합니다."""
    async def wrapper(
        current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
    ):
        # 로그인한 사용자는 실행 가능 (admin은 모든 권한, 일반 user는 제한적 권한)
        return current_user

    return wrapper

def can_execute_module(module_name: str):
    """사용자가 특정 모듈을 실행할 수 있는지 확인합니다."""
    async def wrapper(
        current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
    ):
        from models.module import Module
        from sqlalchemy import select
        
        # admin은 모든 모듈 실행 가능
        await db.refresh(current_user, attribute_names=["roles"])
        if any(role.name == "admin" for role in current_user.roles):
            return current_user
        
        # 모듈 조회
        result = await db.execute(select(Module).where(Module.name == module_name))
        module = result.scalars().first()
        
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module '{module_name}' not found",
            )
        
        # public 모듈이거나 자신이 소유한 모듈이면 실행 가능
        if module.visibility == "public" or module.owner_id == current_user.id:
            return current_user
            
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have permission to execute module '{module_name}'",
        )

    return wrapper 