from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from .base import Base

class Deployment(Base):
    __tablename__ = 'deployments'
    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey('modules.id'), nullable=False, index=True)
    version_id = Column(Integer, ForeignKey('versions.id'), nullable=False, index=True)
    status = Column(String(20), nullable=False, default='pending', index=True)
    deployed_at = Column(DateTime, server_default=func.now())
    # 관계
    module = relationship('Module', back_populates='deployments')
    version = relationship('Version', back_populates='deployments')

    def __repr__(self):
        return f"<Deployment(id={self.id}, module_id={self.module_id}, version_id={self.version_id}, status='{self.status}')>" 