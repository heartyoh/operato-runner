import os
import uuid
import time
import asyncio
import aiofiles
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from core.db import get_sessionmaker
from models.temp_file import TempFile

logger = logging.getLogger(__name__)

class TempFileManager:
    def __init__(self, base_path: str = "/tmp/operato-files"):
        self.base_path = base_path
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        os.makedirs(base_path, exist_ok=True)
    
    def _generate_file_id(self) -> str:
        """고유한 파일 ID 생성"""
        return f"{uuid.uuid4().hex}_{int(time.time())}"
    
    def _sanitize_filename(self, filename: str) -> str:
        """파일명을 안전하게 정리"""
        import re
        import logging
        logger = logging.getLogger(__name__)
        
        # 앞뒤 화이트스페이스 제거
        filename = filename.strip()
        
        # 특수문자 제거, 공백을 언더스코어로 변경
        safe_name = re.sub(r'[^\w\-_\.]', '_', filename)
        
        # 디버깅용 로그
        if filename != safe_name:
            logger.info(f"Filename sanitized: '{filename}' -> '{safe_name}'")
            
        return safe_name[:100]  # 최대 100자로 제한
    
    def _get_file_path(self, file_id: str, filename: str) -> str:
        """파일 저장 경로 생성"""
        safe_filename = self._sanitize_filename(filename)
        return os.path.join(self.base_path, f"{file_id}_{safe_filename}")
    
    async def store_upload(self, file: UploadFile, user_id: int, expires_in_hours: int = 24) -> str:
        """업로드된 파일을 임시 저장하고 파일 ID 반환"""
        # 파일 크기 검증
        content = await file.read()
        if len(content) > self.max_file_size:
            raise ValueError(f"File size exceeds {self.max_file_size} bytes")
        
        # 파일 저장
        file_id = self._generate_file_id()
        file_path = self._get_file_path(file_id, file.filename)
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # DB에 메타데이터 저장
        SessionLocal = get_sessionmaker()
        async with SessionLocal() as db:
            temp_file = TempFile(
                id=file_id,
                file_path=file_path,
                original_filename=file.filename,
                file_size=len(content),
                content_type=file.content_type,
                user_id=user_id,
                file_type='input',
                expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours)
            )
            db.add(temp_file)
            await db.commit()
        
        logger.info(f"Stored upload file {file.filename} as {file_id}")
        return file_id
    
    async def register_result_file(self, file_path: str, user_id: int, expires_in_hours: int = 72) -> str:
        """실행 결과 파일을 등록하고 파일 ID 반환"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Result file not found: {file_path}")
        
        file_id = self._generate_file_id()
        file_size = os.path.getsize(file_path)
        original_filename = os.path.basename(file_path)
        
        # DB에 메타데이터 저장
        SessionLocal = get_sessionmaker()
        async with SessionLocal() as db:
            temp_file = TempFile(
                id=file_id,
                file_path=file_path,
                original_filename=original_filename,
                file_size=file_size,
                content_type=self._get_content_type(file_path),
                user_id=user_id,
                file_type='output',
                expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours)
            )
            db.add(temp_file)
            await db.commit()
        
        logger.info(f"Registered result file {file_path} as {file_id}")
        return file_id
    
    async def get_file_info(self, file_id: str) -> Optional[TempFile]:
        """파일 ID로 파일 정보 조회"""
        SessionLocal = get_sessionmaker()
        async with SessionLocal() as db:
            result = await db.execute(
                select(TempFile).where(TempFile.id == file_id)
            )
            return result.scalar_one_or_none()
    
    async def get_file_path(self, file_id: str) -> Optional[str]:
        """파일 ID로 실제 파일 경로 조회"""
        file_info = await self.get_file_info(file_id)
        if file_info and os.path.exists(file_info.file_path):
            return file_info.file_path
        return None
    
    def create_download_url(self, file_id: str) -> str:
        """다운로드 URL 생성"""
        return f"/api/files/download/{file_id}"
    
    async def cleanup_expired_files(self) -> Dict[str, int]:
        """만료된 파일들을 정리하고 통계 반환"""
        SessionLocal = get_sessionmaker()
        async with SessionLocal() as db:
            # 만료된 파일 조회
            expired_files = await db.execute(
                select(TempFile).where(TempFile.expires_at < datetime.utcnow())
            )
            
            deleted_count = 0
            error_count = 0
            
            for file_record in expired_files.scalars():
                try:
                    # 물리적 파일 삭제
                    if os.path.exists(file_record.file_path):
                        os.unlink(file_record.file_path)
                        logger.info(f"Deleted expired file: {file_record.file_path}")
                    
                    # DB 레코드 삭제
                    await db.delete(file_record)
                    deleted_count += 1
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Failed to cleanup {file_record.file_path}: {e}")
            
            await db.commit()
            
            return {
                "deleted_files": deleted_count,
                "errors": error_count,
                "cleanup_time": datetime.utcnow().isoformat()
            }
    
    async def cleanup_orphaned_files(self) -> int:
        """DB에 기록되지 않은 고아 파일들 정리"""
        orphaned_count = 0
        
        # base_path의 모든 파일 검사
        for filename in os.listdir(self.base_path):
            file_path = os.path.join(self.base_path, filename)
            
            # 24시간 이상 된 파일만 검사
            if os.path.getctime(file_path) < time.time() - (24 * 3600):
                file_id = filename.split('_')[0]
                
                # DB에 기록이 있는지 확인
                file_info = await self.get_file_info(file_id)
                if not file_info:
                    try:
                        os.unlink(file_path)
                        orphaned_count += 1
                        logger.info(f"Deleted orphaned file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to delete orphaned file {file_path}: {e}")
        
        return orphaned_count
    
    def _get_content_type(self, file_path: str) -> str:
        """파일 확장자로 Content-Type 추정"""
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg', 
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.mp4': 'video/mp4',
            '.avi': 'video/avi',
            '.mov': 'video/quicktime',
            '.pdf': 'application/pdf',
            '.json': 'application/json'
        }
        return content_types.get(ext, 'application/octet-stream')

# 전역 인스턴스
temp_file_manager = TempFileManager()

# 백그라운드 정리 태스크
async def start_cleanup_scheduler():
    """정리 스케줄러 시작"""
    while True:
        try:
            # 만료된 파일 정리
            cleanup_stats = await temp_file_manager.cleanup_expired_files()
            logger.info(f"Cleanup completed: {cleanup_stats}")
            
            # 고아 파일 정리
            orphaned_count = await temp_file_manager.cleanup_orphaned_files()
            if orphaned_count > 0:
                logger.info(f"Cleaned {orphaned_count} orphaned files")
                
        except Exception as e:
            logger.error(f"Cleanup scheduler error: {e}")
        
        # 1시간마다 실행
        await asyncio.sleep(3600)