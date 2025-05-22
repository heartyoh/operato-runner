import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yaml
from sqlalchemy.orm import Session
from core.db import sync_engine, Base
from models.module import Module
from models.user import User  # 관계 모델 명시적 import
from models.role import Role  # 필요시 추가 import
from models.version import Version  # 추가
from models.deployment import Deployment  # 추가

# 1. YAML 파일 로드
yaml_path = "modules.yaml"
with open(yaml_path, "r", encoding="utf-8") as f:
    modules_data = yaml.safe_load(f)

# 2. DB 테이블 생성 (없으면)
Base.metadata.create_all(bind=sync_engine)

# 3. 세션 생성
session = Session(bind=sync_engine)

# 4. 데이터 삽입
def to_str(val):
    if val is None:
        return None
    if isinstance(val, list):
        return ",".join(str(v) for v in val)
    return str(val)

for name, info in modules_data.items():
    module = Module(
        name=name,
        env=info.get("env", "inline"),
        path=info.get("path"),
        code=info.get("code"),
        version=to_str(info.get("version", "0.1.0")),
        description=info.get("description"),
        tags=to_str(info.get("tags")),
        owner_id=None
    )
    session.add(module)

session.commit()
session.close()
print(f"{yaml_path} → DB 반영 완료") 