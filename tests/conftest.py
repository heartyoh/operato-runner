import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_dir)

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
from alembic import command
from alembic.config import Config
import asyncio

# 테스트용 DB URL (메모리 DB 사용)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import core.db

# 테스트용 엔진/세션
engine = create_async_engine(
    TEST_DATABASE_URL, 
    echo=False,
    future=True,
    poolclass=None,  # SQLite 메모리 DB를 위해 connection pooling 비활성화
)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 테스트 데이터베이스 테이블 생성
@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    from models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# DB 세션 DI 오버라이드
@pytest.fixture(scope="function")
def db_session():
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session
    core.db.get_db = override_get_db
    yield

# 전역 테스트용 엔진 설정
@pytest.fixture(scope="session", autouse=True)  
def setup_test_engine():
    # 테스트용 엔진으로 core.db 엔진 설정
    core.db.engine = engine
    core.db._session_maker = TestingSessionLocal
    # init_engine 함수 호출로 완전히 초기화
    core.db.init_engine(TEST_DATABASE_URL)

# FastAPI 앱 픽스처
@pytest.fixture
def test_app():
    from api.rest import create_app
    app = create_app()
    
    # 데이터베이스 의존성 오버라이드
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session
    
    app.dependency_overrides[core.db.get_db] = override_get_db
    return app 