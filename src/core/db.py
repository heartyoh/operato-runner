import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine, text, func
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv(override=True)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")

def convert_to_sync_url(async_url):
    """비동기 URL을 동기 URL로 변환"""
    if not async_url:
        return 'sqlite:///./app.db'
    
    # 드라이버 매핑
    driver_mappings = {
        '+asyncpg': '+psycopg2',      # PostgreSQL
        '+aiosqlite': '',             # SQLite  
        '+aiomysql': '+pymysql',      # MySQL
        '+asyncmy': '+pymysql'        # MySQL alternative
    }
    
    sync_url = async_url
    for async_driver, sync_driver in driver_mappings.items():
        if async_driver in sync_url:
            sync_url = sync_url.replace(async_driver, sync_driver)
            break
    
    return sync_url

# 통합 DATABASE_URL 사용 (동기 버전 자동 생성)
SYNC_DATABASE_URL = convert_to_sync_url(DATABASE_URL)

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