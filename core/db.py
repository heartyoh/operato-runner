import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine, text, func
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv(override=True)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")

# 동기용 URL: .env에 SYNC_DATABASE_URL이 있으면 우선 사용, 없으면 DATABASE_URL에서 변환
SYNC_DATABASE_URL = os.getenv("SYNC_DATABASE_URL")
if not SYNC_DATABASE_URL:
    if "+asyncpg" in DATABASE_URL:
        SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "+psycopg2")
    elif "+aiosqlite" in DATABASE_URL:
        SYNC_DATABASE_URL = DATABASE_URL.replace("+aiosqlite", "")
    else:
        SYNC_DATABASE_URL = DATABASE_URL

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
            connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {}
        )
        SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# FastAPI 의존성 주입용 세션 생성 함수
async def get_db():
    async with SessionLocal() as session:
        yield session

# SQLAlchemy 동기 엔진 (Alembic용)
sync_engine = create_engine(SYNC_DATABASE_URL, echo=True, future=True)

def get_db_url():
    return DATABASE_URL

def get_engine():
    return engine

def get_sessionmaker():
    engine = get_engine()
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

def get_database_type():
    """데이터베이스 타입을 반환합니다."""
    if "+aiosqlite" in DATABASE_URL or DATABASE_URL.startswith("sqlite"):
        return "sqlite"
    elif "+asyncpg" in DATABASE_URL or "+psycopg2" in DATABASE_URL:
        return "postgresql"
    elif "+aiomysql" in DATABASE_URL or "+pymysql" in DATABASE_URL:
        return "mysql"
    else:
        return "unknown"

def get_timestamp_default():
    """데이터베이스 타입에 따른 timestamp 기본값을 반환합니다."""
    db_type = get_database_type()
    
    if db_type == "sqlite":
        return text("(datetime('now'))")
    elif db_type in ["postgresql", "mysql"]:
        return func.now()
    else:
        # 알 수 없는 타입인 경우 None 반환 (Python 레벨에서 처리)
        return None

def get_timestamp_onupdate():
    """데이터베이스 타입에 따른 timestamp onupdate 값을 반환합니다."""
    db_type = get_database_type()
    
    if db_type == "sqlite":
        return text("(datetime('now'))")
    elif db_type in ["postgresql", "mysql"]:
        return func.now()
    else:
        return None

async def get_db():
    SessionLocal = get_sessionmaker()
    async with SessionLocal() as session:
        yield session 