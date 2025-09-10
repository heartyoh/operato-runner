from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TempFileCreate(BaseModel):
    original_filename: str
    file_size: int
    content_type: Optional[str] = None
    file_type: str = 'input'  # 'input' or 'output'
    expires_in_hours: int = 24

class TempFileRead(BaseModel):
    id: str
    original_filename: str
    file_size: int
    content_type: Optional[str]
    file_type: str
    created_at: datetime
    expires_at: datetime
    size_human: str
    is_expired: bool
    
    class Config:
        from_attributes = True

class TempFileResponse(BaseModel):
    file_id: str
    download_url: str
    original_filename: str
    file_size: int
    expires_at: datetime