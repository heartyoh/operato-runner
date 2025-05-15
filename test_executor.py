import pytest
import asyncio
from executors.base import Executor
from models import ExecRequest, ExecResult

# 1. 추상 클래스 직접 인스턴스화 불가 테스트
def test_executor_cannot_instantiate():
    with pytest.raises(TypeError):
        Executor()

# 2. 모든 메서드를 구현한 MockExecutor 정의
def make_mock_executor():
    class MockExecutor(Executor):
        async def execute(self, request: ExecRequest) -> ExecResult:
            return ExecResult(result_json={"ok": True}, exit_code=0, duration=0.1)
        async def validate(self, module_name: str) -> bool:
            return True
        async def cleanup(self) -> None:
            pass
        @property
        def executor_type(self) -> str:
            return "mock"
    return MockExecutor

# 3. 구현체는 정상적으로 인스턴스화 및 메서드 동작
def test_mock_executor_implements_interface():
    MockExecutor = make_mock_executor()
    exec = MockExecutor()
    req = ExecRequest(module="mod", input_json={})
    # execute, validate, cleanup, executor_type 동작 확인
    result = asyncio.run(exec.execute(req))
    assert isinstance(result, ExecResult)
    assert result.result_json["ok"] is True
    assert exec.executor_type == "mock"
    assert asyncio.run(exec.validate("mod")) is True
    assert asyncio.run(exec.cleanup()) is None

# 4. 메서드 미구현시 TypeError 발생 확인
def test_incomplete_executor_fails():
    # execute 미구현
    class IncompleteExecutor(Executor):
        async def validate(self, module_name: str) -> bool:
            return True
        async def cleanup(self) -> None:
            pass
        @property
        def executor_type(self) -> str:
            return "incomplete"
    with pytest.raises(TypeError):
        IncompleteExecutor() 