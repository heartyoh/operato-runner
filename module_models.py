from pydantic import BaseModel, Field, ValidationError, StrictStr
from datetime import datetime
from typing import Optional, Dict, Any, List
class Module(BaseModel):
    name: StrictStr
    env: StrictStr  # 'inline', 'venv', 'conda', 'docker'
    code: Optional[str] = None
    path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    version: str = "0.1.0"
    tags: List[str] = []

    def __str__(self) -> str:
        return f"Module({self.name}, {self.env}, v{self.version})"

class ExecRequest(BaseModel):
    module: str  # module name
    input_json: Dict[str, Any]

class ExecResult(BaseModel):
    result_json: Dict[str, Any]
    exit_code: int
    stderr: Optional[str] = None
    stdout: Optional[str] = None
    duration: float  # seconds 