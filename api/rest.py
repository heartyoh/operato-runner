from fastapi import FastAPI, HTTPException, Depends, Body
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from models import Module, ExecRequest, ExecResult
from module_registry import ModuleRegistry
from executor_manager import ExecutorManager

app = FastAPI(title="Operato Runner", description="Python module execution platform")

# API 모델
class ModuleCreate(BaseModel):
    name: str
    env: str
    code: Optional[str] = None
    path: Optional[str] = None
    version: Optional[str] = "0.1.0"
    tags: List[str] = []

class ModuleResponse(BaseModel):
    name: str
    env: str
    version: str
    created_at: str
    tags: List[str]

class RunRequest(BaseModel):
    input: Dict[str, Any]

class RunResponse(BaseModel):
    result: Dict[str, Any]
    exit_code: int
    stderr: str
    stdout: str
    duration: float

# DI
module_registry = ModuleRegistry()
executor_manager = ExecutorManager(module_registry)

def get_module_registry():
    return module_registry

def get_executor_manager():
    return executor_manager

# 라우트
@app.get("/modules", response_model=List[ModuleResponse])
async def list_modules(module_registry: ModuleRegistry = Depends(get_module_registry)):
    modules = module_registry.list_modules()
    return [
        ModuleResponse(
            name=m.name,
            env=m.env,
            version=m.version,
            created_at=m.created_at.isoformat(),
            tags=m.tags
        ) for m in modules
    ]

@app.get("/modules/{name}", response_model=ModuleResponse)
async def get_module(name: str, module_registry: ModuleRegistry = Depends(get_module_registry)):
    module = module_registry.get_module(name)
    if not module:
        raise HTTPException(status_code=404, detail=f"Module '{name}' not found")
    return ModuleResponse(
        name=module.name,
        env=module.env,
        version=module.version,
        created_at=module.created_at.isoformat(),
        tags=module.tags
    )

@app.post("/modules", response_model=ModuleResponse, status_code=201)
async def create_module(
    module_data: ModuleCreate,
    module_registry: ModuleRegistry = Depends(get_module_registry)
):
    if not module_data.code and not module_data.path:
        raise HTTPException(status_code=400, detail="Either code or path must be provided")
    module = Module(
        name=module_data.name,
        env=module_data.env,
        code=module_data.code,
        path=module_data.path,
        version=module_data.version,
        tags=module_data.tags
    )
    module_registry.register_module(module)
    return ModuleResponse(
        name=module.name,
        env=module.env,
        version=module.version,
        created_at=module.created_at.isoformat(),
        tags=module.tags
    )

@app.delete("/modules/{name}", status_code=204)
async def delete_module(
    name: str,
    module_registry: ModuleRegistry = Depends(get_module_registry)
):
    if not module_registry.delete_module(name):
        raise HTTPException(status_code=404, detail=f"Module '{name}' not found")
    return None

@app.post("/run/{module}", response_model=RunResponse)
async def run_module(
    module: str,
    request: RunRequest = Body(...),
    executor_manager: ExecutorManager = Depends(get_executor_manager)
):
    exec_request = ExecRequest(
        module=module,
        input_json=request.input
    )
    result = await executor_manager.execute(exec_request)
    return RunResponse(
        result=result.result_json,
        exit_code=result.exit_code,
        stderr=result.stderr,
        stdout=result.stdout,
        duration=result.duration
    )

@app.get("/environments")
async def list_environments(
    executor_manager: ExecutorManager = Depends(get_executor_manager)
):
    return {"environments": executor_manager.get_available_environments()} 