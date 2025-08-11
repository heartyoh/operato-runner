from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class TempFile(Base):
    __tablename__ = 'temp_files'
    
    id = Column(String(100), primary_key=True, index=True)  # UUID + timestamp
    file_path = Column(String(500), nullable=False)  # 실제 파일 경로
    original_filename = Column(String(255), nullable=False)  # 원본 파일명
    file_size = Column(BigInteger, nullable=False)  # 파일 크기 (bytes)
    content_type = Column(String(100), nullable=True)  # MIME 타입
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # 파일 소유자
    file_type = Column(String(20), nullable=False, default='input')  # 'input', 'output', 'directory'
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)  # 만료 시간
    
    # 관계 설정
    user = relationship('User', back_populates='temp_files')
    
    def __repr__(self):
        return f"<TempFile(id='{self.id}', filename='{self.original_filename}', user_id={self.user_id})>"
    
    @property
    def is_expired(self) -> bool:
        """파일이 만료되었는지 확인"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def size_human(self) -> str:
        """사람이 읽기 쉬운 파일 크기"""
        import humanize
        return humanize.naturalsize(self.file_size)