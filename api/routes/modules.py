from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from models.module import Module
from module_registry import ModuleRegistry
from models.user import User
from api.auth import has_execute_permission, get_current_user
from core.db import get_db
from models.version import Version
from models.deployment import Deployment

# 필요한 Pydantic 모델은 rest.py에서 import
from pydantic import BaseModel
from datetime import datetime
import os
from datetime import timezone

# --- Pydantic 모델 복사 (간략화) ---
class ModuleResponse(BaseModel):
    name: str
    env: str
    version: str
    created_at: Optional[str] = None
    tags: List[str] = []
    isDeployed: bool
    description: Optional[str] = ""
    visibility: str = "private"
    is_public: bool = False
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None

class ModuleDetailResponse(BaseModel):
    name: str
    env: str
    version: str
    description: str
    tags: List[str]
    visibility: str
    isDeployed: bool
    created_at: Optional[str] = None
    owner: Optional[str] = None
    usage_example: Optional[Dict[str, Any]] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    artifact_type: Optional[str] = None
    artifact_uri: Optional[str] = None

# --- 의존성 주입 함수들 ---
async def get_module_registry(db: AsyncSession = Depends(get_db)):
    return ModuleRegistry(db)

# --- 라우터 정의 ---
router = APIRouter()

@router.get("/modules/executable", response_model=List[ModuleResponse])
async def list_executable_modules(
    search: Optional[str] = None,
    env: Optional[str] = None,
    visibility: Optional[str] = None,
    module_registry: ModuleRegistry = Depends(get_module_registry),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(has_execute_permission())
):
    query = select(Module)
    await db.refresh(current_user, attribute_names=["roles"])
    is_admin = any(role.name == "admin" for role in current_user.roles)
    if not is_admin:
        query = query.where(
            or_(
                Module.visibility == "public",
                Module.owner_id == current_user.id
            )
        )
    if search:
        search_filter = or_(
            Module.name.contains(search),
            Module.description.contains(search),
            Module.tags.contains(search),
            Module.env.contains(search)
        )
        query = query.where(search_filter)
    if env:
        query = query.where(Module.env == env)
    if visibility:
        query = query.where(Module.visibility == visibility)
    query = query.order_by(Module.name)
    result = await db.execute(query)
    modules = result.scalars().all()
    # owner_name 조회
    owner_ids = list(set([m.owner_id for m in modules if m.owner_id]))
    owner_map = {}
    if owner_ids:
        owner_result = await db.execute(select(User).where(User.id.in_(owner_ids)))
        for u in owner_result.scalars().all():
            owner_map[u.id] = u.username
    def is_deployed(m):
        """전개 상태 확인: 실제 전개된 버전이 있는지 확인"""
        if m.env == "inline":
            # inline은 전개가 필요 없지만, active 버전이 있어야 함
            return True
        elif m.env == "uv":
            return os.path.exists(os.path.join("module_envs", m.name, "uv"))
        elif m.env == "venv":
            return os.path.exists(os.path.join("module_envs", m.name, "venv"))
        elif m.env == "conda":
            # conda 환경 경로 수정
            return os.path.exists(os.path.join("module_envs", m.name, "conda"))
        elif m.env == "docker":
            # Docker는 이미지 존재 여부도 확인
            import subprocess
            try:
                # Docker 이미지 확인
                result = subprocess.run(
                    ["docker", "images", "-q", f"mod_{m.name}"],
                    capture_output=True, text=True, timeout=10
                )
                has_image = bool(result.stdout.strip())
                # 전개 디렉토리도 확인
                has_deploy_dir = os.path.exists(os.path.join("module_envs", m.name))
                return has_image and has_deploy_dir
            except Exception:
                # Docker 명령어 실패 시 디렉토리만 확인
                return os.path.exists(os.path.join("module_envs", m.name))
        return False
    return [
        ModuleResponse(
            name=m.name,
            env=m.env,
            version=m.version,
            created_at=m.created_at.isoformat() if m.created_at else None,
            tags=m.tags.split(",") if isinstance(m.tags, str) else (m.tags if m.tags else []),
            isDeployed=is_deployed(m),
            description=m.description or "",
            visibility=m.visibility,
            is_public=m.visibility == "public",
            owner_id=m.owner_id,
            owner_name=owner_map.get(m.owner_id) if m.owner_id else None
        )
        for m in modules
    ]

@router.get("/modules", response_model=List[ModuleResponse])
async def list_modules(
    module_registry: ModuleRegistry = Depends(get_module_registry),
    db: AsyncSession = Depends(get_db)
):
    modules = await module_registry.list_modules()
    def is_deployed(m):
        if m.env == "inline":
            return True
        venv_dir = os.path.join("module_envs", m.name, "venv")
        return os.path.exists(venv_dir)
    result = []
    for m in modules:
        description = m.description
        # 모듈의 description을 사용 (버전의 description이 아님)
        created_at_iso = None
        if m.created_at:
            dt = m.created_at
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            created_at_iso = dt.isoformat()
        result.append({
            "name": m.name,
            "env": m.env,
            "version": m.version,
            "created_at": created_at_iso,
            "tags": m.tags.split(",") if isinstance(m.tags, str) else (m.tags if m.tags else []),
            "isDeployed": is_deployed(m),
            "description": description,
            "visibility": m.visibility or "private",
            "is_public": m.visibility == "public",
        })
    return result

@router.get("/modules/{name}", response_model=ModuleDetailResponse)
async def get_module_detail(
    name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    module_registry: ModuleRegistry = Depends(get_module_registry)
):
    def is_deployed(m):
        if m.env == "inline":
            return True
        venv_dir = os.path.join("module_envs", m.name, "venv")
        return os.path.exists(venv_dir)
    result = await db.execute(select(Module).where(Module.name == name))
    module = result.scalars().first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    # 권한 체크
    await db.refresh(current_user, attribute_names=["roles"])
    is_admin = any(role.name == "admin" for role in current_user.roles)
    if not is_admin:
        if module.visibility != "public" and module.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have permission to access module '{name}'",
            )
    # 소유자 정보 조회
    owner_username = None
    if module.owner_id:
        owner_result = await db.execute(select(User).where(User.id == module.owner_id))
        owner = owner_result.scalars().first()
        if owner:
            owner_username = owner.username
    # 사용법 예시 생성 (기본값)
    usage_example = {
        "input": {"example": "input_data"},
        "description": "모듈 실행을 위한 입력 데이터 예시"
    }
    if module.env == "inline" and module.code:
        try:
            if "def main(" in module.code:
                usage_example["input"] = {"data": "example_value"}
            if "return" in module.code:
                usage_example["output"] = {"result": "example_output"}
        except:
            pass
    return ModuleDetailResponse(
        name=module.name,
        env=module.env,
        version=module.version,
        description=module.description or "",
        tags=module.tags.split(",") if isinstance(module.tags, str) else (module.tags if module.tags else []),
        visibility=module.visibility,
        isDeployed=is_deployed(module),
        created_at=(module.created_at.replace(tzinfo=timezone.utc).isoformat() if module.created_at and module.created_at.tzinfo is None else module.created_at.isoformat()) if module.created_at else None,
        owner=owner_username,
        usage_example=usage_example,
        input_schema={"type": "object", "properties": {"data": {"type": "string"}}},
        output_schema={"type": "object", "properties": {"result": {"type": "string"}}},
        artifact_type=getattr(module, "artifact_type", None),
        artifact_uri=getattr(module, "artifact_uri", None),
    )

# (추가로 /api/modules, /api/modules/{name} 등도 이 파일에 분리 가능) 