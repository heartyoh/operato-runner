from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from .base import Base

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

    def __repr__(self):
        return f"<Module(id={self.id}, name='{self.name}', owner_id={self.owner_id})>" 