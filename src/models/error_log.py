from sqlalchemy import Column, Integer, String, Text, DateTime
from .base import Base
from datetime import datetime
from core.db import get_timestamp_default

class ErrorLog(Base):
    __tablename__ = 'error_log'
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), nullable=False)
    message = Column(Text, nullable=False)
    dev_message = Column(Text, nullable=True)
    url = Column(String(255), nullable=True)
    stack = Column(Text, nullable=True)
    user = Column(String(64), nullable=True)
    created_at = Column(DateTime, server_default=get_timestamp_default(), default=datetime.utcnow, nullable=False) 