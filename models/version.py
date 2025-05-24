from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from .base import Base

class Version(Base):
    __tablename__ = 'versions'
    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey('modules.id'), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    code = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    changelog = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    module = relationship('Module', back_populates='versions')
    deployments = relationship('Deployment', back_populates='version', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Version(id={self.id}, module_id={self.module_id}, version='{self.version}')>" 