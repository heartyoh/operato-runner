from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(128), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    roles = relationship('Role', secondary='user_role', back_populates='users')

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>" 