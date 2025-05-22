from fastapi import FastAPI, HTTPException, Depends, Body, Request
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from module_models import Module, ExecRequest, ExecResult
from module_registry import ModuleRegistry
from executor_manager import ExecutorManager
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db
from models.user import User
from schemas.user import UserCreate, UserRead
from utils.jwt import create_access_token
from api.auth import verify_password, get_current_user, has_role
from utils.security import hash_password, validate_password_policy
import hashlib

app = FastAPI(title="Operato Runner", description="Python module execution platform")

# API 모델
class ModuleCreate(BaseModel):
    name: str
    env: str
    code: Optional[str] = None
    path: Optional[str] = None
    version: Optional[str] = "0.1.0"
    tags: List[str] = []

class ModuleResponse(BaseModel):
    name: str
    env: str
    version: str
    created_at: str
    tags: List[str]

class RunRequest(BaseModel):
    input: Dict[str, Any]

class RunResponse(BaseModel):
    result: Dict[str, Any]
    exit_code: int
    stderr: str
    stdout: str
    duration: float

# DI (app.state에서 가져오도록 수정)
def get_module_registry(request: Request):
    return request.app.state.module_registry

def get_executor_manager(request: Request):
    return request.app.state.executor_manager

# 라우트
@app.get("/modules", response_model=List[ModuleResponse])
async def list_modules(module_registry: ModuleRegistry = Depends(get_module_registry)):
    modules = module_registry.list_modules()
    return [
        ModuleResponse(
            name=m.name,
            env=m.env,
            version=m.version,
            created_at=m.created_at.isoformat(),
            tags=m.tags
        ) for m in modules
    ]

@app.get("/modules/{name}", response_model=ModuleResponse)
async def get_module(name: str, module_registry: ModuleRegistry = Depends(get_module_registry)):
    module = module_registry.get_module(name)
    if not module:
        raise HTTPException(status_code=404, detail=f"Module '{name}' not found")
    return ModuleResponse(
        name=module.name,
        env=module.env,
        version=module.version,
        created_at=module.created_at.isoformat(),
        tags=module.tags
    )

@app.post("/modules", response_model=ModuleResponse, status_code=201)
async def create_module(
    module_data: ModuleCreate,
    module_registry: ModuleRegistry = Depends(get_module_registry)
):
    if not module_data.code and not module_data.path:
        raise HTTPException(status_code=400, detail="Either code or path must be provided")
    module = Module(
        name=module_data.name,
        env=module_data.env,
        code=module_data.code,
        path=module_data.path,
        version=module_data.version,
        tags=module_data.tags
    )
    module_registry.register_module(module)
    return ModuleResponse(
        name=module.name,
        env=module.env,
        version=module.version,
        created_at=module.created_at.isoformat(),
        tags=module.tags
    )

@app.delete("/modules/{name}", status_code=204)
async def delete_module(
    name: str,
    module_registry: ModuleRegistry = Depends(get_module_registry)
):
    if not module_registry.delete_module(name):
        raise HTTPException(status_code=404, detail=f"Module '{name}' not found")
    return None

@app.post("/run/{module}", response_model=RunResponse)
async def run_module(
    module: str,
    request: RunRequest = Body(...),
    executor_manager: ExecutorManager = Depends(get_executor_manager)
):
    exec_request = ExecRequest(
        module=module,
        input_json=request.input
    )
    result = await executor_manager.execute(exec_request)
    return RunResponse(
        result=result.result_json,
        exit_code=result.exit_code,
        stderr=result.stderr,
        stdout=result.stdout,
        duration=result.duration
    )

@app.get("/environments")
async def list_environments(
    executor_manager: ExecutorManager = Depends(get_executor_manager)
):
    return {"environments": executor_manager.get_available_environments()}

# DB 연결 상태 확인 엔드포인트
@app.get("/health/db")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute("SELECT 1")
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.post("/auth/register", response_model=UserRead, status_code=201)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # 이미 존재하는 사용자 체크
    result = await db.execute(
        User.__table__.select().where(User.username == user_in.username)
    )
    existing = result.first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    try:
        validate_password_policy(user_in.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    hashed_pw = hash_password(user_in.password)
    user = User(username=user_in.username, email=user_in.email, hashed_password=hashed_pw)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserRead.from_orm(user)

@app.post("/auth/login")
async def login(form: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        User.__table__.select().where(User.username == form.username)
    )
    user = result.first()
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    user = user[0] if isinstance(user, tuple) else user
    if not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token({"sub": user.username, "scopes": []})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserRead)
async def get_profile(current_user: UserRead = Depends(get_current_user)):
    return current_user

@app.patch("/users/me", response_model=UserRead)
async def update_profile(update: UserCreate, db: AsyncSession = Depends(get_db), current_user: UserRead = Depends(get_current_user)):
    result = await db.execute(
        User.__table__.select().where(User.username == current_user.username)
    )
    user = result.first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = user[0] if isinstance(user, tuple) else user
    if update.password:
        try:
            validate_password_policy(update.password)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        user.hashed_password = hash_password(update.password)
    if update.email:
        user.email = update.email
    await db.commit()
    await db.refresh(user)
    return UserRead.from_orm(user)

@app.get("/admin")
async def admin_only(current_user=Depends(has_role("admin"))):
    return {"message": f"Hello, admin {current_user.username}!"} 