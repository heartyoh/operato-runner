from fastapi import FastAPI, HTTPException, Depends, Body, Request, UploadFile, File
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from models.module import Module
from module_registry import ModuleRegistry
from executor_manager import ExecutorManager
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db, Base, get_engine
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
from fastapi.responses import JSONResponse
from models.validation_log import ModuleValidationLog

def create_app() -> FastAPI:
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
    @app.get("/modules", response_model=List[ModuleResponse])
    async def list_modules(module_registry: ModuleRegistry = Depends(get_module_registry)):
        modules = await module_registry.list_modules()
        return [
            ModuleResponse(
                name=m.name,
                env=m.env,
                version=m.version,
                created_at=m.created_at.isoformat() if m.created_at else None,
                tags=m.tags if m.tags else []
            ) for m in modules
        ]

    @app.get("/modules/{name}", response_model=ModuleResponse)
    async def get_module(name: str, module_registry: ModuleRegistry = Depends(get_module_registry)):
        module = await module_registry.get_module(name)
        if not module:
            raise HTTPException(status_code=404, detail=f"Module '{name}' not found")
        return ModuleResponse(
            name=module.name,
            env=module.env,
            version=module.version,
            created_at=module.created_at.isoformat() if module.created_at else None,
            tags=module.tags if module.tags else []
        )

    @app.post("/modules", response_model=ModuleResponse, status_code=201)
    async def create_module(
        module_data: ModuleCreate,
        module_registry: ModuleRegistry = Depends(get_module_registry),
        db: AsyncSession = Depends(get_db),
        current_user: UserRead = Depends(get_current_user)
    ):
        if not module_data.code and not module_data.path:
            raise HTTPException(status_code=400, detail="Either code or path must be provided")
        module = Module(
            name=module_data.name,
            env=module_data.env,
            code=module_data.code,
            path=module_data.path,
            version=module_data.version,
            tags=module_data.tags,
            owner_id=current_user.id
        )
        await module_registry.register_module(module)
        await log_audit_event(db, action="module_deploy", detail=f"Module {module.name} deployed", user_id=current_user.id)
        return ModuleResponse(
            name=module.name,
            env=module.env,
            version=module.version,
            created_at=module.created_at.isoformat() if module.created_at else None,
            tags=module.tags if module.tags else []
        )

    @app.delete("/modules/{name}", status_code=204)
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

    @app.post("/modules/upload")
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

    @app.post("/modules/{module_id}/upload")
    async def upload_module_for_id(module_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
        # 1. 모듈 존재 확인
        result = await db.execute(select(Module).where(Module.id == module_id))
        module = result.scalars().first()
        if not module:
            return JSONResponse(status_code=404, content={"detail": f"Module id {module_id} not found"})
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
            # 6. requirements.txt 의존성 설치 자동화 (기존 pip install은 venv 생성 후로 이동)
            import subprocess
            venv_dir = os.path.abspath(f"module_envs/{module_id}/venv")
            os.makedirs(venv_dir, exist_ok=True)
            # 7. venv 생성
            try:
                subprocess.run(["python3", "-m", "venv", venv_dir], check=True)
            except Exception as e:
                log = ModuleValidationLog(filename=file.filename, status="fail", message=f"venv 생성 실패: {str(e)}")
                db.add(log)
                await db.commit()
                return JSONResponse(status_code=500, content={"detail": f"venv 생성 실패: {str(e)}"})
            # 8. venv 내 pip로 requirements.txt 설치
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
            # 9. 성공 기록 및 모듈 정보 갱신
            log = ModuleValidationLog(filename=file.filename, status="success", message="검증 통과 및 venv 생성/설치/모듈 정보 갱신")
            db.add(log)
            module.path = zip_path  # 실제 운영시에는 영구 저장소로 이동 필요
            module.env = venv_dir   # venv 경로를 env 필드에 저장(또는 별도 필드 활용)
            await db.commit()
            return {"detail": "구조/필수 파일 및 handler 함수 검증 통과, venv 생성 및 의존성 설치, 모듈 정보 갱신 완료"}

    return app

app = create_app() 