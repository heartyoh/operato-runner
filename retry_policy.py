import asyncio
from typing import Dict, Any, Optional, Callable, TypeVar, Generic
from models import ExecRequest, ExecResult

T = TypeVar('T')

class RetryPolicy(Generic[T]):
    def __init__(self, max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.delay = delay
        self.backoff_factor = backoff_factor
    
    async def execute_with_retry(self, func: Callable[..., T], *args, **kwargs) -> T:
        last_exception = None
        current_delay = self.delay
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    await asyncio.sleep(current_delay)
                    current_delay *= self.backoff_factor
                else:
                    raise

class RetryableExecutorManager:
    def __init__(self, executor_manager, retry_policy: Optional[RetryPolicy] = None):
        self.executor_manager = executor_manager
        self.retry_policy = retry_policy or RetryPolicy()
    
    async def execute(self, request: ExecRequest) -> ExecResult:
        try:
            return await self.retry_policy.execute_with_retry(
                self.executor_manager.execute,
                request
            )
        except Exception as e:
            return ExecResult(
                result_json={},
                exit_code=1,
                stderr=f"Failed after {self.retry_policy.max_retries} retries: {str(e)}",
                stdout="",
                duration=0
            )
    
    def register_executor(self, env: str, executor) -> None:
        self.executor_manager.register_executor(env, executor)
    
    def get_available_environments(self):
        return self.executor_manager.get_available_environments()
    
    async def cleanup(self) -> None:
        await self.executor_manager.cleanup() 