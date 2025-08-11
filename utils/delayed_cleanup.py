import asyncio
import os
import shutil
import logging
from typing import Set
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

class DelayedCleanupManager:
    """임시 작업 디렉토리의 지연 삭제를 관리하는 클래스"""
    
    def __init__(self):
        self._scheduled_dirs: Set[str] = set()
        self._lock = threading.Lock()
    
    def schedule_cleanup(self, directory_path: str, delay_minutes: int = 30) -> None:
        """디렉토리를 지정된 시간(분) 후에 삭제하도록 예약"""
        abs_path = os.path.abspath(directory_path)
        
        with self._lock:
            if abs_path in self._scheduled_dirs:
                logger.debug(f"Directory already scheduled for cleanup: {abs_path}")
                return
            self._scheduled_dirs.add(abs_path)
        
        # 백그라운드에서 지연 삭제 실행
        def delayed_delete():
            import time
            time.sleep(delay_minutes * 60)  # 분을 초로 변환
            self._cleanup_directory(abs_path)
        
        thread = threading.Thread(target=delayed_delete, daemon=True)
        thread.start()
        
        logger.info(f"Scheduled directory cleanup in {delay_minutes} minutes: {abs_path}")
    
    def _cleanup_directory(self, directory_path: str) -> None:
        """실제 디렉토리 삭제를 수행"""
        try:
            with self._lock:
                self._scheduled_dirs.discard(directory_path)
            
            if os.path.exists(directory_path):
                shutil.rmtree(directory_path, ignore_errors=True)
                logger.info(f"Successfully cleaned up directory: {directory_path}")
            else:
                logger.debug(f"Directory already removed: {directory_path}")
                
        except Exception as e:
            logger.error(f"Failed to cleanup directory {directory_path}: {str(e)}")
    
    def cleanup_now(self, directory_path: str) -> None:
        """즉시 디렉토리 삭제 (예약된 경우 예약도 취소)"""
        abs_path = os.path.abspath(directory_path)
        
        with self._lock:
            self._scheduled_dirs.discard(abs_path)
        
        self._cleanup_directory(abs_path)
    
    def get_scheduled_directories(self) -> Set[str]:
        """예약된 디렉토리 목록 반환"""
        with self._lock:
            return self._scheduled_dirs.copy()

# 전역 인스턴스
delayed_cleanup_manager = DelayedCleanupManager()