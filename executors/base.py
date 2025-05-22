from abc import ABC, abstractmethod
from typing import Any
from module_models import ExecRequest, ExecResult

class Executor(ABC):
    @abstractmethod
    async def execute(self, request: ExecRequest) -> ExecResult:
        """주어진 입력으로 모듈을 실행하고 결과를 반환"""
        pass

    @abstractmethod
    async def validate(self, module_name: str) -> bool:
        """이 executor가 해당 모듈을 실행할 수 있는지 검증"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """executor가 사용한 리소스 정리"""
        pass

    @property
    @abstractmethod
    def executor_type(self) -> str:
        """executor의 타입(inline, venv, conda, docker) 반환"""
        pass 