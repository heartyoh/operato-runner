import pytest
import os
import tempfile
import asyncio
from datetime import datetime, timedelta
from fastapi import UploadFile
from io import BytesIO
from utils.file_storage import TempFileManager
from models.temp_file import TempFile
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import TestingSessionLocal

@pytest.fixture
async def temp_file_manager():
    """테스트용 임시 파일 매니저"""
    test_dir = tempfile.mkdtemp()
    manager = TempFileManager(base_path=test_dir)
    yield manager
    
    # 정리
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)

@pytest.fixture
def sample_video_file():
    """테스트용 가짜 동영상 파일"""
    content = b"fake video content for testing"
    return UploadFile(
        filename="test_video.mp4",
        file=BytesIO(content),
        size=len(content),
        content_type="video/mp4"
    )

@pytest.fixture
def sample_image_file():
    """테스트용 가짜 이미지 파일"""
    content = b"fake image content for testing"
    return UploadFile(
        filename="test_image.jpg", 
        file=BytesIO(content),
        size=len(content),
        content_type="image/jpeg"
    )

@pytest.mark.asyncio
async def test_store_upload_file(temp_file_manager, sample_video_file):
    """파일 업로드 저장 테스트"""
    user_id = 1
    
    # 파일 저장
    file_id = await temp_file_manager.store_upload(sample_video_file, user_id)
    
    # 결과 검증
    assert file_id is not None
    assert len(file_id) > 10  # UUID + timestamp 형태
    
    # 파일 정보 조회
    file_info = await temp_file_manager.get_file_info(file_id)
    assert file_info is not None
    assert file_info.original_filename == "test_video.mp4"
    assert file_info.user_id == user_id
    assert file_info.file_type == "input"
    assert file_info.content_type == "video/mp4"
    
    # 실제 파일 존재 확인
    file_path = await temp_file_manager.get_file_path(file_id)
    assert file_path is not None
    assert os.path.exists(file_path)

@pytest.mark.asyncio
async def test_register_result_file(temp_file_manager):
    """결과 파일 등록 테스트"""
    user_id = 1
    
    # 임시 결과 파일 생성
    result_content = b"processed image result"
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
        f.write(result_content)
        result_file_path = f.name
    
    try:
        # 결과 파일 등록
        file_id = await temp_file_manager.register_result_file(
            result_file_path, user_id, expires_in_hours=72
        )
        
        # 검증
        file_info = await temp_file_manager.get_file_info(file_id)
        assert file_info is not None
        assert file_info.file_type == "output"
        assert file_info.user_id == user_id
        
        # 다운로드 URL 생성
        download_url = temp_file_manager.create_download_url(file_id)
        assert download_url == f"/api/files/download/{file_id}"
        
    finally:
        # 정리
        if os.path.exists(result_file_path):
            os.unlink(result_file_path)

@pytest.mark.asyncio
async def test_file_size_limit(temp_file_manager):
    """파일 크기 제한 테스트"""
    # 100MB 초과 파일 생성
    large_content = b"x" * (101 * 1024 * 1024)  # 101MB
    large_file = UploadFile(
        filename="large_file.mp4",
        file=BytesIO(large_content),
        size=len(large_content),
        content_type="video/mp4"
    )
    
    # 크기 제한 초과 시 예외 발생 확인
    with pytest.raises(ValueError, match="File size exceeds"):
        await temp_file_manager.store_upload(large_file, user_id=1)

@pytest.mark.asyncio
async def test_cleanup_expired_files(temp_file_manager):
    """만료된 파일 정리 테스트"""
    user_id = 1
    
    # 만료된 파일 생성 (과거 시간으로 설정)
    expired_content = b"expired file content"
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(expired_content)
        expired_file_path = f.name
    
    try:
        # DB에 만료된 파일 직접 추가
        SessionLocal = TestingSessionLocal
        async with SessionLocal() as db:
            expired_file = TempFile(
                id="expired_test_file",
                file_path=expired_file_path,
                original_filename="expired.txt",
                file_size=len(expired_content),
                content_type="text/plain",
                user_id=user_id,
                file_type="output",
                expires_at=datetime.utcnow() - timedelta(hours=1)  # 1시간 전 만료
            )
            db.add(expired_file)
            await db.commit()
        
        # 정리 실행
        cleanup_stats = await temp_file_manager.cleanup_expired_files()
        
        # 검증
        assert cleanup_stats["deleted_files"] >= 1
        assert not os.path.exists(expired_file_path)
        
        # DB에서도 삭제되었는지 확인
        file_info = await temp_file_manager.get_file_info("expired_test_file")
        assert file_info is None
        
    except Exception:
        # 정리
        if os.path.exists(expired_file_path):
            os.unlink(expired_file_path)
        raise

@pytest.mark.asyncio 
async def test_file_access_permissions(temp_file_manager, sample_image_file):
    """파일 접근 권한 테스트"""
    owner_id = 1
    other_user_id = 2
    
    # 파일 저장 (사용자 1)
    file_id = await temp_file_manager.store_upload(sample_image_file, owner_id)
    
    # 소유자는 접근 가능
    file_info = await temp_file_manager.get_file_info(file_id)
    assert file_info.user_id == owner_id
    
    # 다른 사용자 접근 시뮬레이션은 API 레벨에서 테스트

@pytest.mark.asyncio
async def test_filename_sanitization(temp_file_manager):
    """파일명 안전화 테스트"""
    # 특수문자가 포함된 파일명
    dangerous_content = b"test content"
    dangerous_file = UploadFile(
        filename="../../../etc/passwd",
        file=BytesIO(dangerous_content),
        size=len(dangerous_content),
        content_type="text/plain"
    )
    
    file_id = await temp_file_manager.store_upload(dangerous_file, user_id=1)
    file_path = await temp_file_manager.get_file_path(file_id)
    
    # 파일이 base_path 외부에 저장되지 않았는지 확인
    assert file_path.startswith(temp_file_manager.base_path)
    assert "../" not in file_path
    assert "etc/passwd" not in file_path

@pytest.mark.asyncio
async def test_content_type_detection(temp_file_manager):
    """Content-Type 감지 테스트"""
    test_cases = [
        ("test.jpg", "image/jpeg"),
        ("test.png", "image/png"), 
        ("test.mp4", "video/mp4"),
        ("test.unknown", "application/octet-stream")
    ]
    
    for filename, expected_type in test_cases:
        detected_type = temp_file_manager._get_content_type(f"/path/to/{filename}")
        assert detected_type == expected_type