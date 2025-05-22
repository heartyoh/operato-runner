from passlib.context import CryptContext
import re

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 비밀번호 해싱
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# 비밀번호 검증
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 비밀번호 정책 검사 (최소 8자, 대/소문자, 숫자, 특수문자 포함)
def validate_password_policy(password: str) -> None:
    if len(password) < 8:
        raise ValueError("비밀번호는 최소 8자 이상이어야 합니다.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("비밀번호에 대문자가 포함되어야 합니다.")
    if not re.search(r"[a-z]", password):
        raise ValueError("비밀번호에 소문자가 포함되어야 합니다.")
    if not re.search(r"[0-9]", password):
        raise ValueError("비밀번호에 숫자가 포함되어야 합니다.")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\",.<>/?]", password):
        raise ValueError("비밀번호에 특수문자가 포함되어야 합니다.") 