import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
from alembic import command
from alembic.config import Config
import asyncio

# 테스트용 DB URL (명확히 고정)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import core.db

# 테스트용 엔진/세션
engine = create_async_engine(TEST_DATABASE_URL, echo=True, future=True)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Alembic 마이그레이션 자동 적용
@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    alembic_cfg = Config("alembic.ini")
    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")

# DB 세션 DI 오버라이드
@pytest.fixture(scope="function")
def db_session():
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session
    core.db.get_db = override_get_db
    yield

# FastAPI 앱 DI 오버라이드 (예시)
# from api.rest import app
# app.dependency_overrides[core.db.get_db] = override_get_db 