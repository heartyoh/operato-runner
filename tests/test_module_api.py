import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tempfile
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from core.db import Base, get_db
# 관계 모델 명시적 import (SQLAlchemy registry 등록)
from models.version import Version
from models.module import Module
from models.deployment import Deployment
from models.role import Role
from models.user import User
from models.audit_log import AuditLog

@pytest.fixture
def temp_db_url():
    db_fd, db_path = tempfile.mkstemp(suffix=".sqlite3")
    url = f"sqlite+aiosqlite:///{db_path}?cache=shared"
    yield url
    os.close(db_fd)
    os.remove(db_path)

@pytest.fixture
def fresh_app(temp_db_url):
    import core.db as dbmod
    from api.rest import create_app
    app = create_app()
    # DB 엔진/세션 생성
    engine = create_async_engine(temp_db_url, future=True, connect_args={"check_same_thread": False})
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    # 테이블 생성
    import asyncio
    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    asyncio.get_event_loop().run_until_complete(create_tables())
    # DI 오버라이드
    async def _get_db():
        async with async_session() as session:
            yield session
    app.dependency_overrides[dbmod.get_db] = _get_db
    # 글로벌 세션/엔진 patch
    dbmod.engine = engine
    dbmod.AsyncSessionLocal = async_session
    yield app
    asyncio.get_event_loop().run_until_complete(engine.dispose())

@pytest.mark.asyncio
async def test_module_crud_flow(fresh_app):
    app = fresh_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. 회원가입 및 로그인
        resp = await ac.post("/auth/register", json={
            "username": "moduser",
            "email": "moduser@example.com",
            "password": "Moduser123!"
        })
        print('register response:', resp.text)
        assert resp.status_code == 201
        resp = await ac.post("/auth/login", json={
            "username": "moduser",
            "email": "moduser@example.com",
            "password": "Moduser123!"
        })
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. 모듈 등록
        resp = await ac.post("/modules", json={
            "name": "testmod",
            "env": "inline",
            "code": "def handler(input): return input",
            "version": "0.1.0",
            "tags": ["test"]
        }, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "testmod"
        assert data["env"] == "inline"
        assert data["version"] == "0.1.0"
        assert "created_at" in data
        assert data["tags"] == ["test"]

        # 3. 모듈 목록 조회
        resp = await ac.get("/modules", headers=headers)
        assert resp.status_code == 200
        modules = resp.json()
        assert any(m["name"] == "testmod" for m in modules)

        # 4. 단일 모듈 조회
        resp = await ac.get("/modules/testmod", headers=headers)
        assert resp.status_code == 200
        mod = resp.json()
        assert mod["name"] == "testmod"

        # 5. 모듈 삭제
        resp = await ac.delete("/modules/testmod", headers=headers)
        assert resp.status_code == 204

        # 6. 삭제 후 조회 시 404
        resp = await ac.get("/modules/testmod", headers=headers)
        assert resp.status_code == 404 