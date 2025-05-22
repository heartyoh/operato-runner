from models.audit_log import AuditLog
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

async def log_audit_event(db: AsyncSession, action: str, detail: Optional[str] = None, user_id: Optional[int] = None):
    log = AuditLog(user_id=user_id, action=action, detail=detail)
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log 