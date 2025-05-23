from sqlalchemy import Column, Integer, String, Text, DateTime, func
from .base import Base

class ErrorLog(Base):
    __tablename__ = 'error_log'
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), nullable=False)
    message = Column(Text, nullable=False)
    dev_message = Column(Text, nullable=True)
    url = Column(String(255), nullable=True)
    stack = Column(Text, nullable=True)
    user = Column(String(64), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False) 