from sqlalchemy import Column, Integer, String, Text, DateTime, func
from .base import Base

class ModuleValidationLog(Base):
    __tablename__ = 'module_validation_logs'
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False)  # success, fail
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now()) 