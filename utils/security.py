import re
import traceback
import bcrypt

print("[bcrypt] version:", getattr(bcrypt, "__version__", "?"))
print("[bcrypt] C-extension:", getattr(bcrypt, "_bcrypt", None) is not None)

# 비밀번호 해싱
def hash_password(password: str) -> str:
    try:
        print("[hash_password] input type:", type(password), "value:", repr(password))
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        print("[hash_password] hashed type:", type(hashed), "value:", repr(hashed))
        return hashed
    except Exception as e:
        print("[hash_password] Exception:", e)
        traceback.print_exc()
        raise

# 비밀번호 검증
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        print("[verify_password] plain type:", type(plain_password), "value:", repr(plain_password))
        print("[verify_password] hash type:", type(hashed_password), "value:", repr(hashed_password))
        result = bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
        print("[verify_password] checkpw result:", result)
        return result
    except Exception as e:
        print("[verify_password] Exception:", e)
        traceback.print_exc()
        return False

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