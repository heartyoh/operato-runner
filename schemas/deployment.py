from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DeploymentBase(BaseModel):
    module_id: int
    version_id: int
    status: Optional[str] = 'pending'

class DeploymentCreate(DeploymentBase):
    pass

class DeploymentRead(DeploymentBase):
    id: int
    deployed_at: datetime
    class Config:
        orm_mode = True 