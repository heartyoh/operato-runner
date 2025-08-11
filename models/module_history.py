from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime
from core.db import get_timestamp_default

class ModuleHistory(Base):
    __tablename__ = 'module_history'
    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey('modules.id'), nullable=False, index=True)
    version_id = Column(Integer, ForeignKey('versions.id'), nullable=False, index=True)
    action = Column(String(32), nullable=False)  # rollback, activate, deactivate
    operator = Column(String(64), nullable=True)
    timestamp = Column(DateTime, server_default=get_timestamp_default(), default=datetime.utcnow, nullable=False)

    module = relationship('Module')
    version = relationship('Version') 