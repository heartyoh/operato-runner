import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./db.sqlite3")

# SQLAlchemy 비동기 엔진 및 세션 생성
engine = create_async_engine(DATABASE_URL, echo=True, future=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# FastAPI 의존성 주입용 세션 생성 함수
def get_db():
    async def _get_db():
        async with AsyncSessionLocal() as session:
            yield session
    return _get_db() 