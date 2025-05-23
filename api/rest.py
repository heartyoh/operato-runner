from fastapi import FastAPI, HTTPException, Depends, Body, Request, UploadFile, File, Form
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from models.module import Module
from module_registry import ModuleRegistry
from executor_manager import ExecutorManager
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db, Base, get_engine, init_engine
from models.user import User
from schemas.user import UserCreate, UserRead, UserLogin
from utils.jwt import create_access_token
from api.auth import verify_password, get_current_user, has_role
from utils.security import hash_password, validate_password_policy
import hashlib
from utils.audit import log_audit_event
from models.audit_log import AuditLog
from schemas.audit_log import AuditLogRead
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models import ExecRequest
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
logger = logging.getLogger("uvicorn.error")

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

    class RunRequest(BaseModel):
        input: Dict[str, Any]

    class RunResponse(BaseModel):
        result: Dict[str, Any]
        exit_code: int
        stderr: str
        stdout: str
        duration: float

    # DI: AsyncSession을 받아서 ModuleRegistry 생성
    async def get_module_registry(db: AsyncSession = Depends(get_db)):
        return ModuleRegistry(db)

    def get_executor_manager(request: Request):
        return request.app.state.executor_manager

    # 라우트
    @app.get("/api/modules", response_model=List[ModuleResponse])
    async def list_modules(module_registry: ModuleRegistry = Depends(get_module_registry)):
        modules = await module_registry.list_modules()
        return [
            ModuleResponse(
                name=m.name,
                env=m.env,
                version=m.version,
                created_at=m.created_at.isoformat() if m.created_at else None,
                tags=m.tags.split(",") if isinstance(m.tags, str) else (m.tags if m.tags else [])
            ) for m in modules
        ]

    @app.get("/api/modules/{name}", response_model=ModuleResponse)
    async def get_module(name: str, module_registry: ModuleRegistry = Depends(get_module_registry)):
        module = await module_registry.get_module(name)
        if not module:
            raise CustomException(
                code="MODULE_NOT_FOUND",
                message="모듈을 찾을 수 없습니다.",
                dev_message=f"Module(name={name}) not found in modules table",
                status_code=404
            )
        return ModuleResponse(
            name=module.name,
            env=module.env,
            version=module.version,
            created_at=module.created_at.isoformat() if module.created_at else None,
            tags=module.tags.split(",") if isinstance(module.tags, str) else (module.tags if module.tags else [])
        )

    @app.post("/api/modules", response_model=ModuleResponse, status_code=201)
    async def create_module(
        name: str = Form(...),
        env: str = Form(...),
        version: str = Form("0.1.0"),
        code: str = Form(None),
        description: str = Form(""),
        tags: str = Form(""),
        file: UploadFile = File(None),
        input: str = Form(""),
        module_registry: ModuleRegistry = Depends(get_module_registry),
        db: AsyncSession = Depends(get_db),
        current_user: UserRead = Depends(get_current_user)
    ):
        name = name.strip()
        # input 파싱
        input_dict = {}
        if input:
            import json
            try:
                input_dict = json.loads(input)
            except Exception:
                raise HTTPException(status_code=400, detail="input 필드는 올바른 JSON이어야 합니다.")
        if not code and not file:
            raise HTTPException(status_code=400, detail="Either code or file must be provided")
        # 태그 파싱
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
        if file:
            # 파일 업로드 처리 (임시 디렉토리 저장/압축 해제/검증 등 기존 로직 활용)
            # (기존 upload_module_for_id 참고, 또는 별도 함수로 분리 가능)
            # 여기에 파일 업로드 처리 로직을 추가하세요.
            # 예시: 임시 파일 저장, 압축 해제, handler.py/requirements.txt 검증 등
            # 실제 구현은 기존 upload_module_for_id 또는 upload_module 참고
            raise HTTPException(status_code=501, detail="파일 업로드 등록은 별도 구현 필요")
        elif code:
            # 인라인 코드 등록 처리
            module = Module(
                name=name,
                env=env,
                code=code,
                path=None,
                version=version,
                tags=','.join(tag_list),
                description=description,
                owner_id=current_user.id
            )
            # input_dict를 모듈에 저장하거나 필요시 활용 (예: code 실행 시 전달)
            module.input_example = input_dict if hasattr(module, 'input_example') else None
            await module_registry.register_module(module)
            await log_audit_event(db, action="module_deploy", detail=f"Module {module.name} deployed", user_id=current_user.id)
            return ModuleResponse(
                name=module.name,
                env=module.env,
                version=module.version,
                created_at=module.created_at.isoformat() if module.created_at else None,
                tags=module.tags if module.tags else []
            )

    @app.delete("/api/modules/{name}", status_code=204)
    async def delete_module(
        name: str,
        module_registry: ModuleRegistry = Depends(get_module_registry)
    ):
        deleted = await module_registry.delete_module(name)
        if not deleted:
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
        print("[register] db session id:", id(db))
        print("[register] db.bind(engine) id:", id(getattr(db, 'bind', None)))
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
        db.add(user)
        await db.commit()
        await db.refresh(user)
        # 관계 미리 로드
        result = await db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user.id)
        )
        user = result.scalar_one()
        print("[register] db hash:", user.hashed_password)
        return UserRead.from_orm_safe(user)

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
        access_token = create_access_token({"sub": user.username, "scopes": []})
        await log_audit_event(db, action="login", detail=f"User {user.username} logged in", user_id=user.id)
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
        user.roles = []  # lazy load 방지
        return UserRead.from_orm_safe(user)

    @app.get("/admin")
    async def admin_only(current_user=Depends(has_role("admin"))):
        return {"message": f"Hello, admin {current_user.username}!"}

    @app.get("/audit/logs", response_model=List[AuditLogRead])
    async def get_audit_logs(db: AsyncSession = Depends(get_db), current_user=Depends(has_role("admin"))):
        result = await db.execute(AuditLog.__table__.select().order_by(AuditLog.created_at.desc()))
        logs = result.fetchall()
        return [AuditLogRead.from_orm(row if not isinstance(row, tuple) else row[0]) for row in logs]

    @app.post("/test-init-db")
    async def test_init_db():
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return {"status": "ok"}

    @app.post("/api/modules/upload")
    async def upload_module(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
        # 1. 임시 디렉토리 생성 및 파일 저장
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, file.filename)
            with open(zip_path, "wb") as f:
                content = await file.read()
                f.write(content)
            # 2. 압축 해제
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
            except zipfile.BadZipFile:
                log = ModuleValidationLog(filename=file.filename, status="fail", message="압축 해제 실패: 올바른 zip 파일이 아님")
                db.add(log)
                await db.commit()
                return JSONResponse(status_code=400, content={"detail": "업로드 파일이 올바른 zip 압축파일이 아닙니다."})
            # 3. 필수 파일 검사
            required_files = ["handler.py", "requirements.txt", "README", "README.md"]
            found = {f: False for f in required_files}
            handler_path = None
            for root, dirs, files in os.walk(tmpdir):
                for fname in files:
                    for req in required_files:
                        if fname.lower() == req.lower():
                            found[req] = True
                    if fname.lower() == "handler.py":
                        handler_path = os.path.join(root, fname)
            missing = [f for f, ok in found.items() if not ok and not (f.startswith("README") and (found["README"] or found["README.md"]))]
            if missing:
                log = ModuleValidationLog(filename=file.filename, status="fail", message=f"필수 파일 누락: {', '.join(missing)}")
                db.add(log)
                await db.commit()
                return JSONResponse(status_code=400, content={"detail": f"필수 파일 누락: {', '.join(missing)}"})
            # 4. handler.py 내부에 handler 함수 존재 여부 검사
            if handler_path:
                with open(handler_path, "r", encoding="utf-8") as f:
                    handler_code = f.read()
                if "def handler(" not in handler_code:
                    log = ModuleValidationLog(filename=file.filename, status="fail", message="handler.py에 'def handler' 함수가 없음")
                    db.add(log)
                    await db.commit()
                    return JSONResponse(status_code=400, content={"detail": "handler.py에 'def handler' 함수가 정의되어 있지 않습니다."})
            else:
                log = ModuleValidationLog(filename=file.filename, status="fail", message="handler.py 파일 없음")
                db.add(log)
                await db.commit()
                return JSONResponse(status_code=400, content={"detail": "handler.py 파일을 찾을 수 없습니다."})
            # 성공 기록
            log = ModuleValidationLog(filename=file.filename, status="success", message="검증 통과")
            db.add(log)
            await db.commit()
            return {"detail": "구조/필수 파일 및 handler 함수 검증 통과"}

    @app.post("/api/modules/{module_id}/upload")
    async def upload_module_for_id(module_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
        # 1. 모듈 존재 확인
        result = await db.execute(select(Module).where(Module.id == module_id))
        module = result.scalars().first()
        if not module:
            return JSONResponse(status_code=404, content={"detail": f"Module id {module_id} not found"})
        # 1-1. 중복 버전 업로드 방지 (name+version)
        dup_result = await db.execute(select(Module).where(Module.name == module.name, Module.version == module.version, Module.id != module_id))
        dup = dup_result.scalars().first()
        if dup:
            log = ModuleValidationLog(filename=file.filename, status="fail", message=f"중복 버전 업로드: {module.name} v{module.version}")
            db.add(log)
            await db.commit()
            return JSONResponse(status_code=400, content={"detail": f"이미 등록된 모듈 버전입니다: {module.name} v{module.version}"})
        # 2. 임시 디렉토리 생성 및 파일 저장
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, file.filename)
            with open(zip_path, "wb") as f:
                content = await file.read()
                f.write(content)
            # 3. 압축 해제
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
            except zipfile.BadZipFile:
                log = ModuleValidationLog(filename=file.filename, status="fail", message="압축 해제 실패: 올바른 zip 파일이 아님")
                db.add(log)
                await db.commit()
                return JSONResponse(status_code=400, content={"detail": "업로드 파일이 올바른 zip 압축파일이 아닙니다."})
            # 4. 필수 파일 검사
            required_files = ["handler.py", "requirements.txt", "README", "README.md"]
            found = {f: False for f in required_files}
            handler_path = None
            requirements_path = None
            for root, dirs, files in os.walk(tmpdir):
                for fname in files:
                    for req in required_files:
                        if fname.lower() == req.lower():
                            found[req] = True
                    if fname.lower() == "handler.py":
                        handler_path = os.path.join(root, fname)
                    if fname.lower() == "requirements.txt":
                        requirements_path = os.path.join(root, fname)
            missing = [f for f, ok in found.items() if not ok and not (f.startswith("README") and (found["README"] or found["README.md"]))]
            if missing:
                log = ModuleValidationLog(filename=file.filename, status="fail", message=f"필수 파일 누락: {', '.join(missing)}")
                db.add(log)
                await db.commit()
                return JSONResponse(status_code=400, content={"detail": f"필수 파일 누락: {', '.join(missing)}"})
            # 5. handler.py 내부에 handler 함수 존재 여부 검사
            if handler_path:
                with open(handler_path, "r", encoding="utf-8") as f:
                    handler_code = f.read()
                if "def handler(" not in handler_code:
                    log = ModuleValidationLog(filename=file.filename, status="fail", message="handler.py에 'def handler' 함수가 없음")
                    db.add(log)
                    await db.commit()
                    return JSONResponse(status_code=400, content={"detail": "handler.py에 'def handler' 함수가 정의되어 있지 않습니다."})
            else:
                log = ModuleValidationLog(filename=file.filename, status="fail", message="handler.py 파일 없음")
                db.add(log)
                await db.commit()
                return JSONResponse(status_code=400, content={"detail": "handler.py 파일을 찾을 수 없습니다."})
            # 6. 환경별 독립 실행 환경 자동 생성
            import subprocess
            env_type = module.env.lower() if module.env else "venv"
            if env_type == "venv":
                venv_dir = os.path.abspath(f"module_envs/{module_id}/venv")
                os.makedirs(venv_dir, exist_ok=True)
                try:
                    subprocess.run(["python3", "-m", "venv", venv_dir], check=True)
                except Exception as e:
                    log = ModuleValidationLog(filename=file.filename, status="fail", message=f"venv 생성 실패: {str(e)}")
                    db.add(log)
                    await db.commit()
                    return JSONResponse(status_code=500, content={"detail": f"venv 생성 실패: {str(e)}"})
                if requirements_path:
                    pip_path = os.path.join(venv_dir, "bin", "pip")
                    try:
                        proc = subprocess.run([
                            pip_path, "install", "-r", requirements_path
                        ], capture_output=True, text=True, check=False)
                        if proc.returncode == 0:
                            log = ModuleValidationLog(filename=file.filename, status="success", message=f"venv 내 requirements.txt 의존성 설치 성공\n{proc.stdout}")
                            db.add(log)
                        else:
                            log = ModuleValidationLog(filename=file.filename, status="fail", message=f"venv 내 requirements.txt 의존성 설치 실패\n{proc.stderr}")
                            db.add(log)
                            await db.commit()
                            return JSONResponse(status_code=400, content={"detail": f"venv 내 requirements.txt 의존성 설치 실패", "error": proc.stderr})
                    except Exception as e:
                        log = ModuleValidationLog(filename=file.filename, status="fail", message=f"venv 내 requirements.txt 설치 중 예외: {str(e)}")
                        db.add(log)
                        await db.commit()
                        return JSONResponse(status_code=500, content={"detail": f"venv 내 requirements.txt 설치 중 예외: {str(e)}"})
                module.env = venv_dir
            elif env_type == "conda":
                conda_env_name = f"mod_{module_id}"
                try:
                    subprocess.run(["conda", "create", "-y", "-n", conda_env_name, "python=3.10"], check=True)
                except Exception as e:
                    log = ModuleValidationLog(filename=file.filename, status="fail", message=f"conda 환경 생성 실패: {str(e)}")
                    db.add(log)
                    await db.commit()
                    return JSONResponse(status_code=500, content={"detail": f"conda 환경 생성 실패: {str(e)}"})
                if requirements_path:
                    try:
                        proc = subprocess.run([
                            "conda", "run", "-n", conda_env_name, "pip", "install", "-r", requirements_path
                        ], capture_output=True, text=True, check=False)
                        if proc.returncode == 0:
                            log = ModuleValidationLog(filename=file.filename, status="success", message=f"conda 환경 requirements.txt 설치 성공\n{proc.stdout}")
                            db.add(log)
                        else:
                            log = ModuleValidationLog(filename=file.filename, status="fail", message=f"conda 환경 requirements.txt 설치 실패\n{proc.stderr}")
                            db.add(log)
                            await db.commit()
                            return JSONResponse(status_code=400, content={"detail": f"conda 환경 requirements.txt 설치 실패", "error": proc.stderr})
                    except Exception as e:
                        log = ModuleValidationLog(filename=file.filename, status="fail", message=f"conda 환경 requirements.txt 설치 중 예외: {str(e)}")
                        db.add(log)
                        await db.commit()
                        return JSONResponse(status_code=500, content={"detail": f"conda 환경 requirements.txt 설치 중 예외: {str(e)}"})
                module.env = conda_env_name
            elif env_type == "docker":
                docker_tag = f"mod_{module_id}:latest"
                dockerfile_path = os.path.join(tmpdir, "Dockerfile")
                # Dockerfile 생성
                with open(dockerfile_path, "w") as df:
                    df.write("FROM python:3.10-slim\n")
                    df.write("WORKDIR /app\n")
                    df.write("COPY . /app\n")
                    if requirements_path:
                        df.write("RUN pip install --no-cache-dir -r requirements.txt\n")
                    df.write("CMD [\"python\", \"handler.py\"]\n")
                try:
                    proc = subprocess.run([
                        "docker", "build", "-t", docker_tag, tmpdir
                    ], capture_output=True, text=True, check=False)
                    if proc.returncode == 0:
                        log = ModuleValidationLog(filename=file.filename, status="success", message=f"docker 이미지 빌드 성공\n{proc.stdout}")
                        db.add(log)
                    else:
                        log = ModuleValidationLog(filename=file.filename, status="fail", message=f"docker 이미지 빌드 실패\n{proc.stderr}")
                        db.add(log)
                        await db.commit()
                        return JSONResponse(status_code=400, content={"detail": f"docker 이미지 빌드 실패", "error": proc.stderr})
                except Exception as e:
                    log = ModuleValidationLog(filename=file.filename, status="fail", message=f"docker 이미지 빌드 중 예외: {str(e)}")
                    db.add(log)
                    await db.commit()
                    return JSONResponse(status_code=500, content={"detail": f"docker 이미지 빌드 중 예외: {str(e)}"})
                module.env = docker_tag
            else:
                log = ModuleValidationLog(filename=file.filename, status="fail", message=f"알 수 없는 env 타입: {env_type}")
                db.add(log)
                await db.commit()
                return JSONResponse(status_code=400, content={"detail": f"알 수 없는 env 타입: {env_type}"})
            # 7. 성공 기록 및 모듈 정보 갱신
            log = ModuleValidationLog(filename=file.filename, status="success", message="검증 통과 및 환경 생성/설치/모듈 정보 갱신")
            db.add(log)
            module.path = zip_path  # 실제 운영시에는 영구 저장소로 이동 필요
            await db.commit()
            return {"detail": f"구조/필수 파일 및 handler 함수 검증 통과, {env_type} 환경 생성 및 의존성 설치, 모듈 정보 갱신 완료"}

    @app.post("/modules/{module_id}/activate")
    async def activate_module(id: int, db: AsyncSession = Depends(get_db), current_user: UserRead = Depends(get_current_user)):
        result = await db.execute(select(Module).where(Module.id == id))
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")
        if getattr(module, 'status', None) == 'active':
            raise HTTPException(status_code=400, detail="이미 활성화된 모듈입니다.")
        # handler 정상 동작 확인 (간단히 import 및 함수 존재만 체크)
        try:
            env_type = module.env.lower() if module.env else "venv"
            if env_type == "venv":
                handler_path = os.path.join(module.env, "../..", "handler.py")
            elif env_type == "conda":
                handler_path = os.path.join("modules", str(id), "handler.py")
            elif env_type == "docker":
                handler_path = None  # docker는 별도 실행 필요
            else:
                handler_path = None
            if handler_path and os.path.exists(handler_path):
                with open(handler_path, "r", encoding="utf-8") as f:
                    code = f.read()
                if "def handler(" not in code:
                    raise Exception("handler 함수가 없습니다.")
            # docker는 실제 컨테이너 실행 등 추가 구현 필요
        except Exception as e:
            await log_audit_event(db, action="module_activate_fail", detail=f"Module {module.name} activate fail: {str(e)}", user_id=current_user.id)
            raise HTTPException(status_code=400, detail=f"핸들러 동작 확인 실패: {str(e)}")
        module.status = 'active'
        await db.commit()
        await log_audit_event(db, action="module_activate", detail=f"Module {module.name} activated", user_id=current_user.id)
        return {"detail": "모듈이 활성화되었습니다."}

    @app.post("/modules/{module_id}/deactivate")
    async def deactivate_module(id: int, db: AsyncSession = Depends(get_db), current_user: UserRead = Depends(get_current_user)):
        result = await db.execute(select(Module).where(Module.id == id))
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")
        if getattr(module, 'status', None) == 'inactive':
            raise HTTPException(status_code=400, detail="이미 비활성화된 모듈입니다.")
        module.status = 'inactive'
        await db.commit()
        await log_audit_event(db, action="module_deactivate", detail=f"Module {module.name} deactivated", user_id=current_user.id)
        return {"detail": "모듈이 비활성화되었습니다."}

    @app.delete("/modules/{id}/delete")
    async def delete_module_api(id: int, db: AsyncSession = Depends(get_db), current_user: UserRead = Depends(get_current_user)):
        result = await db.execute(select(Module).where(Module.id == id))
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")
        if getattr(module, 'status', None) == 'deleted':
            raise HTTPException(status_code=400, detail="이미 삭제된 모듈입니다.")
        module.status = 'deleted'
        await db.commit()
        await log_audit_event(db, action="module_delete", detail=f"Module {module.name} deleted", user_id=current_user.id)
        # 환경/파일 정리(필요시)
        return {"detail": "모듈이 삭제되었습니다."}

    @app.post("/modules/{id}/run")
    async def run_module_api(id: int, input: dict = Body(...), db: AsyncSession = Depends(get_db), current_user: UserRead = Depends(get_current_user)):
        result = await db.execute(select(Module).where(Module.id == id))
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")
        if getattr(module, 'status', None) != 'active':
            raise HTTPException(status_code=400, detail="비활성화된 모듈입니다.")
        env_type = module.env.lower() if module.env else "venv"
        try:
            # venv/conda: handler.py 직접 실행, docker: docker run 등 분기
            if env_type == "venv":
                import importlib.util
                import sys
                handler_path = os.path.abspath(os.path.join(module.env, "../..", "handler.py"))
                spec = importlib.util.spec_from_file_location("handler", handler_path)
                handler_mod = importlib.util.module_from_spec(spec)
                sys.modules["handler"] = handler_mod
                spec.loader.exec_module(handler_mod)
                result_data = handler_mod.handler(input)
            elif env_type == "conda":
                # 실제로는 conda 환경에서 별도 프로세스 실행 필요(여기선 단순화)
                handler_path = os.path.join("modules", str(id), "handler.py")
                import importlib.util
                import sys
                spec = importlib.util.spec_from_file_location("handler", handler_path)
                handler_mod = importlib.util.module_from_spec(spec)
                sys.modules["handler"] = handler_mod
                spec.loader.exec_module(handler_mod)
                result_data = handler_mod.handler(input)
            elif env_type == "docker":
                # 실제로는 docker run 명령으로 실행해야 함(여기선 생략/로깅)
                result_data = {"detail": "docker 환경 실행은 별도 구현 필요"}
            else:
                raise Exception(f"알 수 없는 env 타입: {env_type}")
            await log_audit_event(db, action="module_run", detail=f"Module {module.name} run 성공", user_id=current_user.id)
            return {"result": result_data}
        except Exception as e:
            await log_audit_event(db, action="module_run_fail", detail=f"Module {module.name} run 실패: {str(e)}", user_id=current_user.id)
            raise HTTPException(status_code=500, detail=f"모듈 실행 실패: {str(e)}")

    @app.get("/modules/{id}/status")
    async def get_module_status(id: int, db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Module).where(Module.id == id))
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")
        return {"id": id, "name": module.name, "status": getattr(module, 'status', None)}

    @app.get("/modules/{id}/history")
    async def get_module_history(id: int, db: AsyncSession = Depends(get_db), current_user: UserRead = Depends(get_current_user)):
        # AuditLog에서 해당 모듈 관련 이력 반환(간단히 action/detail에 모듈명 포함된 것)
        from models.audit_log import AuditLog
        result = await db.execute(AuditLog.__table__.select().where(AuditLog.detail.contains(str(id))).order_by(AuditLog.created_at.desc()))
        logs = result.fetchall()
        return [dict(row) if not isinstance(row, tuple) else dict(row[0]) for row in logs]

    @app.get("/api/modules/{name}/versions")
    async def get_module_versions(name: str, db: AsyncSession = Depends(get_db)):
        # 해당 모듈의 모든 버전 및 상태 조회
        result = await db.execute(select(Module).where(Module.name == name))
        module = result.scalars().first()
        if not module:
            raise CustomException(
                code="MODULE_NOT_FOUND",
                message="모듈을 찾을 수 없습니다.",
                dev_message=f"Module(name={name}) not found in modules table",
                status_code=404
            )
        versions = await db.execute(select(Version).where(Version.module_id == module.id))
        version_list = versions.scalars().all()
        deployments = await db.execute(select(Deployment).where(Deployment.module_id == module.id))
        deployment_list = deployments.scalars().all()
        # 버전별 상태 매핑
        version_status = {d.version_id: d.status for d in deployment_list}
        return [
            {
                "id": v.id,
                "version": v.version,
                "created_at": v.created_at,
                "status": version_status.get(v.id, "inactive")
            } for v in version_list
        ]

    @app.post("/api/modules/{name}/rollback")
    async def rollback_module(name: str, version: str = Body(..., embed=True), db: AsyncSession = Depends(get_db), current_user: UserRead = Depends(get_current_user)):
        # 롤백: 해당 모듈의 지정 버전을 활성화, 나머지는 비활성화
        result = await db.execute(select(Module).where(Module.name == name))
        module = result.scalars().first()
        if not module:
            raise CustomException(
                code="MODULE_NOT_FOUND",
                message="모듈을 찾을 수 없습니다.",
                dev_message=f"Module(name={name}) not found in modules table",
                status_code=404
            )
        v_result = await db.execute(select(Version).where(Version.module_id == module.id, Version.version == version))
        version_obj = v_result.scalars().first()
        if not version_obj:
            raise CustomException(
                code="VERSION_NOT_FOUND",
                message="지정한 버전을 찾을 수 없습니다.",
                dev_message=f"Version({version}) not found for module_id={module.id}",
                status_code=404
            )
        # deployments: 해당 버전만 active, 나머지 inactive
        deployments = await db.execute(select(Deployment).where(Deployment.module_id == module.id))
        for d in deployments.scalars().all():
            d.status = "active" if d.version_id == version_obj.id else "inactive"
        # modules 테이블도 is_active=1로 갱신
        module.version = version
        module.is_active = 1
        await db.commit()
        # 이력 기록
        history = ModuleHistory(module_id=module.id, version_id=version_obj.id, action="rollback", operator=current_user.username)
        db.add(history)
        await db.commit()
        return {"detail": f"롤백 완료: {name} v{version}"}

    @app.post("/api/modules/{name}/activate")
    async def activate_module_version(name: str, version: str = Body(..., embed=True), db: AsyncSession = Depends(get_db), current_user: UserRead = Depends(get_current_user)):
        result = await db.execute(select(Module).where(Module.name == name))
        module = result.scalars().first()
        if not module:
            raise CustomException(
                code="MODULE_NOT_FOUND",
                message="모듈을 찾을 수 없습니다.",
                dev_message=f"Module(name={name}) not found in modules table",
                status_code=404
            )
        v_result = await db.execute(select(Version).where(Version.module_id == module.id, Version.version == version))
        version_obj = v_result.scalars().first()
        if not version_obj:
            raise CustomException(
                code="VERSION_NOT_FOUND",
                message="지정한 버전을 찾을 수 없습니다.",
                dev_message=f"Version({version}) not found for module_id={module.id}",
                status_code=404
            )
        deployments = await db.execute(select(Deployment).where(Deployment.module_id == module.id))
        for d in deployments.scalars().all():
            d.status = "active" if d.version_id == version_obj.id else "inactive"
        module.version = version
        module.is_active = 1
        await db.commit()
        history = ModuleHistory(module_id=module.id, version_id=version_obj.id, action="activate", operator=current_user.username)
        db.add(history)
        await db.commit()
        return {"detail": f"활성화 완료: {name} v{version}"}

    @app.post("/api/modules/{name}/deactivate")
    async def deactivate_module_version(name: str, version: str = Body(..., embed=True), db: AsyncSession = Depends(get_db), current_user: UserRead = Depends(get_current_user)):
        result = await db.execute(select(Module).where(Module.name == name))
        module = result.scalars().first()
        if not module:
            raise CustomException(
                code="MODULE_NOT_FOUND",
                message="모듈을 찾을 수 없습니다.",
                dev_message=f"Module(name={name}) not found in modules table",
                status_code=404
            )
        v_result = await db.execute(select(Version).where(Version.module_id == module.id, Version.version == version))
        version_obj = v_result.scalars().first()
        if not version_obj:
            raise CustomException(
                code="VERSION_NOT_FOUND",
                message="지정한 버전을 찾을 수 없습니다.",
                dev_message=f"Version({version}) not found for module_id={module.id}",
                status_code=404
            )
        deployments = await db.execute(select(Deployment).where(Deployment.module_id == module.id, Deployment.version_id == version_obj.id))
        for d in deployments.scalars().all():
            d.status = "inactive"
        await db.commit()
        history = ModuleHistory(module_id=module.id, version_id=version_obj.id, action="deactivate", operator=current_user.username)
        db.add(history)
        await db.commit()
        return {"detail": f"비활성화 완료: {name} v{version}"}

    @app.get("/api/modules/{name}/history", response_model=List[ModuleHistoryRead])
    async def get_module_history(name: str, db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Module).where(Module.name == name))
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")
        history_result = await db.execute(select(ModuleHistory).where(ModuleHistory.module_id == module.id).order_by(ModuleHistory.timestamp.desc()))
        return history_result.scalars().all()

    @app.get("/api/logs/errors", response_model=list[ErrorLogRead])
    async def get_error_logs(
        code: str = None,
        user: str = None,
        from_: str = None,
        to: str = None,
        keyword: str = None,
        limit: int = 100,
        offset: int = 0,
        db: AsyncSession = Depends(get_db)
    ):
        from models.error_log import ErrorLog
        filters = []
        if code:
            filters.append(ErrorLog.code == code)
        if user:
            filters.append(ErrorLog.user == user)
        if from_:
            filters.append(ErrorLog.created_at >= from_)
        if to:
            filters.append(ErrorLog.created_at <= to)
        if keyword:
            kw = f"%{keyword}%"
            filters.append(or_(ErrorLog.message.like(kw), ErrorLog.dev_message.like(kw), ErrorLog.stack.like(kw)))
        q = select(ErrorLog).where(and_(*filters)) if filters else select(ErrorLog)
        q = q.order_by(ErrorLog.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(q)
        logs = result.scalars().all()
        return logs

    @app.get("/api/logs/errors/download")
    async def download_error_logs(
        code: str = None,
        user: str = None,
        from_: str = None,
        to: str = None,
        keyword: str = None,
        db: AsyncSession = Depends(get_db)
    ):
        from models.error_log import ErrorLog
        filters = []
        if code:
            filters.append(ErrorLog.code == code)
        if user:
            filters.append(ErrorLog.user == user)
        if from_:
            filters.append(ErrorLog.created_at >= from_)
        if to:
            filters.append(ErrorLog.created_at <= to)
        if keyword:
            kw = f"%{keyword}%"
            filters.append(or_(ErrorLog.message.like(kw), ErrorLog.dev_message.like(kw), ErrorLog.stack.like(kw)))
        q = select(ErrorLog).where(and_(*filters)) if filters else select(ErrorLog)
        q = q.order_by(ErrorLog.created_at.desc())
        result = await db.execute(q)
        logs = result.scalars().all()
        # CSV 변환
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "code", "message", "dev_message", "url", "stack", "user", "created_at"])
        for l in logs:
            writer.writerow([
                l.id, l.code, l.message, l.dev_message, l.url, l.stack, l.user, l.created_at
            ])
        output.seek(0)
        return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=error_logs.csv"})

    @app.get("/api/templates/module")
    async def download_module_template():
        return FileResponse(
            "templates/module_template.zip",
            media_type="application/zip",
            filename="module_template.zip"
        )

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

    return app

app = create_app() 