import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")

# Base 정의 (모델에서 import)
Base = declarative_base()

# 싱글턴 엔진/세션
engine = None
SessionLocal = None

def init_engine(db_url=DATABASE_URL):
    global engine, SessionLocal
    if engine is None:
        engine = create_async_engine(
            db_url,
            future=True,
            connect_args={"check_same_thread": False}
        )
        SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# FastAPI 의존성 주입용 세션 생성 함수
async def get_db():
    async with SessionLocal() as session:
        yield session

# SQLAlchemy 동기 엔진 (Alembic용)
SYNC_DATABASE_URL = DATABASE_URL.replace("+aiosqlite", "") if "+aiosqlite" in DATABASE_URL else DATABASE_URL
sync_engine = create_engine(SYNC_DATABASE_URL, echo=True, future=True)

def get_db_url():
    return DATABASE_URL

def get_engine():
    return engine

def get_sessionmaker():
    engine = get_engine()
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    SessionLocal = get_sessionmaker()
    async with SessionLocal() as session:
        yield session 