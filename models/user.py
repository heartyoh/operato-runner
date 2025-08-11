from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime
from core.db import get_timestamp_default

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(128), nullable=False)
    created_at = Column(DateTime, server_default=get_timestamp_default(), default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    roles = relationship('Role', secondary='user_role', back_populates='users')
    modules = relationship('Module', back_populates='owner')
    temp_files = relationship('TempFile', back_populates='user')

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>" 