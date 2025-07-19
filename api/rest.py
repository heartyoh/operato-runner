from fastapi import FastAPI, HTTPException, Depends, Body, Request, UploadFile, File, Form, status
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, field_serializer
from models.module import Module
from module_registry import ModuleRegistry
from executor_manager import ExecutorManager
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db, Base, get_engine, init_engine
from models.user import User
from schemas.user import UserCreate, UserRead, UserLogin, UserUpdate
from schemas.role import RoleRead
from utils.jwt import create_access_token, create_refresh_token, decode_token, REFRESH_TOKEN_EXPIRE_MINUTES
from api.auth import verify_password, get_current_user, has_role, has_execute_permission, can_execute_module
from utils.security import hash_password, validate_password_policy
import hashlib
from utils.audit import log_audit_event
from models.audit_log import AuditLog
from schemas.audit_log import AuditLogRead
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from models import ExecRequest, Role
import tempfile
import zipfile
import os
from fastapi.responses import JSONResponse, FileResponse
from models.validation_log import ModuleValidationLog
from models.module_history import ModuleHistory
from models.version import Version
from models.deployment import Deployment
from schemas.module_history import ModuleHistoryRead
from sqlalchemy import update
from utils.exceptions import CustomException
import logging
from models.error_log import ErrorLog
from sqlalchemy import and_, or_
from schemas.error_log import ErrorLogRead
import csv
from fastapi.responses import StreamingResponse
from io import StringIO
import shutil
import subprocess
from sqlalchemy import text
from datetime import datetime, timezone
import pathlib
from schemas.validation_log import ModuleValidationLogRead
from utils.redis_client import redis_client
from models.module import ModuleEnvVar
import humanize
import re
from api.routes import modules

# 프로젝트 루트 경로
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent

def create_app() -> FastAPI:
    app = FastAPI(title="Operato Runner", description="Python module execution platform")

    @app.on_event("startup")
    async def on_startup():
        init_engine()

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
        created_at: Optional[str] = None
        tags: List[str] = []
        isDeployed: bool
        description: Optional[str] = ""
        visibility: str = "private"
        is_public: bool = False  # 호환성을 위해 유지 (deprecated)
        artifact_type: Optional[str] = None
        artifact_uri: Optional[str] = None
        owner_id: Optional[int] = None
        owner_name: Optional[str] = None
        latest_version: Optional[str] = None  # 최신 버전
        active_version: Optional[str] = None  # 활성화된 버전

    class VersionResponse(BaseModel):
        id: int
        version: str
        description: Optional[str] = None
        created_at: datetime
        is_active: bool

        @field_serializer('created_at')
        def serialize_dt(self, dt: datetime, _info):
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc).isoformat()
            return dt.isoformat()

    class HistoryResponse(BaseModel):
        id: int
        module_id: int
        version_id: int
        version: Optional[str] = None
        action: str
        operator: Optional[str] = None
        timestamp: datetime

        @field_serializer('timestamp')
        def serialize_dt(self, dt: datetime, _info):
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc).isoformat()
            return dt.isoformat()

    class RunRequest(BaseModel):
        input: Dict[str, Any]

    class RunResponse(BaseModel):
        result: Any
        exit_code: int
        stderr: str
        stdout: str
        duration: float

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
        usage_example: Optional[str] = None
        input_schema: Optional[Dict[str, Any]] = None
        output_schema: Optional[Dict[str, Any]] = None
        artifact_type: Optional[str] = None
        artifact_uri: Optional[str] = None

    class VersionDetailResponse(BaseModel):
        version: str
        description: Optional[str] = None
        code: Optional[str] = None
        created_at: Optional[str] = None

    # DI: AsyncSession을 받아서 ModuleRegistry 생성
    async def get_module_registry(db: AsyncSession = Depends(get_db)):
        return ModuleRegistry(db)

    def get_executor_manager(request: Request):
        return request.app.state.executor_manager

    # 라우트
    @app.get("/api/templates/module", response_class=FileResponse)
    async def download_module_template():
        template_path = ROOT_DIR / "templates" / "module_template.zip"
        if not template_path.exists():
            raise HTTPException(status_code=404, detail="Template file not found.")
        return FileResponse(
            path=str(template_path),
            media_type="application/zip",
            filename="module_template.zip",
        )

    @app.get("/api/modules", response_model=List[ModuleResponse])
    async def list_modules(
        module_registry: ModuleRegistry = Depends(get_module_registry),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        modules = await module_registry.list_modules()
        
        def is_deployed(m):
            """전개 상태 확인: 실제 전개된 버전이 있는지 확인"""
            if m.env == "inline":
                # inline은 Active 버전이 있을 때만 전개된 것으로 간주
                # 이 함수는 파일시스템 체크용이므로, Active 버전 존재 여부는 별도로 확인
                return True  # 인라인은 전개 개념이 없으므로 항상 True
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
        
        result = []
        for m in modules:
            if m.owner_id != current_user.id:
                continue  # 내가 만든 모듈만 반환
            
            # 실제 전개 상태 확인
            is_actually_deployed = is_deployed(m)
            
            # Active 버전 조회
            # Active 버전은 "현재 전개된 버전" 또는 "다음 전개될 버전"을 의미
            # 전개된 상태가 있다면 해당 버전, 없다면 최신 버전이 active가 됨
            active_version_result = await db.execute(
                select(Version).join(Deployment, Deployment.version_id == Version.id)
                .where(Version.module_id == m.id, Deployment.status == "active")
            )
            active_version = active_version_result.scalars().first()
            
            # 최신 버전 조회
            latest_version_result = await db.execute(
                select(Version).where(Version.module_id == m.id)
                .order_by(Version.created_at.desc())
            )
            latest_version = latest_version_result.scalars().first()
            
            # Active 버전은 항상 "현재 전개된 버전" 또는 "다음 전개될 버전"을 의미
            # 불일치 상태는 존재하지 않음
            
            description = m.description
            if m.env == "inline" and active_version:
                description = active_version.description
            
            # created_at에 timezone 보정
            created_at_iso = None
            if m.created_at:
                dt = m.created_at
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                created_at_iso = dt.isoformat()
            
            # owner_name 조회
            owner_name = None
            if m.owner_id:
                owner_result = await db.execute(select(User).where(User.id == m.owner_id))
                owner = owner_result.scalars().first()
                if owner:
                    owner_name = owner.username
            
            result.append({
                "name": m.name,
                "env": m.env,
                "version": m.version,
                "created_at": created_at_iso,
                "tags": m.tags.split(",") if isinstance(m.tags, str) else (m.tags if m.tags else []),
                "isDeployed": is_actually_deployed,
                "description": description,
                "visibility": m.visibility or "private",
                "is_public": m.visibility == "public",  # 호환성을 위해 유지
                "artifact_type": getattr(m, "artifact_type", None),
                "artifact_uri": getattr(m, "artifact_uri", None),
                "owner_id": m.owner_id,
                "owner_name": owner_name,
                "latest_version": latest_version.version if latest_version else None,
                "active_version": active_version.version if active_version else None,
            })
        return result


    @app.get("/api/modules/{name}/versions", response_model=List[VersionResponse])
    async def get_module_versions(name: str, db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Module).where(Module.name == name))
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")

        versions_result = await db.execute(
            select(Version, Deployment.status)
            .outerjoin(Deployment, and_(Deployment.version_id == Version.id, Deployment.status == "active"))
            .where(Version.module_id == module.id)
            .order_by(Version.created_at.desc())
        )
        
        return [
            VersionResponse(
                id=v.id,
                version=v.version,
                description=v.description,
                created_at=v.created_at,
                is_active=d_status == "active"
            )
            for v, d_status in versions_result.all()
        ]

    @app.get("/api/modules/{name}/history", response_model=List[HistoryResponse])
    async def get_module_history(name: str, db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Module).where(Module.name == name))
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")
        
        # history와 version join
        history_result = await db.execute(
            select(ModuleHistory, Version.version)
            .outerjoin(Version, (ModuleHistory.version_id == Version.id) & (Version.module_id == module.id))
            .where(ModuleHistory.module_id == module.id)
            .order_by(ModuleHistory.timestamp.desc())
        )
        return [
            HistoryResponse(
                id=h.id,
                module_id=h.module_id,
                version_id=h.version_id,
                version=version,
                action=h.action,
                operator=h.operator,
                timestamp=h.timestamp
            )
            for h, version in history_result.all()
        ]

    @app.post("/api/modules", response_model=ModuleResponse, status_code=201)
    async def create_module(
        name: str = Form(...),
        env: str = Form(...),
        version: str = Form("0.1.0"),
        code: str = Form(None),
        description: str = Form(""),
        tags: str = Form(""),
        artifact_type: str = Form(None),
        artifact_uri: str = Form(None),
        file: UploadFile = File(None),
        input: str = Form(""),
        is_public: str = Form("false"),
        auto_deploy: bool = Form(False),  # 자동 전개 여부
        module_registry: ModuleRegistry = Depends(get_module_registry),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        name = name.strip()
        # 모듈명에 슬래시 등 경로 구분자 금지
        import re
        if "/" in name or "\\" in name or ".." in name or not re.match(r"^[a-zA-Z0-9_\-]+$", name):
            raise HTTPException(status_code=400, detail="모듈명에 경로 구분자나 특수문자를 사용할 수 없습니다.")
        # input 파싱
        input_dict = {}
        if input:
            import json
            try:
                input_dict = json.loads(input)
            except Exception:
                raise HTTPException(status_code=400, detail="input 필드는 올바른 JSON이어야 합니다.")
        # 태그 파싱
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
        # is_public 파싱
        is_public_bool = is_public.lower() == 'true'
        # env/배포 방식 유효성 체크
        valid_envs = ["venv", "conda", "uv", "docker", "inline"]
        valid_artifact_types = ["zip", "git", "docker", "inline", None]
        if env not in valid_envs:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 실행 환경입니다: {env}")
        # artifact_type 자동 세팅
        if artifact_uri and not artifact_type:
            artifact_type = "git"
        if file and not artifact_type:
            artifact_type = "zip"
        if artifact_type not in valid_artifact_types:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 artifact_type입니다: {artifact_type}")
        # 논리적 조합 체크
        if env == "git":
            raise HTTPException(status_code=400, detail="env에 'git'은 허용하지 않습니다. 실행 환경만 입력하세요.")
        if artifact_type == "git" and not artifact_uri:
            raise HTTPException(status_code=400, detail="artifact_type이 git이면 artifact_uri가 필요합니다.")
        if artifact_type == "zip" and not file:
            raise HTTPException(status_code=400, detail="artifact_type이 zip이면 파일 업로드가 필요합니다.")
        if artifact_type == "docker" and not artifact_uri:
            raise HTTPException(status_code=400, detail="artifact_type이 docker이면 artifact_uri(도커 이미지 주소)가 필요합니다.")
        # 논리적 조합 체크 (inline은 양방향으로 강제)
        if (artifact_type == "inline") != (env == "inline"):
            raise HTTPException(
                status_code=400,
                detail="artifact_type과 env가 모두 inline이거나 모두 inline이 아니어야 합니다."
            )
        # inline 환경에서 불필요한 업로드/링크 차단 (artifact_type이 inline이거나 없으면 허용)
        if env == "inline" and (artifact_type not in [None, "", "inline"] or artifact_uri or file):
            raise HTTPException(status_code=400, detail="inline 환경은 별도 소스 업로드/링크가 필요 없습니다.")
        if env == "inline" and artifact_type != "inline":
            raise HTTPException(status_code=400, detail="env가 inline이면 artifact_type도 inline이어야 합니다.")
        # 실제 분기
        if artifact_type == "git":
            # git 저장소 등록 처리
            module = Module(
                name=name,
                env=env,
                version=version,
                artifact_type=artifact_type,
                artifact_uri=artifact_uri,
                description=description,
                tags=",".join(tag_list),
                visibility="public" if is_public_bool else "private",
            )
            db.add(module)
            await db.commit()
            await db.refresh(module)
            # [추가] git 저장소를 modules/<name>/<version>/에 clone
            modules_dir = os.path.join("modules", name, version)
            if os.path.exists(modules_dir):
                shutil.rmtree(modules_dir)
            os.makedirs(modules_dir, exist_ok=True)
            import subprocess
            try:
                subprocess.run([
                    "git", "clone", artifact_uri, modules_dir
                ], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                raise HTTPException(status_code=400, detail=f"git clone 실패: {e.stderr}")
            # Version/Deployment 생성 추가
            version_obj = Version(
                module_id=module.id,
                version=version,
                code=None,
                description=description,
                changelog=None,
            )
            db.add(version_obj)
            await db.commit()
            await db.refresh(version_obj)
            deployment_obj = Deployment(module_id=module.id, version_id=version_obj.id, status="active")
            db.add(deployment_obj)
            module.version = version
            await db.commit()
            return ModuleResponse(
                name=module.name,
                env=module.env,
                version=module.version,
                created_at=(module.created_at.replace(tzinfo=timezone.utc).isoformat() if module.created_at and module.created_at.tzinfo is None else module.created_at.isoformat()) if module.created_at else None,
                tags=tag_list,
                isDeployed=False,
                description=description,
                visibility=module.visibility,
                is_public=module.visibility == "public",
                artifact_type=artifact_type,
                artifact_uri=artifact_uri,
                owner_id=module.owner_id,
                owner_name=module.owner_name,
                latest_version=latest_version.version if latest_version else None,
                active_version=active_version.version if active_version else None,
            )
        elif artifact_type == "docker":
            # 도커 이미지 등록 처리
            module = Module(
                name=name,
                env=env,
                version=version,
                artifact_type=artifact_type,
                artifact_uri=artifact_uri,
                description=description,
                tags=",".join(tag_list),
                visibility="public" if is_public_bool else "private",
            )
            db.add(module)
            await db.commit()
            await db.refresh(module)
            return ModuleResponse(
                name=module.name,
                env=module.env,
                version=module.version,
                created_at=(module.created_at.replace(tzinfo=timezone.utc).isoformat() if module.created_at and module.created_at.tzinfo is None else module.created_at.isoformat()) if module.created_at else None,
                tags=tag_list,
                isDeployed=False,
                description=description,
                visibility=module.visibility,
                is_public=module.visibility == "public",
                artifact_type=artifact_type,
                artifact_uri=artifact_uri,
                owner_id=module.owner_id,
                owner_name=module.owner_name,
                latest_version=latest_version.version if latest_version else None,
                active_version=active_version.version if active_version else None,
            )
        elif artifact_type == "zip":
            # zip 파일 업로드 처리 (기존 로직)
            if not file:
                raise HTTPException(status_code=400, detail="파일 기반 모듈의 경우 파일 업로드가 필요합니다.")
            
            # 1. 모듈명 중복 체크
            result = await db.execute(select(Module).where(Module.name == name))
            if result.scalars().first():
                raise HTTPException(status_code=400, detail=f"이미 등록된 모듈명입니다: {name}")
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, file.filename)
                with open(zip_path, "wb") as f:
                    content = await file.read()
                    f.write(content)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                # modules/{name}/{version}/에 압축 해제
                modules_dir = os.path.join("modules", name, version)
                if os.path.exists(modules_dir):
                    shutil.rmtree(modules_dir)
                os.makedirs(modules_dir, exist_ok=True)
                # 압축 해제된 실제 소스 루트 찾기
                items = [item for item in os.listdir(tmpdir) if not item.startswith('.') and item != file.filename]
                if len(items) == 1 and os.path.isdir(os.path.join(tmpdir, items[0])):
                    root_dir = os.path.join(tmpdir, items[0])
                else:
                    root_dir = tmpdir
                # 소스 전체를 modules/{name}/{version}/로 복사
                for item in os.listdir(root_dir):
                    s = os.path.join(root_dir, item)
                    d = os.path.join(modules_dir, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    elif os.path.isfile(s):
                        shutil.copy2(s, d)
                # module_envs/{name}/로 복사하는 로직은 제거
                module = Module(
                    name=name,
                    env=env,
                    code=None,
                    path=None,
                    version=version,
                    tags=','.join(tag_list),
                    description=description,
                    owner_id=current_user.id,
                    is_active=1,  # 등록과 동시에 활성화
                    visibility="public" if is_public_bool else "private",
                    artifact_type="zip",  # ← zip 타입 명시적으로 저장
                    artifact_uri=None,     # ← 필요시 파일명 등 저장 가능
                )
                db.add(module)
                await db.commit()
                await db.refresh(module)
                # 업그레이드처럼 versions 테이블에도 버전 추가
                version_obj = Version(
                    module_id=module.id,
                    version=version,
                    code=None,
                    description=description,
                    changelog=None,
                )
                db.add(version_obj)
                await db.commit()
                await db.refresh(version_obj)
                # 활성화 배포 정보도 추가
                deployment_obj = Deployment(module_id=module.id, version_id=version_obj.id, status="active")
                db.add(deployment_obj)
                # Module.version 필드도 갱신
                module.version = version
                await db.commit()
                return ModuleResponse(
                    name=module.name,
                    env=module.env,
                    version=module.version,
                    created_at=(module.created_at.replace(tzinfo=timezone.utc).isoformat() if module.created_at and module.created_at.tzinfo is None else module.created_at.isoformat()) if module.created_at else None,
                    tags=module.tags.split(",") if module.tags else [],
                    isDeployed=True,
                    description=module.description,
                    visibility=module.visibility or "private",
                    is_public=module.visibility == "public",
                    artifact_type=artifact_type,
                    artifact_uri=artifact_uri,
                    owner_id=module.owner_id,
                    owner_name=module.owner_name,
                    latest_version=latest_version.version if latest_version else None,
                    active_version=active_version.version if active_version else None,
                )
        elif env == "inline":
            # 인라인 코드 등록 처리 (기존 로직)
            module = Module(
                name=name,
                env=env,
                code=code,
                path=None,
                version=version,
                tags=','.join(tag_list),
                description=description,
                owner_id=current_user.id,
                is_active=1,  # 등록과 동시에 활성화
                visibility="public" if is_public_bool else "private",
                artifact_type="inline",  # ← inline 타입 명시적으로 저장
                artifact_uri=None,
            )
            module.input_example = input_dict if hasattr(module, 'input_example') else None
            db.add(module)
            await db.commit()
            await db.refresh(module)
            # 업그레이드처럼 versions 테이블에도 버전 추가
            result = await db.execute(select(Module).where(Module.name == name))
            module = result.scalars().first()
            if not module:
                raise HTTPException(status_code=404, detail=f"Module not found: {name}")
            v_result = await db.execute(
                select(Version).where(Version.module_id == module.id, Version.version == version)
            )
            dup = v_result.scalars().first()
            if dup:
                raise HTTPException(status_code=400, detail=f"이미 등록된 모듈 버전입니다: {name} v{version}")
            version_obj = Version(
                module_id=module.id,
                version=version,
                code=code,
                description=description,
                changelog=None,
            )
            db.add(version_obj)
            await db.commit()
            await db.refresh(version_obj)
            # 기존 Deployment 모두 inactive로
            deployments = await db.execute(select(Deployment).where(Deployment.module_id == module.id))
            for d in deployments.scalars().all():
                d.status = "inactive"
            # 새 버전만 active
            deployment_obj = Deployment(module_id=module.id, version_id=version_obj.id, status="active")
            db.add(deployment_obj)
            # Module.version 필드도 갱신
            module.version = version
            await db.commit()
            await log_audit_event(db, action="module_deploy", detail=f"Module {module.name} deployed", user_id=current_user.id)
            return ModuleResponse(
                name=module.name,
                env=module.env,
                version=module.version,
                created_at=(module.created_at.replace(tzinfo=timezone.utc).isoformat() if module.created_at and module.created_at.tzinfo is None else module.created_at.isoformat()) if module.created_at else None,
                tags=module.tags.split(",") if module.tags else [],
                isDeployed=True,
                description=module.description,
                visibility=module.visibility or "private",
                is_public=module.visibility == "public",
                artifact_type=artifact_type,
                artifact_uri=artifact_uri,
                owner_id=module.owner_id,
                owner_name=module.owner_name,
                latest_version=latest_version.version if latest_version else None,
                active_version=active_version.version if active_version else None,
            )
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 조합입니다.")

    @app.delete("/api/modules/{name}", status_code=204)
    async def delete_module(
        name: str,
        module_registry: ModuleRegistry = Depends(get_module_registry)
    ):
        deleted = await module_registry.delete_module(name)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Module '{name}' not found")
        return None

    @app.post("/api/run/{module}", response_model=RunResponse)
    async def run_module(
        module: str,
        request: RunRequest = Body(...),
        executor_manager: ExecutorManager = Depends(get_executor_manager),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        # 활성화된 버전의 code를 versions에서 읽어옴
        result = await db.execute(select(Module).where(Module.name == module))
        module_obj = result.scalars().first()
        if not module_obj:
            raise HTTPException(status_code=404, detail="Module not found")
            
        # 권한 체크
        await db.refresh(current_user, attribute_names=["roles"])
        is_admin = any(role.name == "admin" for role in current_user.roles)
        
        if not is_admin:
            # 일반 사용자는 public 모듈이나 자신이 소유한 모듈만 실행 가능
            if module_obj.visibility != "public" and module_obj.owner_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User does not have permission to execute module '{module}'",
                )
                
        # 활성화된 버전 조회
        # 모든 환경에서 동일하게 Deployment 테이블의 Active 버전을 조회
        active_version_result = await db.execute(
            select(Version).join(Deployment, Deployment.version_id == Version.id)
            .where(Version.module_id == module_obj.id, Deployment.status == "active")
        )
        
        version_obj = active_version_result.scalars().first()
        if not version_obj:
            raise HTTPException(
                status_code=400,
                detail="활성화된 버전이 없습니다. 배포/버전 상태를 확인하세요."
            )
        # 모든 모듈을 executor_manager를 통해 실행
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

    @app.get("/api/environments")
    async def list_environments(
        executor_manager: ExecutorManager = Depends(get_executor_manager)
    ):
        return {"environments": executor_manager.get_available_environments()}

    # DB 연결 상태 확인 엔드포인트
    @app.get("/api/health/db")
    async def health_check(db: AsyncSession = Depends(get_db)):
        try:
            await db.execute(text("SELECT 1"))
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    # Redis 연결 상태 확인 엔드포인트
    @app.get("/api/health/redis")
    async def redis_health_check():
        try:
            is_connected = await redis_client.is_connected()
            if is_connected:
                return {"status": "ok", "redis": "connected"}
            else:
                return {"status": "error", "redis": "disconnected"}
        except Exception as e:
            return {"status": "error", "redis": "error", "detail": str(e)}

    # 전체 헬스체크 엔드포인트
    @app.get("/api/health")
    async def full_health_check(db: AsyncSession = Depends(get_db)):
        health_status = {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {}
        }
        
        # DB 체크
        try:
            await db.execute(text("SELECT 1"))
            health_status["services"]["database"] = "ok"
        except Exception as e:
            health_status["services"]["database"] = f"error: {str(e)}"
            health_status["status"] = "error"
        
        # Redis 체크
        try:
            is_connected = await redis_client.is_connected()
            health_status["services"]["redis"] = "ok" if is_connected else "disconnected"
            if not is_connected:
                health_status["status"] = "error"
        except Exception as e:
            health_status["services"]["redis"] = f"error: {str(e)}"
            health_status["status"] = "error"
        
        return health_status

    @app.post("/auth/register", response_model=UserRead, status_code=201)
    async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
        print("[register] db session id:", id(db))
        print("[register] db.bind(engine) id:", id(getattr(db, 'bind', None)))
        
        # Check if any user exists
        user_count_result = await db.execute(select(User))
        is_first_user = len(user_count_result.scalars().all()) == 0
        
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
        print("[register] input:", user_in.password, "hash:", hashed_pw)
        
        user = User(username=user_in.username, email=user_in.email, hashed_password=hashed_pw)
        
        if is_first_user:
            # Find or create admin role
            admin_role_result = await db.execute(select(Role).where(Role.name == "admin"))
            admin_role = admin_role_result.scalars().first()
            if not admin_role:
                admin_role = Role(name="admin", description="Administrator")
                db.add(admin_role)
            user.roles.append(admin_role)

        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Eagerly load roles to prevent lazy loading issues in async context
        result = await db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user.id)
        )
        refreshed_user = result.scalar_one()
        
        response = UserRead(
            id=refreshed_user.id,
            username=refreshed_user.username,
            email=refreshed_user.email,
            created_at=refreshed_user.created_at,
            is_active=refreshed_user.is_active,
            roles=[
                RoleRead(id=role.id, name=role.name, description=role.description)
                for role in refreshed_user.roles
            ]
        )
        return response

    @app.post("/auth/login")
    async def login(form: UserLogin, db: AsyncSession = Depends(get_db)):
        # username으로만 유저 조회
        result = await db.execute(
            select(User).options(selectinload(User.roles)).where(User.username == form.username)
        )
        user = result.scalar_one_or_none()
        if not user:
            print("[login] user not found for:", form.username)
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        print("[login] input:", form.password, "db hash:", user.hashed_password)
        print("[login] db hash repr:", repr(user.hashed_password))
        print("[login] == 비교:", user.hashed_password == hash_password(form.password))
        verify = verify_password(form.password, user.hashed_password)
        print("[login] input:", form.password, "db hash:", user.hashed_password, "verify:", verify)
        if not verify:
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="비활성화된 계정입니다. 관리자에게 문의하세요.")

        scopes = [role.name for role in user.roles]
        access_token = create_access_token({"sub": user.username, "scopes": scopes})
        refresh_token = create_refresh_token({"sub": user.username})

        await log_audit_event(db, action="login", detail=f"User {user.username} logged in", user_id=user.id)
        response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=60*60*12  # 12시간
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=60*60*24*30  # 30일
        )
        return response

    @app.post("/auth/refresh")
    async def refresh_token(request: Request, db: AsyncSession = Depends(get_db)):
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            try:
                body = await request.json()
                refresh_token = body.get("refresh_token")
            except Exception:
                refresh_token = None
        if not refresh_token:
            raise HTTPException(status_code=401, detail="No refresh token provided")
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid refresh token type")
            username = payload.get("sub")
            # 유저 존재 여부 확인
            result = await db.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            if not user.is_active:
                raise HTTPException(status_code=403, detail="비활성화된 계정입니다. 관리자에게 문의하세요.")
            scopes = [role.name for role in user.roles]
            access_token = create_access_token({"sub": username, "scopes": scopes})
            new_refresh_token = create_refresh_token({"sub": username})
            response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=60*60*12
            )
            response.set_cookie(
                key="refresh_token",
                value=new_refresh_token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=60*60*24*30
            )
            return response
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

    @app.get("/api/profile", response_model=UserRead)
    async def get_profile(current_user: User = Depends(get_current_user)):
        return current_user

    @app.patch("/api/profile", response_model=UserRead)
    async def update_profile(
        user_in: UserUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        result = await db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == current_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        update_data = user_in.model_dump(exclude_unset=True)
        if "email" in update_data:
            user.email = update_data["email"]
        if "is_active" in update_data:
            user.is_active = update_data["is_active"]
        # roles는 일반 사용자가 직접 수정 불가 (필요시 admin만 허용)
        await db.commit()
        await db.refresh(user)
        await db.refresh(user, attribute_names=['roles'])
        response = UserRead(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            is_active=user.is_active,
            roles=[
                RoleRead(id=role.id, name=role.name, description=role.description)
                for role in user.roles
            ]
        )
        return response

    @app.get("/api/users", response_model=List[UserRead])
    async def list_users(
        username: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[str] = None,
        db: AsyncSession = Depends(get_db), current_user: User = Depends(has_role("admin"))
    ):
        from sqlalchemy.orm import selectinload
        query = select(User).options(selectinload(User.roles))
        if username:
            query = query.where(User.username.contains(username))
        if email:
            query = query.where(User.email.contains(email))
        if role:
            from models.role import Role
            query = query.join(User.roles).where(Role.name == role)
        result = await db.execute(query)
        users = result.scalars().all()
        # Manually construct the response to avoid lazy loading issues
        response_users = []
        for user in users:
            response_users.append(
                UserRead(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    created_at=user.created_at,
                    is_active=user.is_active,
                    roles=[
                        RoleRead(id=role.id, name=role.name, description=role.description)
                        for role in user.roles
                    ]
                )
            )
        return response_users

    @app.post("/api/users", response_model=UserRead, status_code=201)
    async def create_user(
        user_in: UserCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(has_role("admin")),
    ):
        result = await db.execute(select(User).where(User.username == user_in.username))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Username already registered")
        
        try:
            validate_password_policy(user_in.password)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
            
        hashed_pw = hash_password(user_in.password)
        user = User(username=user_in.username, email=user_in.email, hashed_password=hashed_pw)
        
        # Role assignment logic
        if user_in.roles:
            roles_result = await db.execute(
                select(Role).where(Role.name.in_(user_in.roles))
            )
            roles = roles_result.scalars().all()
            for role in roles:
                user.roles.append(role)

        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Eagerly load roles to prevent lazy loading issues in async context
        result = await db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user.id)
        )
        refreshed_user = result.scalar_one()
        
        response = UserRead(
            id=refreshed_user.id,
            username=refreshed_user.username,
            email=refreshed_user.email,
            created_at=refreshed_user.created_at,
            is_active=refreshed_user.is_active,
            roles=[
                RoleRead(id=role.id, name=role.name, description=role.description)
                for role in refreshed_user.roles
            ]
        )
        return response

    @app.patch("/api/users/{user_id}", response_model=UserRead)
    async def update_user(
        user_id: int,
        user_in: UserUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(has_role("admin")),
    ):
        result = await db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        update_data = user_in.model_dump(exclude_unset=True)
        if "email" in update_data:
            user.email = update_data["email"]
        if "is_active" in update_data:
            user.is_active = update_data["is_active"]
        
        if "roles" in update_data and update_data["roles"] is not None:
            role_names = update_data["roles"]
            # 기존 role을 모두 지우고 시작
            user.roles.clear()
            if role_names:
                # DB에서 Role 객체들을 조회
                roles_result = await db.execute(
                    select(Role).where(Role.name.in_(role_names))
                )
                roles = roles_result.scalars().all()
                
                # 조회된 Role 객체들을 user.roles에 추가
                for role in roles:
                    user.roles.append(role)
        
        await db.commit()
        await db.refresh(user)
        
        # Manually construct response to ensure roles are loaded
        await db.refresh(user, attribute_names=['roles'])
        
        response = UserRead(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            is_active=user.is_active,
            roles=[
                RoleRead(id=role.id, name=role.name, description=role.description)
                for role in user.roles
            ]
        )
        return response

    @app.delete("/api/users/{user_id}", status_code=204)
    async def delete_user(
        user_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(has_role("admin")),
    ):
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        await db.delete(user)
        await db.commit()
        return None

    @app.patch("/api/modules/{name}")
    async def update_module_info(
        name: str,
        description: str = Form(None),
        tags: str = Form(None),
        is_public: str = Form(None),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        result = await db.execute(select(Module).where(Module.name == name))
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail="모듈을 찾을 수 없습니다.")

        update_fields = {}
        if description is not None:
            # 인라인 모듈의 경우, 활성화된 버전의 설명을 업데이트
            if module.env == 'inline':
                v_result = await db.execute(
                    select(Version).join(Deployment, Deployment.version_id == Version.id)
                    .where(Version.module_id == module.id, Deployment.status == "active")
                )
                active_version = v_result.scalars().first()
                if active_version:
                    active_version.description = description
            else:
                update_fields['description'] = description
        
        if tags is not None:
            update_fields['tags'] = tags
        if is_public is not None:
            update_fields['visibility'] = 'public' if is_public.lower() == 'true' else 'private'

        if update_fields:
            await db.execute(update(Module).where(Module.name == name).values(**update_fields))

        await db.commit()
        return {"detail": "모듈 정보가 수정되었습니다."}

    @app.get("/api/audit/logs", response_model=List[AuditLogRead])
    async def get_audit_logs(
        action: Optional[str] = None,
        username: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
        db: AsyncSession = Depends(get_db), 
        current_user=Depends(has_role("admin"))
    ):
        from models.user import User
        from sqlalchemy.orm import selectinload, joinedload
        query = select(AuditLog).options(joinedload(AuditLog.user))
        if action:
            query = query.where(AuditLog.action.contains(action))
        if username:
            query = query.join(User, AuditLog.user_id == User.id).where(User.username.contains(username))
        if from_date:
            query = query.where(AuditLog.created_at >= from_date)
        if to_date:
            query = query.where(AuditLog.created_at <= to_date)
        query = query.order_by(AuditLog.created_at.desc()).limit(limit)
        result = await db.execute(query)
        logs = result.unique().scalars().all()
        return [
            {
                "id": log.id,
                "user_id": log.user_id,
                "username": log.user.username if log.user else None,
                "action": log.action,
                "detail": log.detail,
                "created_at": log.created_at,
            }
            for log in logs
        ]

    @app.get("/api/audit/logs/download")
    async def download_audit_logs(
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(has_role("admin"))
    ):
        """감사 로그를 CSV로 다운로드합니다."""
        from models.user import User
        stmt = select(
            AuditLog.id,
            AuditLog.action,
            AuditLog.detail,
            AuditLog.created_at,
            User.username
        ).select_from(
            AuditLog.__table__.outerjoin(User, AuditLog.user_id == User.id)
        )
        # 필터링 조건 추가
        if action:
            stmt = stmt.where(AuditLog.action.contains(action))
        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if from_date:
            stmt = stmt.where(AuditLog.created_at >= from_date)
        if to_date:
            stmt = stmt.where(AuditLog.created_at <= to_date)
        stmt = stmt.order_by(AuditLog.created_at.desc())
        result = await db.execute(stmt)
        rows = result.all()
        # CSV 생성
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Action", "Detail", "Username", "Created At"])
        for row in rows:
            writer.writerow([
                row.id,
                row.action,
                row.detail,
                row.username or "",
                (row.created_at.replace(tzinfo=timezone.utc).isoformat() if row.created_at and row.created_at.tzinfo is None else row.created_at.isoformat()) if row.created_at else ""
            ])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_logs.csv"}
        )

    @app.get("/api/logs/errors", response_model=List[ErrorLogRead])
    async def get_error_logs(
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        query = select(ErrorLog)
        # admin이 아니면 자신의 모듈만
        await db.refresh(current_user, attribute_names=["roles"])
        is_admin = any(role.name == "admin" for role in current_user.roles)
        if not is_admin:
            # ErrorLog.module_name(또는 filename 등)에 내 모듈명만 포함되도록
            module_result = await db.execute(select(Module).where(Module.owner_id == current_user.id))
            my_modules = [m.name for m in module_result.scalars().all()]
            if my_modules:
                from sqlalchemy import or_
                query = query.where(or_(*[ErrorLog.module_name.contains(name) for name in my_modules]))
            else:
                return []
        if from_date:
            query = query.where(ErrorLog.created_at >= from_date)
        if to_date:
            query = query.where(ErrorLog.created_at <= to_date)
        query = query.order_by(ErrorLog.created_at.desc()).limit(limit)
        result = await db.execute(query)
        logs = result.scalars().all()
        return logs

    @app.get("/api/logs/validation", response_model=List[ModuleValidationLogRead])
    async def get_validation_logs(
        module_name: Optional[str] = None,
        status: Optional[str] = None,  # success, fail
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        query = select(ModuleValidationLog)
        # admin이 아니면 자신의 모듈만
        await db.refresh(current_user, attribute_names=["roles"])
        is_admin = any(role.name == "admin" for role in current_user.roles)
        if not is_admin:
            # ModuleValidationLog.filename에서 모듈명을 추출해, 해당 모듈의 owner_id가 본인인 것만
            # 우선 모듈명 리스트 추출
            module_result = await db.execute(select(Module).where(Module.owner_id == current_user.id))
            my_modules = [m.name for m in module_result.scalars().all()]
            if my_modules:
                # filename이 내 모듈명 중 하나를 포함하는 것만
                from sqlalchemy import or_
                query = query.where(or_(*[ModuleValidationLog.filename.contains(name) for name in my_modules]))
            else:
                # 소유 모듈이 없으면 빈 결과
                return []
        if module_name:
            query = query.where(ModuleValidationLog.filename.contains(module_name))
        if status:
            query = query.where(ModuleValidationLog.status == status)
        if from_date:
            query = query.where(ModuleValidationLog.created_at >= from_date)
        if to_date:
            query = query.where(ModuleValidationLog.created_at <= to_date)
        query = query.order_by(ModuleValidationLog.created_at.desc()).limit(limit)
        result = await db.execute(query)
        logs = result.scalars().all()
        return logs

    @app.get("/api/logs/validation/download")
    async def download_validation_logs(
        module_name: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(has_role("admin"))
    ):
        """모듈 검증 로그를 CSV로 다운로드합니다."""
        query = select(ModuleValidationLog)
        
        # 필터링 조건 추가
        if module_name:
            query = query.where(ModuleValidationLog.filename.contains(module_name))
        if status:
            query = query.where(ModuleValidationLog.status == status)
        if from_date:
            query = query.where(ModuleValidationLog.created_at >= from_date)
        if to_date:
            query = query.where(ModuleValidationLog.created_at <= to_date)
        
        query = query.order_by(ModuleValidationLog.created_at.desc())
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # CSV 생성
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Filename", "Version", "Status", "Message", "Created At"])
        import re
        semver_pattern = re.compile(r"[\-_]v?(\d+\.\d+\.\d+)")
        for log in logs:
            # filename에서 semver 추출
            version = ""
            match = semver_pattern.search(log.filename)
            if match:
                version = match.group(1)
            writer.writerow([
                log.id,
                log.filename,
                version,
                log.status,
                log.message or "",
                (log.created_at.replace(tzinfo=timezone.utc).isoformat() if log.created_at and log.created_at.tzinfo is None else log.created_at.isoformat()) if log.created_at else ""
            ])
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=validation_logs.csv"}
        )

    @app.post("/test-init-db")
    async def test_init_db():
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return {"status": "ok"}

    @app.post("/api/modules/{name}/activate")
    async def activate_module_version(
        name: str,
        version: str = Form(...),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """특정 버전을 활성화합니다."""
        # 1. 모듈 존재 확인
        result = await db.execute(select(Module).where(Module.name == name))
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail=f"Module '{name}' not found")
        
        # 2. 버전 존재 확인
        version_result = await db.execute(
            select(Version).where(Version.module_id == module.id, Version.version == version)
        )
        version_obj = version_result.scalars().first()
        if not version_obj:
            raise HTTPException(status_code=404, detail=f"Version '{version}' not found for module '{name}'")
        
        # 3. 기존 활성 배포를 비활성화
        deployments = await db.execute(select(Deployment).where(Deployment.module_id == module.id))
        for d in deployments.scalars().all():
            d.status = "inactive"
        
        # 4. 새 버전을 활성화
        deployment_obj = Deployment(module_id=module.id, version_id=version_obj.id, status="active")
        db.add(deployment_obj)
        
        # 5. Module.version 필드도 갱신
        module.version = version
        await db.commit()
        
        # 6. 히스토리 기록
        history = ModuleHistory(
            module_id=module.id,
            version_id=version_obj.id,
            action="activate",
            operator=current_user.username,
        )
        db.add(history)
        await db.commit()
        
        return {"detail": f"모듈 '{name}' 버전 '{version}'이 활성화되었습니다."}

    @app.post("/api/modules/{name}/deactivate")
    async def deactivate_module_version(
        name: str,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """모든 버전을 비활성화합니다."""
        # 1. 모듈 존재 확인
        result = await db.execute(select(Module).where(Module.name == name))
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail=f"Module '{name}' not found")
        
        # 2. 모든 활성 배포를 비활성화
        deployments = await db.execute(select(Deployment).where(Deployment.module_id == module.id))
        deactivated_count = 0
        for d in deployments.scalars().all():
            if d.status == "active":
                d.status = "inactive"
                deactivated_count += 1
        
        await db.commit()
        
        # 3. 히스토리 기록
        if deactivated_count > 0:
            # 현재 활성 버전의 ID를 가져와서 히스토리에 기록
            current_deployment_result = await db.execute(
                select(Deployment).where(Deployment.module_id == module.id, Deployment.status == "inactive")
            )
            current_deployment = current_deployment_result.scalars().first()
            version_id = current_deployment.version_id if current_deployment else None
            
            if version_id:
                history = ModuleHistory(
                    module_id=module.id,
                    version_id=version_id,
                    action="deactivate",
                    operator=current_user.username,
                )
                db.add(history)
                await db.commit()
        
        return {"detail": f"모듈 '{name}'의 모든 버전이 비활성화되었습니다."}

    @app.post("/api/modules/{name}/rollback")
    async def rollback_module_version(
        name: str,
        target_version: str = Form(...),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """특정 버전으로 롤백합니다."""
        # 1. 모듈 존재 확인
        result = await db.execute(select(Module).where(Module.name == name))
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail=f"Module '{name}' not found")
        
        # 2. 롤백 대상 버전 존재 확인
        target_version_result = await db.execute(
            select(Version).where(Version.module_id == module.id, Version.version == target_version)
        )
        target_version_obj = target_version_result.scalars().first()
        if not target_version_obj:
            raise HTTPException(status_code=404, detail=f"Target version '{target_version}' not found for module '{name}'")
        
        # 3. 현재 활성 버전 확인
        current_deployment_result = await db.execute(
            select(Deployment).where(Deployment.module_id == module.id, Deployment.status == "active")
        )
        current_deployment = current_deployment_result.scalars().first()
        current_version = "unknown"
        if current_deployment:
            current_version_result = await db.execute(
                select(Version).where(Version.id == current_deployment.version_id)
            )
            current_version_obj = current_version_result.scalars().first()
            if current_version_obj:
                current_version = current_version_obj.version
        
        # 4. 기존 활성 배포를 비활성화
        deployments = await db.execute(select(Deployment).where(Deployment.module_id == module.id))
        for d in deployments.scalars().all():
            d.status = "inactive"
        
        # 5. 롤백 대상 버전을 활성화
        deployment_obj = Deployment(module_id=module.id, version_id=target_version_obj.id, status="active")
        db.add(deployment_obj)
        
        # 6. Module.version 필드도 갱신
        module.version = target_version
        await db.commit()
        
        # 7. 히스토리 기록
        history = ModuleHistory(
            module_id=module.id,
            version_id=target_version_obj.id,
            action="rollback",
            operator=current_user.username,
        )
        db.add(history)
        await db.commit()
        
        return {"detail": f"모듈 '{name}'이 버전 '{target_version}'으로 롤백되었습니다."}

    @app.post("/api/modules/{name}/versions")
    async def upload_module_version(
        name: str, 
        file: UploadFile = File(None), 
        version: str = Form(...),
        description: str = Form(""),
        code: str = Form(None),  # inline 모듈용 코드
        auto_deploy: bool = Form(False),  # 자동 전개 여부
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """모듈 이름으로 새 버전을 업로드합니다."""
        # 1. 모듈 존재 확인
        result = await db.execute(select(Module).where(Module.name == name))
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail=f"Module '{name}' not found")
        
        # 2. 이전 버전의 전개 상태 확인
        current_deployment = await db.execute(
            select(Deployment).where(Deployment.module_id == module.id, Deployment.status == "active")
        )
        is_currently_deployed = current_deployment.scalars().first() is not None
        
        # 3. 중복 버전 체크
        version_result = await db.execute(
            select(Version).where(Version.module_id == module.id, Version.version == version)
        )
        if version_result.scalars().first():
            raise HTTPException(status_code=400, detail=f"이미 존재하는 버전입니다: {name} v{version}")
        
        # 4. inline 모듈 처리
        if module.env == "inline":
            if not code:
                raise HTTPException(status_code=400, detail="inline 모듈의 경우 코드가 필요합니다.")
            # 실제 inline 버전 업로드 처리
            version_obj = Version(
                module_id=module.id,
                version=version,
                code=code,
                description=description,
                changelog=None,
            )
            db.add(version_obj)
            await db.commit()
            await db.refresh(version_obj)
            # 버전 업로드만 수행, 활성화는 별도 단계
            return {
                "detail": f"inline 모듈 버전 업로드 성공: {name} v{version}",
                "version": version,
                "description": description,
                "auto_deployed": False,  # 인라인 모듈도 자동 활성화하지 않음
                "was_deployed": is_currently_deployed
            }
        elif getattr(module, "artifact_type", None) == "git":
            # 실제 git 타입 업그레이드 처리
            import tempfile, os, shutil, subprocess
            repo_url = module.artifact_uri
            if not repo_url:
                raise HTTPException(status_code=400, detail="git 저장소 URL이 없습니다.")
            with tempfile.TemporaryDirectory() as tmpdir:
                try:
                    subprocess.run(["git", "clone", "--depth", "1", repo_url, tmpdir], check=True)
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"git clone 실패: {e}")
                # 필수 파일 체크
                main_path = os.path.join(tmpdir, "__main__.py")
                requirements_path = os.path.join(tmpdir, "requirements.txt")
                if not os.path.exists(main_path):
                    raise HTTPException(status_code=400, detail="__main__.py 파일이 없습니다.")
                if not os.path.exists(requirements_path):
                    raise HTTPException(status_code=400, detail="requirements.txt 파일이 없습니다.")
                # modules/{name}/{version}에 복사
                modules_dir = os.path.join("modules", name, version)
                if os.path.exists(modules_dir):
                    shutil.rmtree(modules_dir)
                os.makedirs(modules_dir, exist_ok=True)
                for item in os.listdir(tmpdir):
                    s = os.path.join(tmpdir, item)
                    d = os.path.join(modules_dir, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    elif os.path.isfile(s):
                        shutil.copy2(s, d)
                # Version 테이블에 새 버전 추가
                version_obj = Version(
                    module_id=module.id,
                    version=version,
                    code=None,
                    description=description,
                    changelog=None,
                )
                db.add(version_obj)
                await db.commit()
                await db.refresh(version_obj)
                # 버전 업로드만 수행, 활성화는 별도 단계
                return {
                    "detail": f"git 모듈 버전 업로드 성공: {name} v{version}",
                    "version": version,
                    "description": description,
                    "auto_deployed": False,  # 자동 활성화하지 않음
                    "was_deployed": is_currently_deployed
                }
        else:
            # zip 업로드(파일 기반) 처리 (artifact_type/env 등 기존 모듈 정보 사용)
            import tempfile, os, shutil, zipfile
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, file.filename)
                with open(zip_path, "wb") as f:
                    content = await file.read()
                    f.write(content)
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(tmpdir)
                except zipfile.BadZipFile:
                    raise HTTPException(status_code=400, detail="업로드 파일이 올바른 zip 압축파일이 아닙니다.")
                # 필수 파일 검사
                required_files = ["__main__.py", "requirements.txt"]
                found = {f: False for f in required_files}
                main_path = None
                requirements_path = None
                for root, dirs, files in os.walk(tmpdir):
                    for fname in files:
                        for req in required_files:
                            if fname.lower() == req.lower():
                                found[req] = True
                        if fname.lower() == "__main__.py":
                            main_path = os.path.join(root, fname)
                        if fname.lower() == "requirements.txt":
                            requirements_path = os.path.join(root, fname)
                missing = [f for f, ok in found.items() if not ok]
                if missing:
                    raise HTTPException(status_code=400, detail=f"필수 파일 누락: {', '.join(missing)}")
                # __main__.py 내부에 main 함수 존재 여부 검사
                if main_path:
                    with open(main_path, "r", encoding="utf-8") as f:
                        main_code = f.read()
                    if "def main(" not in main_code:
                        raise HTTPException(status_code=400, detail="__main__.py에 'def main' 함수가 정의되어 있지 않습니다.")
                # modules/{name}/{version}에 복사
                modules_dir = os.path.join("modules", name, version)
                if os.path.exists(modules_dir):
                    shutil.rmtree(modules_dir)
                os.makedirs(modules_dir, exist_ok=True)
                items = [item for item in os.listdir(tmpdir) if not item.startswith('.') and item != file.filename]
                if len(items) == 1 and os.path.isdir(os.path.join(tmpdir, items[0])):
                    root_dir = os.path.join(tmpdir, items[0])
                else:
                    root_dir = tmpdir
                for item in os.listdir(root_dir):
                    s = os.path.join(root_dir, item)
                    d = os.path.join(modules_dir, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    elif os.path.isfile(s):
                        shutil.copy2(s, d)
                # Version 테이블에 새 버전 추가 (artifact_type/env 등 기존 모듈 정보 사용)
                version_obj = Version(
                    module_id=module.id,
                    version=version,
                    code=None,
                    description=description,
                    changelog=None,
                )
                db.add(version_obj)
                await db.commit()
                await db.refresh(version_obj)
                # 버전 업로드만 수행, 활성화는 별도 단계
                # 성공 로그 기록
                log = ModuleValidationLog(filename=file.filename, status="success", message=f"버전 업로드 성공: {name} v{version}")
                db.add(log)
                await db.commit()
                return {
                    "detail": f"모듈 버전 업로드 성공: {name} v{version}",
                    "version": version,
                    "description": description,
                    "auto_deployed": False,  # 자동 활성화하지 않음
                    "was_deployed": is_currently_deployed
                }

    @app.post("/api/modules/{name}/deploy")
    async def deploy_module(name: str, db: AsyncSession = Depends(get_db)):
        """미전개 상태의 모듈을 배포(가상환경 생성 및 의존성 설치)합니다."""
        result = await db.execute(select(Module).where(Module.name == name))
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail=f"Module {name} not found")
        
        def is_deployed(m):
            """전개 상태 확인: 실제 전개된 버전이 있는지 확인"""
            if m.env == "inline":
                return True  # 인라인은 전개 개념이 없으므로 항상 True
            elif m.env == "uv":
                return os.path.exists(os.path.join("module_envs", m.name, "uv"))
            elif m.env == "venv":
                return os.path.exists(os.path.join("module_envs", m.name, "venv"))
            elif m.env == "conda":
                return os.path.exists(os.path.join("module_envs", m.name, "conda"))
            elif m.env == "docker":
                import subprocess
                try:
                    result = subprocess.run(
                        ["docker", "images", "-q", f"mod_{m.name}"],
                        capture_output=True, text=True, timeout=10
                    )
                    has_image = bool(result.stdout.strip())
                    has_deploy_dir = os.path.exists(os.path.join("module_envs", m.name))
                    return has_image and has_deploy_dir
                except Exception:
                    return os.path.exists(os.path.join("module_envs", m.name))
            return False

        # Active 버전 확인
        active_version_result = await db.execute(
            select(Version).join(Deployment, Deployment.version_id == Version.id)
            .where(Version.module_id == module.id, Deployment.status == "active")
        )
        active_version = active_version_result.scalars().first()
        
        # Active 버전이 없으면 최신 버전을 active로 설정
        if not active_version:
            latest_version_result = await db.execute(
                select(Version).where(Version.module_id == module.id).order_by(Version.created_at.desc())
            )
            latest_version = latest_version_result.scalars().first()
            if not latest_version:
                raise HTTPException(status_code=404, detail=f"No versions found for module {name}")
            
            # 기존 active 배포를 모두 비활성화
            deployments = await db.execute(select(Deployment).where(Deployment.module_id == module.id))
            for d in deployments.scalars().all():
                d.status = "inactive"
            
            # 최신 버전을 active로 설정
            deployment_obj = Deployment(module_id=module.id, version_id=latest_version.id, status="active")
            db.add(deployment_obj)
            module.version = latest_version.version
            await db.commit()
            
            active_version = latest_version
        else:
            # Active 버전이 있으면 해당 버전 사용
            active_version = active_version

        env_type = module.env.lower() if module.env else "venv"
        src_dir = os.path.join("modules", module.name, active_version.version)
        dst_dir = os.path.join("module_envs", module.name)

        if not os.path.exists(src_dir):
            raise HTTPException(status_code=400, detail="영구 저장소에 모듈 파일이 존재하지 않습니다.")

        os.makedirs(dst_dir, exist_ok=True)

        try:
            if env_type == "venv":
                req_dir = _find_requirements_dir(src_dir)
                _prepare_env_dir(dst_dir, "venv")
                _copy_src_to_env_dir(req_dir, dst_dir)
                
                venv_dir = os.path.join(dst_dir, "venv")
                # 기존 환경이 있으면 삭제하고 새로 생성
                if os.path.exists(venv_dir):
                    shutil.rmtree(venv_dir)
                subprocess.run(["python3", "-m", "venv", venv_dir], check=True, capture_output=True, text=True)

                venv_python = os.path.join(venv_dir, "bin", "python")
                requirements_path = os.path.join(dst_dir, "requirements.txt")
                if os.path.exists(requirements_path):
                    subprocess.run(
                        [venv_python, "-m", "pip", "install", "--upgrade", "pip"],
                        check=True, capture_output=True, text=True
                    )
                    subprocess.run(
                        [venv_python, "-m", "pip", "install", "-r", requirements_path],
                        check=True, capture_output=True, text=True
                    )

            elif env_type == "uv":
                req_dir = _find_requirements_dir(src_dir)
                _prepare_env_dir(dst_dir, "uv")
                _copy_src_to_env_dir(req_dir, dst_dir)
                
                uv_dir = os.path.join(dst_dir, "uv")
                # 기존 환경이 있으면 삭제하고 새로 생성
                if os.path.exists(uv_dir):
                    shutil.rmtree(uv_dir)
                subprocess.run(["uv", "venv", uv_dir, "--python", "3.9"], check=True, capture_output=True, text=True)

                requirements_path = "requirements.txt"  # <-- 파일명만 넘김
                if os.path.exists(os.path.join(dst_dir, requirements_path)):
                    subprocess.run(["uv", "pip", "install", "-r", requirements_path], check=True, cwd=dst_dir, capture_output=True, text=True)
            
            elif env_type == "conda":
                req_dir = _find_requirements_dir(src_dir)
                _prepare_env_dir(dst_dir, "conda")
                _copy_src_to_env_dir(req_dir, dst_dir)
                
                conda_dir = os.path.join(dst_dir, "conda")
                # 기존 환경이 있으면 삭제하고 새로 생성
                if os.path.exists(conda_dir):
                    subprocess.run(["conda", "remove", "-y", "-p", conda_dir, "--all"], check=False, capture_output=True, text=True)
                    shutil.rmtree(conda_dir)
                subprocess.run(["conda", "create", "-p", conda_dir, "python=3.9", "-y"], check=True, capture_output=True, text=True)

                conda_python = os.path.join(conda_dir, "bin", "python")
                requirements_path = os.path.join(dst_dir, "requirements.txt")
                if os.path.exists(requirements_path):
                    subprocess.run(
                        [conda_python, "-m", "pip", "install", "--upgrade", "pip"],
                        check=True, capture_output=True, text=True
                    )
                    subprocess.run(
                        [conda_python, "-m", "pip", "install", "-r", requirements_path],
                        check=True, capture_output=True, text=True
                    )
            
            elif env_type == "docker":
                docker_tag = f"mod_{module.name}:{active_version.version}"
                dockerfile_path = os.path.join(src_dir, "Dockerfile")
                if not os.path.exists(dockerfile_path):
                    raise HTTPException(status_code=400, detail="Dockerfile이 존재하지 않습니다.")
                
                # 기존 이미지가 있으면 삭제
                try:
                    subprocess.run(["docker", "rmi", docker_tag], check=False, capture_output=True, text=True)
                except Exception:
                    pass
                
                proc = subprocess.run(
                    ["docker", "build", "-t", docker_tag, src_dir],
                    capture_output=True, text=True, check=False
                )
                if proc.returncode != 0:
                    raise subprocess.CalledProcessError(proc.returncode, proc.args, stderr=proc.stderr)
            
            else:
                raise HTTPException(status_code=400, detail=f"지원하지 않는 환경 타입입니다: {env_type}")
            
            log_module_action(module.name, active_version.version, "deploy", f"{env_type} 환경 배포 성공")
            log = ModuleValidationLog(filename=module.name, status="success", message=f"{env_type} 환경 배포 성공")
            db.add(log)
            await db.commit()

        except subprocess.CalledProcessError as e:
            error_message = f"{env_type} 환경 배포 실패: {e.stderr}"
            log_module_action(module.name, active_version.version, "deploy", error_message)
            log = ModuleValidationLog(filename=module.name, status="fail", message=error_message)
            db.add(log)
            await db.commit()
            raise HTTPException(status_code=500, detail=error_message)
        except Exception as e:
            error_message = f"배포 중 알 수 없는 예외 발생: {str(e)}"
            log_module_action(module.name, active_version.version, "deploy", error_message)
            log = ModuleValidationLog(filename=module.name, status="fail", message=error_message)
            db.add(log)
            await db.commit()
            raise HTTPException(status_code=500, detail=error_message)

        # 전개 완료 후 상태 확인
        is_deployed_after = is_deployed(module)
        log_module_action(module.name, active_version.version, "deploy", f"{env_type} 환경 배포 완료. 전개 상태: {is_deployed_after}")
        
        return {"detail": f"{env_type} 환경에서 모듈 배포가 완료되었습니다. (버전: {active_version.version}, 전개 상태: {is_deployed_after})"}

    @app.delete("/api/modules/{name}/deploy")
    async def undeploy_module(name: str):
        module_env_dir = os.path.abspath(os.path.join("module_envs", name))
        venv_dir = os.path.join(module_env_dir, "venv")
        conda_env_dir = os.path.join(module_env_dir, "conda")
        uv_dir = os.path.join(module_env_dir, "uv")
        
        # venv 환경 삭제
        if os.path.exists(venv_dir):
            try:
                shutil.rmtree(venv_dir)
            except Exception:
                pass
        # conda 환경 삭제
        if os.path.exists(conda_env_dir):
            import subprocess
            try:
                subprocess.run(["conda", "remove", "-y", "-p", conda_env_dir, "--all"], check=False)
            except Exception:
                pass
            try:
                if os.path.exists(conda_env_dir):
                    shutil.rmtree(conda_env_dir)
            except Exception:
                pass
        # uv 환경 삭제
        if os.path.exists(uv_dir):
            try:
                shutil.rmtree(uv_dir)
            except Exception:
                pass
        # docker 환경 삭제
        if os.path.exists(module_env_dir):
            try:
                shutil.rmtree(module_env_dir)
            except Exception:
                pass
        return {"success": True, "log": "전개 환경이 제거되었습니다."}

    # 환경변수 관리 API
    @app.get("/api/modules/{name}/env-vars")
    async def get_module_env_vars(
        name: str,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """모듈의 환경변수 목록을 조회합니다."""
        result = await db.execute(select(Module).where(Module.name == name))
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")
        
        env_vars_result = await db.execute(
            select(ModuleEnvVar).where(ModuleEnvVar.module_id == module.id)
        )
        return [
            {"key": ev.key, "value": ev.value}
            for ev in env_vars_result.scalars().all()
        ]

    @app.post("/api/modules/{name}/env-vars")
    async def add_module_env_var(
        name: str,
        key: str = Form(...),
        value: str = Form(...),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """모듈에 환경변수를 추가합니다."""
        result = await db.execute(select(Module).where(Module.name == name))
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")
        
        # 중복 키 체크
        existing_result = await db.execute(
            select(ModuleEnvVar).where(
                ModuleEnvVar.module_id == module.id,
                ModuleEnvVar.key == key
            )
        )
        if existing_result.scalars().first():
            raise HTTPException(status_code=400, detail=f"이미 존재하는 환경변수 키입니다: {key}")
        
        env_var = ModuleEnvVar(
            module_id=module.id,
            key=key,
            value=value
        )
        db.add(env_var)
        await db.commit()
        
        return {"key": key, "value": value}

    @app.put("/api/modules/{name}/env-vars/{key}")
    async def update_module_env_var(
        name: str,
        key: str,
        value: str = Form(...),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """모듈의 환경변수를 수정합니다."""
        result = await db.execute(select(Module).where(Module.name == name))
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")
        
        env_var_result = await db.execute(
            select(ModuleEnvVar).where(
                ModuleEnvVar.module_id == module.id,
                ModuleEnvVar.key == key
            )
        )
        env_var = env_var_result.scalars().first()
        if not env_var:
            raise HTTPException(status_code=404, detail=f"환경변수를 찾을 수 없습니다: {key}")
        
        env_var.value = value
        await db.commit()
        
        return {"key": key, "value": value}

    @app.delete("/api/modules/{name}/env-vars/{key}")
    async def delete_module_env_var(
        name: str,
        key: str,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        """모듈의 환경변수를 삭제합니다."""
        result = await db.execute(select(Module).where(Module.name == name))
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")
        
        env_var_result = await db.execute(
            select(ModuleEnvVar).where(
                ModuleEnvVar.module_id == module.id,
                ModuleEnvVar.key == key
            )
        )
        env_var = env_var_result.scalars().first()
        if not env_var:
            raise HTTPException(status_code=404, detail=f"환경변수를 찾을 수 없습니다: {key}")
        
        await db.delete(env_var)
        await db.commit()
        
        return {"message": f"환경변수가 삭제되었습니다: {key}"}

    @app.exception_handler(CustomException)
    async def custom_exception_handler(request: Request, exc: CustomException):
        logger.error(f"[{exc.code}] {exc.dev_message} | {request.url}")
        # 에러 로그 DB 기록
        db: AsyncSession = request.state.db if hasattr(request.state, 'db') else None
        user = None
        try:
            # FastAPI Depends로 current_user를 바로 얻기 어렵기 때문에, 토큰에서 추출하거나 None 처리
            if hasattr(request, 'user') and getattr(request, 'user', None):
                user = getattr(request, 'user').username
        except Exception:
            user = None
        # stack trace는 exc.__traceback__에서 추출 가능
        import traceback
        stack = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        # DB 기록 (비동기)
        if db:
            log = ErrorLog(
                code=exc.code,
                message=exc.message,
                dev_message=exc.dev_message,
                url=str(request.url),
                stack=stack,
                user=user
            )
            db.add(log)
            await db.commit()
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict()
        )

    @app.get("/api/modules/{name}/deployed-info")
    async def get_deployed_info(name: str, db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Module).where(Module.name == name))
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")
        if module.env == "inline":
            return {"message": "이 모듈은 인라인 실행 방식이므로 별도의 배포/전개 정보가 없습니다."}
        
        # 활성화된 버전 찾기
        active_version_result = await db.execute(
            select(Version).join(Deployment, Deployment.version_id == Version.id)
            .where(Version.module_id == module.id, Deployment.status == "active")
        )
        active_version = active_version_result.scalars().first()
        
        # 배포 경로 (modules) - 원본 업로드 파일들
        deploy_base_dir = None
        deploy_exists = False
        if active_version:
            deploy_base_dir = os.path.join("modules", module.name, active_version.version)
            deploy_exists = os.path.exists(deploy_base_dir)
        else:
            # 활성화된 버전이 없으면 최신 버전 찾기
            latest_version_result = await db.execute(
                select(Version).where(Version.module_id == module.id)
                .order_by(Version.created_at.desc())
            )
            latest_version = latest_version_result.scalars().first()
            if latest_version:
                deploy_base_dir = os.path.join("modules", module.name, latest_version.version)
                deploy_exists = os.path.exists(deploy_base_dir)
        
        # 전개 경로 (module_envs) - 실제 실행 환경
        env_base_dir = os.path.join("module_envs", module.name)
        env_exists = os.path.exists(env_base_dir)
        
        if not deploy_exists and not env_exists:
            return {"message": f"배포 경로와 전개 경로 모두 존재하지 않습니다."}
        
        # 배포된 파일 목록 수집
        deploy_files = []
        deploy_total_size = 0
        if deploy_exists and deploy_base_dir:
            for root, dirs, files in os.walk(deploy_base_dir):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        stat = os.stat(fp)
                        deploy_files.append({
                            "path": os.path.relpath(fp, deploy_base_dir),
                            "size": humanize.naturalsize(stat.st_size),
                            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                        })
                        deploy_total_size += stat.st_size
                    except Exception:
                        continue
        
        # 전개된 환경 파일 목록 수집
        env_files = []
        env_total_size = 0
        if env_exists:
            for root, dirs, files in os.walk(env_base_dir):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        stat = os.stat(fp)
                        env_files.append({
                            "path": os.path.relpath(fp, env_base_dir),
                            "size": humanize.naturalsize(stat.st_size),
                            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                        })
                        env_total_size += stat.st_size
                    except Exception:
                        continue
        
        # 환경별 하위 디렉토리 확인
        env_subdir = None
        if module.env == "venv":
            env_subdir = os.path.join(env_base_dir, "venv")
        elif module.env == "conda":
            env_subdir = os.path.join(env_base_dir, "conda")
        elif module.env == "uv":
            env_subdir = os.path.join(env_base_dir, "uv")
        
        # 실제 설치된 dependencies 정보 수집
        dependencies = []
        if module.env in ["venv", "conda", "uv"] and env_subdir and os.path.exists(env_subdir):
            try:
                # 환경별 python 경로 찾기
                if module.env == "venv":
                    python_path = os.path.join(env_subdir, "bin", "python")
                elif module.env == "conda":
                    python_path = os.path.join(env_subdir, "bin", "python")
                elif module.env == "uv":
                    python_path = os.path.join(env_subdir, "bin", "python")
                
                if os.path.exists(python_path):
                    # pip list 명령 실행
                    result = subprocess.run(
                        [python_path, "-m", "pip", "list", "--format=freeze"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode == 0:
                        for line in result.stdout.strip().split('\n'):
                            if line and '==' in line:
                                package, version = line.split('==', 1)
                                dependencies.append({
                                    "package": package,
                                    "version": version
                                })
                        # 패키지 이름으로 정렬
                        dependencies.sort(key=lambda x: x["package"].lower())
            except Exception as e:
                dependencies = [{"error": f"의존성 정보 조회 실패: {str(e)}"}]
        
        return {
            "deploy_path": deploy_base_dir,
            "deploy_exists": deploy_exists,
            "deploy_file_count": len(deploy_files),
            "deploy_total_size": humanize.naturalsize(deploy_total_size),
            "deploy_files": deploy_files[:30],  # 최대 30개만 반환
            "active_version": active_version.version if active_version else None,
            
            "env_path": env_base_dir,
            "env_exists": env_exists,
            "env_type": module.env,
            "env_subdir": env_subdir,
            "env_file_count": len(env_files),
            "env_total_size": humanize.naturalsize(env_total_size),
            "env_files": env_files[:30],  # 최대 30개만 반환
            
            "dependencies": dependencies,
            "dependency_count": len(dependencies) if dependencies and "error" not in dependencies[0] else 0
        }

    @app.get("/api/logs/errors/download")
    async def download_error_logs(
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(has_role("admin"))
    ):
        query = select(ErrorLog)
        if from_date:
            query = query.where(ErrorLog.created_at >= from_date)
        if to_date:
            query = query.where(ErrorLog.created_at <= to_date)
        query = query.order_by(ErrorLog.created_at.desc()).limit(limit)
        result = await db.execute(query)
        logs = result.scalars().all()
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Code", "Message", "User", "Created At"])
        for log in logs:
            writer.writerow([
                log.id,
                log.code,
                log.message,
                log.user or "",
                (log.created_at.replace(tzinfo=timezone.utc).isoformat() if log.created_at and log.created_at.tzinfo is None else log.created_at.isoformat()) if log.created_at else ""
            ])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=error_logs.csv"}
        )

    @app.get("/api/modules/{name}/versions/{version}", response_model=VersionDetailResponse)
    async def get_module_version_detail(name: str, version: str, db: AsyncSession = Depends(get_db)):
        # 모듈 조회
        result = await db.execute(select(Module).where(Module.name == name))
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")
        # 버전 조회
        version_result = await db.execute(
            select(Version).where(Version.module_id == module.id, Version.version == version)
        )
        version_obj = version_result.scalars().first()
        if not version_obj:
            raise HTTPException(status_code=404, detail="Version not found")
        # code는 inline 타입일 때만 반환, 그 외는 None
        code_value = version_obj.code if module.env == "inline" else None
        created_at_iso = None
        if version_obj.created_at:
            dt = version_obj.created_at
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            created_at_iso = dt.isoformat()
        return VersionDetailResponse(
            version=version_obj.version,
            description=version_obj.description,
            code=code_value,
            created_at=created_at_iso
        )

    app.include_router(modules.router, prefix="/api", tags=["modules"])

    return app

def upgrade_pip(venv_python):
    env = os.environ.copy()
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    subprocess.run([
        venv_python, "-m", "pip", "install", "--upgrade", "pip"
    ], check=True, env=env)

def install_requirements(venv_python, requirements_path):
    env = os.environ.copy()
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    subprocess.run([
        venv_python, "-m", "pip", "install", "-r", requirements_path
    ], check=True, env=env)

def log_module_action(module_name, version, action, message):
    logging.info(f"[{module_name}][v{version}][{action}] {message}")

def _find_requirements_dir(base_dir):
    for root, dirs, files in os.walk(base_dir):
        if "requirements.txt" in files:
            return root
    return base_dir

def _prepare_env_dir(dst_dir, keep_dir_name):
    for item in os.listdir(dst_dir):
        if item == keep_dir_name:
            continue
        item_path = os.path.join(dst_dir, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)

def _copy_src_to_env_dir(src_dir, dst_dir):
    for item in os.listdir(src_dir):
        s = os.path.join(src_dir, item)
        d = os.path.join(dst_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        elif os.path.isfile(s):
            shutil.copy2(s, d)

app = create_app() 