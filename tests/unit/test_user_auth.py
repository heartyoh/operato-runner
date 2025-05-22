import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models.base import Base
from models.user import User
from utils.security import hash_password, verify_password, validate_password_policy

@pytest.mark.asyncio
async def test_user_create_and_authenticate():
    # 임시 DB 엔진/세션
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # 회원 생성
        pw = "Test1234!"
        hashed = hash_password(pw)
        user = User(username="testuser", email="test@example.com", hashed_password=hashed)
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # DB에서 직접 조회
        result = await session.execute(User.__table__.select().where(User.username == "testuser"))
        row = result.first()
        assert row is not None
        db_user = row[0] if isinstance(row, tuple) else row
        # 비밀번호 검증
        assert verify_password(pw, db_user.hashed_password)
        assert not verify_password("WrongPass!", db_user.hashed_password)

    await engine.dispose()

def test_password_policy():
    # 정상 케이스
    validate_password_policy("Test1234!")
    # 실패 케이스
    with pytest.raises(ValueError):
        validate_password_policy("short")
    with pytest.raises(ValueError):
        validate_password_policy("test1234!")  # 대문자 없음
    with pytest.raises(ValueError):
        validate_password_policy("Testtest!")  # 숫자 없음
    with pytest.raises(ValueError):
        validate_password_policy("Test1234")   # 특수문자 없음 