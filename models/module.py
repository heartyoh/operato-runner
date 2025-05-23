from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from .base import Base
from pydantic import BaseModel, Field, ValidationError, StrictStr
from datetime import datetime
from typing import Optional, Dict, Any, List

class ModuleSchema(BaseModel):
    name: StrictStr
    env: StrictStr  # 'inline', 'venv', 'conda', 'docker'
    code: Optional[str] = None
    path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    version: str = "0.1.0"
    tags: List[str] = []

    def __str__(self) -> str:
        return f"Module({self.name}, {self.env}, v{self.version})"

class ExecRequest(BaseModel):
    module: str  # module name
    input_json: Dict[str, Any]

class ExecResult(BaseModel):
    result_json: Dict[str, Any]
    exit_code: int
    stderr: Optional[str] = None
    stdout: Optional[str] = None
    duration: float  # seconds

class Module(Base):
    __tablename__ = 'modules'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    code = Column(Text, nullable=True)
    path = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    version = Column(String(20), default="0.1.0")
    tags = Column(String(255), nullable=True)  # JSON 문자열 등으로 저장 가능
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    owner = relationship('User', back_populates='modules')
    versions = relationship('Version', back_populates='module')
    deployments = relationship('Deployment', back_populates='module')
    env = Column(String(20), default="inline", nullable=False)  # 실행 환경 필드 추가
    is_active = Column(Integer, default=1)  # 1: 활성, 0: 비활성

    def __repr__(self):
        return f"<Module(id={self.id}, name='{self.name}', owner_id={self.owner_id})>" 