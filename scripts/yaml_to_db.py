import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yaml
from sqlalchemy.orm import Session
from src.core.db import sync_engine, Base
from src.models.module import Module
from src.models.user import User  # 관계 모델 명시적 import
from src.models.role import Role  # 필요시 추가 import
from src.models.version import Version  # 추가
from src.models.deployment import Deployment  # 추가
from passlib.context import CryptContext

# 1. YAML 파일 로드
yaml_path = "modules.yaml"
with open(yaml_path, "r", encoding="utf-8") as f:
    modules_data = yaml.safe_load(f)

# 2. DB 테이블 생성 (없으면)
Base.metadata.create_all(bind=sync_engine)

# 3. 세션 생성
session = Session(bind=sync_engine)

# 4. admin 유저 생성 또는 확인
def create_admin_user():
    """admin 유저 생성 또는 기존 유저 반환"""
    admin_user = session.query(User).filter(User.username == "admin").first()
    if not admin_user:
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash("admin123")  # 기본 패스워드
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=hashed_password,
            is_active=True
        )
        session.add(admin_user)
        session.commit()
        print("✅ admin 유저 생성 완료")
    else:
        print("ℹ️  admin 유저 이미 존재")
    return admin_user

# 5. 데이터 삽입
def to_str(val):
    if val is None:
        return None
    if isinstance(val, list):
        return ",".join(str(v) for v in val)
    return str(val)

# admin 유저 생성
admin_user = create_admin_user()

for name, info in modules_data.items():
    # 기존 모듈이 있는지 확인
    existing_module = session.query(Module).filter(Module.name == name).first()
    if existing_module:
        print(f"ℹ️  모듈 '{name}' 이미 존재, 스킵")
        continue
        
    module = Module(
        name=name,
        env=info.get("env", "inline"),
        path=info.get("path"),
        code=info.get("code"),
        version=to_str(info.get("version", "0.1.0")),
        description=info.get("description"),
        tags=to_str(info.get("tags")),
        owner_id=admin_user.id  # admin을 owner로 설정
    )
    session.add(module)
    print(f"✅ 모듈 '{name}' 추가됨 (owner: admin)")

session.commit()
session.close()
print(f"{yaml_path} → DB 반영 완료") 