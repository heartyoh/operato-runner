from typing import Dict, List, Any, Optional
from executors.base import Executor
from executors.inline import InlineExecutor
from executors.venv import VenvExecutor
from module_registry import ModuleRegistry
from models import ExecRequest, ExecResult

class ExecutorManager:
    def __init__(self, module_registry: ModuleRegistry):
        self.module_registry = module_registry
        self.executors: Dict[str, Executor] = {}

    async def execute(self, request: ExecRequest) -> ExecResult:
        module_name = request.module
        module = await self.module_registry.get_module(module_name)
        if not module:
            return ExecResult(
                result_json={},
                exit_code=1,
                stderr=f"Module '{module_name}' not found",
                stdout="",
                duration=0
            )
        executor = self.executors.get(module.env)
        if not executor:
            return ExecResult(
                result_json={},
                exit_code=1,
                stderr=f"No executor available for environment '{module.env}'",
                stdout="",
                duration=0
            )
        if not await executor.validate(module_name):
            return ExecResult(
                result_json={},
                exit_code=1,
                stderr=f"Module '{module_name}' cannot be executed in environment '{module.env}'",
                stdout="",
                duration=0
            )
        return await executor.execute(request)

    def register_executor(self, env: str, executor: Executor) -> None:
        self.executors[env] = executor

    def get_available_environments(self) -> List[str]:
        return list(self.executors.keys())

    async def cleanup(self) -> None:
        for executor in self.executors.values():
            await executor.cleanup() 