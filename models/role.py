from sqlalchemy import Column, Integer, String, Text, Table, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

# Association table for User-Role N:M
user_role = Table(
    'user_role', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    users = relationship('User', secondary='user_role', back_populates='roles')

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>" 